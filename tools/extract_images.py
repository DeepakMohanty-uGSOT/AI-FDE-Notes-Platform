"""Pull the original screenshots out of the course's Google Docs (.docx exports).

How to get the source files: in Google Drive, right-click the "FDE -Notes" folder → Download.
Drive zips the folder and converts every Google Doc to .docx. Drop the zip(s) or the extracted
folder into  _source/  in the project root, then run:

    python tools/extract_images.py

For each doc it writes
    notes/<module>/<note>/img/01.png, 02.png ...         (web-sized copies, in document order)
    tools/images/<module>__<note>.json                   (manifest: each image + the text before/after it,
                                                          used to place the image in the right spot)
"""
import difflib, io, json, os, re, sys, zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_source')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
V = '{urn:schemas-microsoft-com:vml}'
MAX_W = 1400

# Google Doc title (as in Drive) → (module, note). Code docs are mapped too; their images go to the same note.
TITLES = {
    'FDE Role': ('fde', 'fde-role'), 'FDE_Responsibilities': ('fde', 'fde-responsibilities'), 'The FDE Mindset': ('fde', 'fde-mindset'),
    'Introduction to UNIX & Linux': ('linux', 'intro-unix-linux'), 'Linux Architecture': ('linux', 'linux-architecture'),
    'Environment Setup': ('linux', 'environment-setup'), 'Linux Terminal and Shell': ('linux', 'terminal-and-shell'),
    'The Linux File System Structure': ('linux', 'file-system-structure'), 'Files & Directories in Linux': ('linux', 'files-and-directories'),
    'Reading Files in Linux': ('linux', 'reading-files'), 'Searching Files & Content': ('linux', 'searching-files'),
    'Essential Text Filters in Linux': ('linux', 'text-filters'), 'Pipes & Redirection in Linux': ('linux', 'pipes-and-redirection'),
    'Command Chaining': ('linux', 'command-chaining'),
    'Networking Fundamentals – I: Physical Connectivity & Network Types': ('networking', 'physical-connectivity'),
    'Networking Fundamentals – II: Device Identification & Core Protocols': ('networking', 'device-identification-protocols'),
    'Networking Fundamentals – III: OSI Model & Data Communication': ('networking', 'osi-model'),
    'IP Address Fundamentals': ('networking', 'ip-address-fundamentals'), 'IP Addressing – Subnetting & CIDR': ('networking', 'subnetting-cidr'),
    'Version Control System': ('git', 'version-control'), 'Git Fundamentals': ('git-basics', 'git-fundamentals'),
    'Untitled document': ('git', 'git-workflows+github'), 'Git deep dive': ('git', 'git-workflows+github'),
    'HTML Syntax and Structure': ('web', 'html-syntax-structure'), 'Common HTML Elements': ('web', 'common-html-elements'),
    'HTML List & image': ('web', 'html-lists-images'), 'Forms and inputs': ('web', 'forms-and-inputs'),
    'Python Basics - Part 1': ('python-fundamentals', 'python-basics-1'), 'Python Basics — Part 2': ('python-fundamentals', 'python-basics-2'),
    'Python Control Flow': ('python-fundamentals', 'control-flow'), 'Python Data Structures': ('python-fundamentals', 'data-structures'),
    'Python Functions': ('python-fundamentals', 'functions'), 'Python Modules & Packages': ('python-fundamentals', 'modules-packages'),
    'Python Working with Data': ('python-fundamentals', 'working-with-data'), 'Python Error Handling': ('python-fundamentals', 'error-handling'),
    'Intro_To_OOPs_part 1': ('python-fundamentals', 'oops-1'), 'Intro_To_OOPs_part 2_': ('python-fundamentals', 'oops-2'),
    'Inheritance': ('python-fundamentals', 'inheritance'), 'Method_Overriding': ('python-fundamentals', 'method-overriding'),
    'Python_Project_Development_Notes': ('python-advanced', 'project-development'), 'API_Basics': ('python-advanced', 'api-basics'),
    'FastAPI Fundamentals, Setup & Project Structure': ('python-advanced', 'fastapi-fundamentals'),
    'Pydantic — Validating Data in Python': ('python-advanced', 'pydantic'),
    'Path Operations and HTTP Methods': ('python-advanced', 'path-operations-http-methods'),
    'Path & Query Parameters': ('python-advanced', 'path-query-parameters'),
    'LLM Engineering': ('llm-engineering', 'llm-engineering'), 'Prompt_and_Context_Engineering': ('prompt-context', 'prompt-context-engineering'),
    'LangChain_Fundamentals': ('langchain', 'langchain-fundamentals'), 'Model_selection': ('model-selection', 'model-selection'),
}


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())


NORM = {norm(k): v for k, v in TITLES.items()}


def match(name):
    base = norm(re.sub(r'\.docx$', '', name, flags=re.I))
    base = re.sub(r'\d$', '', base) if base not in NORM else base   # "Doc (1).docx" duplicates
    if base in NORM:
        return NORM[base]
    best = difflib.get_close_matches(base, list(NORM), n=1, cutoff=0.82)
    return NORM[best[0]] if best else None


def run_events(p, rid):
    """Text and images of one paragraph, in reading order."""
    ev, buf = [], []
    for t in p.iter():
        if t.tag == W + 't' and t.text:
            buf.append(t.text)
        elif t.tag == W + 'tab':
            buf.append('    ')
        elif t.tag in (W + 'br', W + 'cr'):
            buf.append('\n')
        elif t.tag in (A + 'blip', V + 'imagedata'):
            r_ = t.get(R + 'embed') or t.get(R + 'id')
            if r_ in rid:
                if buf:
                    ev.append(('text', ''.join(buf))); buf = []
                ev.append(('img', 'word/' + rid[r_].lstrip('/').replace('word/', '')))
    if buf:
        ev.append(('text', ''.join(buf)))
    return ev


def para_prefix(p):
    ppr = p.find(W + 'pPr')
    if ppr is None:
        return ''
    st = ppr.find(W + 'pStyle')
    sv = (st.get(W + 'val') if st is not None else '') or ''
    m = re.match(r'(?i)heading\s*(\d)', sv)
    if m:
        return '#' * int(m.group(1)) + ' '
    if sv.lower() == 'title':
        return '# '
    num = ppr.find(W + 'numPr')
    if num is not None:
        lvl = num.find(W + 'ilvl')
        return '  ' * int(lvl.get(W + 'val') if lvl is not None else 0) + '- '
    return ''


def walk(docx_bytes):
    """Return (zip, events). Events: ('text', str) and ('img', member) in document order; tables as | rows |."""
    z = zipfile.ZipFile(io.BytesIO(docx_bytes))
    rels = ET.fromstring(z.read('word/_rels/document.xml.rels'))
    rid = {r.get('Id'): r.get('Target') for r in rels}
    body = ET.fromstring(z.read('word/document.xml')).find(W + 'body')
    events = []

    def block(el):
        if el.tag == W + 'p':
            pre, first = para_prefix(el), True
            for k, v in run_events(el, rid):
                if k == 'text':
                    v = v.strip('\n')
                    if v.strip():
                        events.append(('text', (pre if first else '') + v)); first = False
                else:
                    events.append((k, v))
        elif el.tag == W + 'tbl':
            events.append(('text', '[TABLE]'))
            for tr in el.iter(W + 'tr'):
                cells, imgs = [], []
                for tc in tr.findall(W + 'tc'):
                    parts = []
                    for p in tc.iter(W + 'p'):
                        for k, v in run_events(p, rid):
                            if k == 'text' and v.strip():
                                parts.append(v.strip())
                            elif k == 'img':
                                imgs.append(v); parts.append('(image)')
                    cells.append(' / '.join(parts))
                events.append(('text', '| ' + ' | '.join(cells) + ' |'))
                for v in imgs:
                    events.append(('img', v))
            events.append(('text', '[/TABLE]'))
        elif el.tag == W + 'sdt':
            c = el.find(W + 'sdtContent')
            for ch in (list(c) if c is not None else []):
                block(ch)

    for el in body:
        block(el)
    return z, events


def save_image(data, path_noext):
    """Web-sized WebP copy (text stays crisp at q90; ~5-10x smaller than PNG)."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data))
        im.load()
        if im.width > MAX_W:
            im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
        if im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGBA' if 'A' in im.mode or im.mode == 'P' else 'RGB')
        out = path_noext + '.webp'
        im.save(out, 'WEBP', quality=90, method=6)
        return out, im.width, im.height
    except Exception:
        return None, 0, 0


def collect_docx():
    found = []
    for dp, _, fs in os.walk(SRC):
        for f in fs:
            p = os.path.join(dp, f)
            if f.lower().endswith('.docx'):
                found.append((f, open(p, 'rb').read()))
            elif f.lower().endswith('.zip'):
                with zipfile.ZipFile(p) as z:
                    for n in z.namelist():
                        if n.lower().endswith('.docx'):
                            found.append((os.path.basename(n), z.read(n)))
    return found


def main():
    import hashlib
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    if not os.path.isdir(SRC):
        print('Put the Drive download (zip or .docx files) in %s first.' % SRC); return 1
    os.makedirs(os.path.join(ROOT, 'tools', 'images'), exist_ok=True)
    files = collect_docx()
    if not files:
        print('No .docx files found under _source/'); return 1
    per_note, unmatched = {}, []
    for name, data in files:
        m = match(name)
        if not m:
            unmatched.append(name); continue
        per_note.setdefault(m, []).append((name, data))
    total = 0
    for (mod, note), docs in sorted(per_note.items()):
        # duplicates like "Doc(1).docx": keep the biggest (the real doc, not an empty stub)
        name, data = max(docs, key=lambda d: len(d[1]))
        targets = note.split('+')
        outdir = os.path.join(ROOT, 'notes', mod, targets[0], 'img')
        os.makedirs(outdir, exist_ok=True)
        for old in os.listdir(outdir):
            if re.match(r'\d{2,3}\.(png|jpg|webp)$', old):
                os.remove(os.path.join(outdir, old))
        z, events = walk(data)
        manifest, lines, seen, n = [], [], {}, 0
        for i, (kind, val) in enumerate(events):
            if kind == 'text':
                lines.append(val); continue
            try:
                raw = z.read(val)
            except KeyError:
                continue
            hsh = hashlib.md5(raw).hexdigest()
            if hsh in seen:
                lines.append('[[IMG %02d again]]' % seen[hsh]['n'])
                continue
            n += 1
            out, w, h = save_image(raw, os.path.join(outdir, '%02d' % n))
            before = [v for k, v in events[max(0, i - 6):i] if k == 'text'][-3:]
            after = [v for k, v in events[i + 1:i + 8] if k == 'text'][:2]
            rec = {'n': n, 'file': os.path.basename(out) if out else None, 'w': w, 'h': h,
                   'before': before, 'after': after,
                   'skipped': None if out else 'unsupported format ' + os.path.splitext(val)[1]}
            seen[hsh] = rec; manifest.append(rec)
            lines.append('[[IMG %02d | %s | %dx%d]]' % (n, rec['file'] or 'SKIPPED', w, h))
        base = '%s__%s' % (mod, note.replace('+', '_'))
        with open(os.path.join(ROOT, 'tools', 'images', base + '.json'), 'w', encoding='utf-8') as f:
            json.dump({'module': mod, 'notes': targets, 'source': name,
                       'imgdir': os.path.relpath(outdir, ROOT).replace('\\', '/'), 'images': manifest}, f, ensure_ascii=False, indent=1)
        with open(os.path.join(ROOT, 'tools', 'images', base + '.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        total += len(manifest)
        print('%-20s %-34s %3d images %6d words  <- %s' % (mod, note, len(manifest), sum(len(l.split()) for l in lines), name))
    print('\nTotal unique images: %d' % total)
    if unmatched:
        print('\nUnmatched files (not in the course map):')
        for u in unmatched:
            print('  - ' + u)
    missing = sorted(set(TITLES.values()) - set(per_note))
    if missing:
        print('\nNo .docx found for:')
        for m in missing:
            print('  - %s/%s' % m)
    return 0


if __name__ == '__main__':
    sys.exit(main())
