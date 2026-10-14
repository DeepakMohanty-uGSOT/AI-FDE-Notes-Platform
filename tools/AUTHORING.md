# Writing an AIFDE note page

Every note is one self-contained page at `notes/<module>/<note>/index.html`. The shared engine (`assets/site.js`) adds the top bar, the sidebar contents, section numbers, "Got it" boxes, reading progress, the quiz engine, copy buttons, syntax highlighting, prev/next links and the footer. **You only write the content.**

**The gold-standard example is `notes/linux/command-chaining/index.html`.** Read it fully before writing, and copy its skeleton exactly.

## 1. Skeleton (copy exactly; change only the marked parts)

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>NOTE TITLE · MODULE TITLE | AIFDE Notes</title>
<meta name="description" content="ONE OR TWO SENTENCES: what this note covers. Shown on cards and in search.">
<meta name="keywords" content="5–8 short topic chips, comma separated">
<meta name="date" content="YYYY-MM-DD">   <!-- the Google Doc's createdTime date -->
...fonts + stylesheet + theme script lines copied from the example, unchanged...
</head>
<body data-root="../../../" data-page="note" data-note="MODULE-SLUG/NOTE-SLUG">
<main class="page" id="top">
<header class="top">
  <h1>Note Title</h1>
  <p class="byline">One friendly sentence: what you will be able to do after this note.</p>
</header>

<section class="ch" id="short-kebab-id">
  <h2>Section title</h2>
  ...content...
</section>
...more sections...
<section class="ch" id="terms"><h2>Key terms</h2> ... </section>
<section class="ch" id="quiz"><h2>Self-check</h2> ... </section>
<section class="ch" id="summary"><h2>All of it, in one sentence</h2> ... </section>
</main>
<script src="../../../assets/site.js"></script>
</body>
</html>
```

Rules:
- Every `section.ch` needs a unique `id` and exactly one `<h2>`. Do **not** number headings and do **not** add "Got it" boxes; the engine does both.
- Use `<h3>` for sub-headings inside a section.
- Never add `<style>` or `<script>` blocks, and never load other libraries. Use only the components below.

## 2. Content rules (the most important part)

1. **Keep everything.** Read the whole Google Doc. Every concept, definition, command, code sample, example, table, comparison, warning and practice task in the source must appear on the page. Restructure and improve it, but do not drop material. If the source has an accompanying code doc, fold its examples in where they belong.
2. **Structure it better.** Group the material into clear sections, usually 6 to 14 content sections plus Key terms, Self-check and Summary. Follow the source's teaching order unless a different order is clearly more logical. Merge repetition, fix typos and grammar, and turn walls of text into the components below.
3. **Rebuild the visuals.** Screenshots and images don't come through the Drive export. Wherever the source relies on one (a terminal output, a diagram, a UI), recreate it: an SVG diagram, a `.flow`, a table, or a `pre.out` showing the expected output. Text "arrow diagrams" (`↓`, `→`) in the source must become `.flow` chips, `ol.path` steps or SVG diagrams.
4. **Teach like the example:**
   - Open the main concepts with a `.story` everyday analogy. Indian everyday life works well: chai, trains, Swiggy, the post office, the kirana shop.
   - Highlight the one key sentence with `<mark>`.
   - Give each note **at least 3 sketched SVG diagrams**, more for conceptual notes.
   - Add a `.sticky.fde` "In the field (FDE)" note wherever a topic connects to real customer and production work.
   - Use `.sticky.warn` for common mistakes and gotchas.
5. **Be technically correct.** If the source contains a factual error, fix it on the page and list the fix in your final report. Only add knowledge that is standard and certain.
6. **Key terms:** 6–15 `<dl class="terms">` entries. They feed the site-wide glossary and flashcards, so make each definition stand alone in one or two sentences.
7. **Self-check:** 6–10 multiple-choice questions, each with 4 options, `data-answer` set to the 1-based correct option, and a `.why` line explaining it. Vary the position of the right answer. Test understanding, not trivia.
8. **Summary:** a `p.final` one-to-three-sentence recap with `<b>` on the key words, then a line pointing to the next note in the module, then `<p class="sign">— Vishwa Mohan</p>`.
9. Write warm, simple English for beginners. Address the reader as "you".

## 3. Components (all styled already)

| Need | Markup |
|---|---|
| Analogy | `<div class="story"><b class="lbl">Title</b>Text… <mark>key line</mark></div>` |
| Highlight | `<mark>` (yellow), `<mark class="g">` green, `.p` pink, `.b` blue, `.v` violet |
| Sticky note | `<div class="sticky">` + `<strong>Title</strong> text`. Variants: `.tip` green, `.warn` orange, `.info` blue, `.fde` violet; add `.l` to tilt left |
| Concept cards | `<div class="grid">` (or `.two`) holding `<div class="card t1 tilt-a"><h4>Title</h4><p>…</p></div>`. Colours t1 blue, t2 green, t3 orange, t4 pink, t5 violet, t6 grey, t7 yellow, t8 teal; tilts `tilt-a` / `tilt-b` |
| Flow chips | `<div class="flow"><span>A</span><span class="ok">B</span><span class="bad">C</span></div>`. Add class `v` for vertical. Chip classes: `ok`, `bad`, `hl`, `op` (monospace), `skip` |
| Steps | `<ol class="path"><li><span class="dot">1</span><div><b>Step title</b>Text <span class="tag">→ hint</span></div></li></ol>` |
| Big numbers | `<div class="notes"><div class="note"><b>443</b>HTTPS</div>…</div>` |
| Table | `<div class="tbl"><table><tr><th>…</th></tr><tr><td>…</td></tr></table></div>` |
| Split string | `<div class="anatomy"><span class="a1">https://</span><span class="a2">host</span>…</div>` + `<div class="legend"><div><span class="sw a1"></span><p>…</p></div></div>` (a1–a7) |
| Code | `<pre><code class="language-python">…</code></pre>` (also `language-bash`, `language-html`, `language-json`, `language-sql`, `language-javascript`, `language-css`, `language-plaintext`). **Escape `<`, `>`, `&`.** |
| Code with caption | `<div class="codebox"><span class="cap">app/main.py</span><pre><code class="language-python">…</code></pre></div>` |
| Expected output | `<pre class="out"><code>…</code></pre>` |
| Labelled command | `<div class="cmd"><p class="what">Try it</p><pre>…</pre></div>` |
| Keyboard | `<kbd>Ctrl</kbd> + <kbd>C</kbd>` |
| Key terms | `<dl class="terms"><div><dt>Term</dt><dd>Definition.</dd></div>…</dl>` |
| Quiz | `<div class="quiz"><div class="q" data-answer="2"><p>Question?</p><ol><li>A</li><li>B</li><li>C</li><li>D</li></ol><p class="why">Because…</p></div>…</div>` |
| Open question | `<details class="qa"><summary>Question</summary><p>Answer</p></details>` |
| Summary | `<p class="final">…<b>key</b>…</p>` then `<p class="sign">— Vishwa Mohan</p>` |

## 4. SVG diagrams (hand-drawn look)

```html
<figure>
  <div class="dia"><svg viewBox="0 0 720 240" role="img" aria-label="Plain-English description of the diagram">
    <g class="rough">  <!-- shapes and lines only: the filter makes them wobble -->
      <rect class="box f-blue" x="40" y="60" width="200" height="110" rx="16"/>
      <path class="lr" d="M248 115 L 470 115" marker-end="url(#ahr)"/>
    </g>
    <!-- text goes OUTSIDE the rough group so it stays crisp -->
    <text class="th" x="140" y="110" text-anchor="middle">Client</text>
    <text class="ts" x="140" y="138" text-anchor="middle">small grey label</text>
  </svg></div>
  <figcaption>One line explaining the takeaway.</figcaption>
</figure>
```

- **Fills:** `f-blue f-green f-orange f-pink f-purple f-grey f-yellow f-teal f-card f-none`, combined with `box` for the ink outline.
- **Lines:** `ln` ink, `lr` violet, `lb` teal; add `dash` for dashed.
- **Arrowheads:** `marker-end="url(#ah)"` ink, `url(#ahr)` violet, `url(#ahb)` teal (the engine defines them).
- **Text:** `th` heading (28px handwriting), `tr` violet handwriting, `tb` teal handwriting, `t` body 17px, `ts` small grey 14.5px, `tm` monospace 14px.
- **Width:** use `viewBox="0 0 720 H"`. Add class `sm` to `.dia` for small, narrow diagrams of 520 or less.
- **Fitting text:** estimate width before placing it. `th` is about 13px per character, `t` about 8.5px, `ts` about 7.5px, `tm` about 8.6px. Make boxes wide enough with 12px of padding, and never let text overlap lines or other text. Keep everything inside the viewBox.
- Never hard-code colours. Classes only, so dark mode works.

## 5. Check your work

1. Run `python tools/build.py` from the project root and fix every warning that mentions your files. Ignore "page not written yet" for other notes.
2. Screenshot your page and **look at it**, especially the diagrams:
   `python "<scratchpad>/shot.py" "<scratchpad>/shots" "notes/<module>/<note>/index.html|1280|<note>"`
   To inspect a region, crop it with PIL. Fix any overlapping or clipped text and anything that looks broken.
3. Don't edit shared files (`assets/*`, `tools/*`, `index.html`, other modules' notes).

## 6. Original screenshots and full source coverage

`python tools/extract_images.py` reads the course `.docx` files in `_source/` and writes three things for every doc:

- `notes/<module>/<note>/img/NN.webp`: the doc's images in document order. The Git "deep dive" doc's images go in `notes/git/git-workflows/img/`, and the github page uses `../git-workflows/img/NN.webp`.
- `tools/images/<module>__<note>.txt`: the **complete** doc text, with headings (`#`), list items (`- `), tables (`| a | b |`) and image markers `[[IMG 07 | 07.webp | 1200x340]]` at their exact positions. This is the source of truth. It is more complete than the Drive text export the pages were first written from.
- `tools/images/<module>__<note>.json`: the size of each image and the text right before and after it.

### Placement rules (the course owner's instructions)

1. **Use every image.** Open each one with the Read tool to see what it shows.
2. **Insert these exactly as they are:** terminal and console output, program output, code-editor screenshots, browser results, tool or app UIs, official docs pages, photos, and any image carrying data, tables or results. Examples of tool and UI screenshots: AWS console, VS Code, Swagger UI, Postman, GitHub, DevTools, OpenAI tokenizer, TensorFlow Playground. Examples of official docs: LangChain, OpenAI, Python, FastAPI, Pydantic, MDN.
3. **Explanatory drawings** are concept illustrations, infographics and flowcharts that the course author drew. You may replace one with an SVG on the page, but only if that SVG contains everything in the image. In that case leave a comment where the image was: `<!-- img 07: replaced by SVG "OSI layer stack" -->`. When in doubt, insert the image.
4. **Placement:**
   - Put each image at the same spot as in the source, which is the marker's position in the `.txt`.
   - When a page shows code that the source showed as a screenshot, keep both. The text code stays copyable, and the screenshot goes right after it.
   - Group a code screenshot and its output screenshot side by side with `<div class="shots">…</div>`.
5. **Replace invented stand-ins.** Wherever the page has a typed-out output (`pre.out`), a mock-up SVG, or a table that was invented because the image was missing, swap in the real screenshot. Remove the stand-in when it shows the same thing, or worse, contradicts the real image. Fix any text that disagrees with what the screenshot really shows.
6. **Markup:**

   ```html
   <figure class="shot">
     <img src="img/03.webp" alt="What the screenshot shows, in words" width="1089" height="130">
     <figcaption>One line saying what to notice.</figcaption>
   </figure>
   ```

   Set `width` and `height` from the manifest. Add `class="shot sm"` for small images.

### Content rules

- Read the whole `.txt` and compare it with the page. Add anything missing: every paragraph, example, table row, list item and practice task.
- Run `python tools/coverage.py <module>/<note>` and work through its list.
  - "Images not placed" must reach **0**.
  - Every flagged text line must either be added, or you must confirm it is already covered in other words. The checker is word-based, so rewording triggers false alarms.
