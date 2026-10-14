"""AIFDE Notes · build script

Reads tools/modules.json plus every notes/<module>/<note>/index.html and writes:
  notes.json            full site data (handy for humans / other tools)
  assets/data.js        same data as window.AIFDE_DATA (lets the site run from file:// too)
  assets/search.js      section-level full-text index (window.AIFDE_SEARCH)
  assets/glossary.js    every <dl class="terms"> entry (window.AIFDE_GLOSSARY)
  notes/<module>/index.html   module landing pages
It also validates each note and prints warnings.

Usage:  python tools/build.py
"""
import json, os, re, sys, datetime
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    def cls(self):
        return (self.attrs.get('class') or '').split()

    def text(self):
        out = []
        for k in self.kids:
            out.append(k if isinstance(k, str) else (' ' if k.tag in ('br',) else '') + k.text() + (' ' if k.tag in BLOCK else ''))
        return ''.join(out)

    def find_all(self, pred):
        res = []
        for k in self.kids:
            if isinstance(k, Node):
                if pred(k):
                    res.append(k)
                res.extend(k.find_all(pred))
        return res

    def find(self, pred):
        r = self.find_all(pred)
        return r[0] if r else None


BLOCK = {'p', 'div', 'li', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'dt', 'dd', 'pre', 'tr', 'figcaption', 'section', 'span', 'text'}


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('#root', {})
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.kids.append(data)


def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()


def parse_note(path, mod, meta, warn):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    t = Tree()
    t.feed(html)
    doc = t.root
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    nid = mod['slug'] + '/' + meta['slug']

    h1 = doc.find(lambda n: n.tag == 'h1')
    title = clean(h1.text()) if h1 else meta['title']
    desc = doc.find(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'description')
    summary = clean(desc.attrs.get('content')) if desc else ''
    if not summary:
        warn(rel, 'missing <meta name="description">')
    date_m = doc.find(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'date')
    date = date_m.attrs.get('content') if date_m else datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
    kw = doc.find(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'keywords')

    body = doc.find(lambda n: n.tag == 'body')
    if not body or body.attrs.get('data-note') != nid:
        warn(rel, 'body data-note should be "%s"' % nid)
    if not body or body.attrs.get('data-root') != '../../../':
        warn(rel, 'body data-root should be "../../../"')
    if 'assets/site.js' not in html:
        warn(rel, 'site.js script tag missing')

    sections, index, terms = [], [], []
    for s in doc.find_all(lambda n: n.tag == 'section' and 'ch' in n.cls()):
        h2 = s.find(lambda n: n.tag == 'h2')
        if not h2:
            warn(rel, 'section without <h2>')
            continue
        sid = s.attrs.get('id')
        if not sid:
            warn(rel, 'section "%s" has no id' % clean(h2.text()))
            sid = re.sub(r'[^a-z0-9]+', '-', clean(h2.text()).lower()).strip('-')
        stitle = clean(h2.text())
        sections.append({'id': sid, 'title': stitle})
        index.append({'n': nid, 's': sid, 'h': stitle, 't': clean(s.text())[:6000]})
        for dl in s.find_all(lambda n: n.tag == 'dl' and 'terms' in n.cls()):
            dts = dl.find_all(lambda n: n.tag == 'dt')
            for dt in dts:
                dd = None
                par = dt.parent
                for k in par.kids:
                    if isinstance(k, Node) and k.tag == 'dd':
                        dd = k
                        break
                if dd is not None:
                    terms.append({'term': clean(dt.text()), 'def': clean(dd.text()), 'n': nid, 's': sid})

    qs = doc.find_all(lambda n: n.tag == 'div' and 'q' in n.cls())
    for i, q in enumerate(qs):
        ans = q.attrs.get('data-answer', '')
        lis = q.find_all(lambda n: n.tag == 'li')
        if not ans.isdigit() or not (1 <= int(ans) <= len(lis)):
            warn(rel, 'quiz question %d: data-answer "%s" invalid for %d options' % (i + 1, ans, len(lis)))
        if not q.find(lambda n: 'why' in n.cls()):
            warn(rel, 'quiz question %d has no .why explanation' % (i + 1))
    if len(sections) < 4:
        warn(rel, 'only %d sections' % len(sections))
    if not qs:
        warn(rel, 'no quiz questions')
    if not terms:
        warn(rel, 'no key terms (<dl class="terms">)')

    main = doc.find(lambda n: n.tag == 'main')
    words = len(clean(main.text() if main else '').split())
    skip = {'key terms', 'self-check', 'all of it, in one sentence', 'summary'}
    topics = [x.strip() for x in kw.attrs.get('content', '').split(',')] if kw else \
        [x['title'] for x in sections if x['title'].lower() not in skip][:8]
    return {
        'id': nid, 'module': mod['slug'], 'slug': meta['slug'], 'order': meta['order'],
        'title': title, 'summary': summary, 'topics': [x for x in topics if x],
        'readMinutes': max(3, round(words / 190)), 'words': words,
        'sections': sections, 'quiz': len(qs), 'terms': len(terms), 'date': date,
        'drive': meta.get('drive', ''),
    }, index, terms


MODULE_PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title} | AIFDE Notes</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Patrick+Hand&family=Nunito:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="../../assets/style.css?v=0">
<script>try{{var t=localStorage.getItem('aifde:theme'),f=localStorage.getItem('aifde:font');if(t)document.documentElement.setAttribute('data-theme',JSON.parse(t));if(f&&JSON.parse(f)==='clean')document.documentElement.setAttribute('data-font','clean')}}catch(e){{}}</script>
</head>
<body data-root="../../" data-page="module" data-module="{slug}">
<!-- generated by tools/build.py — edit tools/modules.json, not this file -->
<main class="wrap ruled">
  <section aria-labelledby="m-title">
    <p class="eyebrow" id="m-eyebrow">Module</p>
    <div class="actions" style="gap:16px"><span class="pn" id="m-icon" aria-hidden="true" style="width:64px;height:64px;font-size:26px;border-radius:50%">{icon}</span><h1 id="m-title">{title}</h1></div>
    <svg class="squiggle" viewBox="0 0 210 15" aria-hidden="true"><path d="M3 9 C 24 2, 44 14, 68 8 S 112 2, 136 9 S 178 14, 207 7"/></svg>
    <p class="lede" id="m-summary">{desc}</p>
    <p class="meta" id="m-meta"></p>
    <div class="progress" id="m-progress" aria-live="polite"></div>
    <div class="actions"><a class="btn primary" id="m-start" href="#m-notes">Start reading →</a><a class="btn" href="../index.html#{slug}">Search this module</a></div>
  </section>
  <section aria-labelledby="m-notes-title">
    <p class="eyebrow">Read them in order</p>
    <h2 id="m-notes-title">Notes in this module</h2>
    <ul class="note-list" id="m-notes"><li class="empty">Loading notes…</li></ul>
    <nav class="pager" id="m-pager" aria-label="Other modules"></nav>
  </section>
</main>
<script src="../../assets/site.js?v=0"></script>
</body>
</html>
'''


def main():
    with open(os.path.join(ROOT, 'tools', 'modules.json'), encoding='utf-8') as f:
        cfg = json.load(f)
    warnings = []

    def warn(where, msg):
        warnings.append('%s: %s' % (where, msg))

    notes, index, glossary, modules = [], [], [], []
    num = 0
    for mod in sorted(cfg['modules'], key=lambda m: m['order']):
        mod.setdefault('kind', 'module')
        if mod['kind'] == 'module':
            num += 1
            mod.setdefault('number', str(num))
        found = []
        for i, meta in enumerate(mod.get('notes', []), 1):
            meta = dict(meta, order=i)
            p = os.path.join(ROOT, 'notes', mod['slug'], meta['slug'], 'index.html')
            if not os.path.exists(p):
                warn('notes/%s/%s' % (mod['slug'], meta['slug']), 'page not written yet')
                continue
            n, ix, gl = parse_note(p, mod, meta, warn)
            notes.append(n); index.extend(ix); glossary.extend(gl); found.append(n['slug'])
        status = 'soon' if (mod.get('status') == 'soon' or not found) else 'published'
        m = {k: v for k, v in mod.items() if k not in ('notes', 'folder', 'topics') or k == 'topics'}
        m['status'] = status
        m['notes'] = found
        modules.append(m)
        if status == 'published' and mod['kind'] == 'module':
            d = os.path.join(ROOT, 'notes', mod['slug'])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
                f.write(MODULE_PAGE.format(title=mod['title'], desc=mod['summary'].replace('"', '&quot;'), slug=mod['slug'], icon=mod['number']))

    data = {'site': cfg['site'], 'stages': cfg['stages'], 'modules': modules, 'notes': notes,
            'built': datetime.datetime.now().isoformat(timespec='seconds')}
    with open(os.path.join(ROOT, 'notes.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    def js(name, var, obj):
        with open(os.path.join(ROOT, 'assets', name), 'w', encoding='utf-8', newline='\n') as f:
            f.write('/* generated by tools/build.py */\nwindow.%s=' % var)
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
            f.write(';\n')

    js('data.js', 'AIFDE_DATA', data)
    js('search.js', 'AIFDE_SEARCH', index)
    js('glossary.js', 'AIFDE_GLOSSARY', glossary)

    # cache-busting: stamp every page's style.css / site.js link with this build's version
    ver = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    for dp, _, fs in os.walk(ROOT):
        if any(x in dp for x in ('_source', '.git', 'tools')):
            continue
        for fn in fs:
            if fn.endswith('.html'):
                fp = os.path.join(dp, fn)
                with open(fp, encoding='utf-8') as f:
                    h = f.read()
                h2 = re.sub(r'(assets/(?:style\.css|site\.js))(\?v=\w+)?"', lambda m: m.group(1) + '?v=' + ver + '"', h)
                if h2 != h:
                    with open(fp, 'w', encoding='utf-8', newline='
') as f:
                        f.write(h2)

    pub = [m for m in modules if m['status'] == 'published' and m['kind'] == 'module']
    print('Built: %d modules published, %d notes, %d sections, %d glossary terms, %d quiz questions, ~%d min reading'
          % (len(pub), len(notes), len(index), len(glossary), sum(n['quiz'] for n in notes), sum(n['readMinutes'] for n in notes)))
    if warnings:
        print('\n%d warning(s):' % len(warnings))
        for w in warnings:
            print('  - ' + w)
    return 0


if __name__ == '__main__':
    sys.exit(main())
