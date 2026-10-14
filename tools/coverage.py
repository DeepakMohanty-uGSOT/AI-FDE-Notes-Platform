"""Coverage check: is every image and every piece of source content on the website?

Needs the extracted dumps from tools/extract_images.py (tools/images/<module>__<note>.txt/.json).

  python tools/coverage.py                     summary for every note
  python tools/coverage.py linux/text-filters  detailed report for one note (or several)

An image counts as placed when the page references img/NN.webp, or carries an explanatory
comment  <!-- img NN: <reason> -->  (only allowed for purely explanatory drawings that an SVG
on the page fully replaces). For git-workflows + github both pages are checked together.

A source line counts as covered when most of its meaningful words appear on the page.
Flagged lines are candidates to review, not proof something is missing (the pages paraphrase).
"""
import glob, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set('''a an the and or but if then else of to in on at by for with from as is are was were be been being this that these those it its
it's we you your our they them their he she his her i me my can could will would should shall may might must do does did done not no yes
so such than too very just also only into onto over under about after before again further once here there when where why how all any both
each few more most other some own same what which who whom whose let lets let's now use used using get got like one two three'''.split())


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def words(s):
    return [w for w in re.findall(r"[a-z0-9_]+", s.lower()) if len(w) > 2 and w not in STOP]


def check(base, verbose):
    meta = json.load(open(os.path.join(ROOT, 'tools', 'images', base + '.json'), encoding='utf-8'))
    src = open(os.path.join(ROOT, 'tools', 'images', base + '.txt'), encoding='utf-8').read().splitlines()
    html = ''
    for n in meta['notes']:
        p = os.path.join(ROOT, 'notes', meta['module'], n, 'index.html')
        if os.path.exists(p):
            html += open(p, encoding='utf-8').read()
    t = Text(); t.feed(html)
    page_words = set(words(' '.join(t.out)))
    # images
    missing_img = []
    for im in meta['images']:
        nn = '%02d' % im['n']
        if not (re.search(r'img/%s\.webp' % nn, html) or re.search(r'<!--\s*img\s+%s\s*:' % nn, html)):
            missing_img.append(nn)
    # text
    gaps = []
    for i, line in enumerate(src, 1):
        if line.startswith('[[IMG') or line.strip() in ('[TABLE]', '[/TABLE]'):
            continue
        ws = set(words(line))
        if len(ws) < 3:
            continue
        cov = len(ws & page_words) / len(ws)
        if cov < 0.6:
            gaps.append((i, cov, line.strip()))
    total_lines = sum(1 for l in src if len(set(words(l))) >= 3 and not l.startswith('[[IMG'))
    print('%-46s images %3d/%-3d  text %5.1f%% covered  (%d lines to review)' % (
        base, len(meta['images']) - len(missing_img), len(meta['images']),
        100 * (1 - len(gaps) / max(1, total_lines)), len(gaps)))
    if verbose:
        if missing_img:
            print('  images not placed:', ' '.join(missing_img))
        for i, cov, line in gaps:
            print('  L%-5d %3d%%  %s' % (i, cov * 100, line[:150]))
    return len(missing_img), len(gaps)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    args = sys.argv[1:]
    bases = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'tools', 'images', '*.json')))
    if args:
        want = [a.replace('/', '__') for a in args]
        bases = [b for b in bases if any(b.startswith(w) or w in b for w in want)]
    mi = mg = 0
    for b in bases:
        a, g = check(b, verbose=bool(args))
        mi += a; mg += g
    print('\nTOTAL: %d images not placed, %d source lines to review' % (mi, mg))


if __name__ == '__main__':
    main()
