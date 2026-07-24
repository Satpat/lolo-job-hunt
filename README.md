# Lolo Job Hunt

A directory of businesses in Bundoora VIC 3083 and nearby PT-connected suburbs
that typically hire casual/part-time staff (cafes, restaurants, retail,
supermarkets, gyms, pharmacies, salons, childcare, cinemas, healthcare) — built
to help with job hunting.

Live site: https://satpat.github.io/lolo-job-hunt/ (password gated — see
`build_ghpages.py` for the hint/logic; the gate is a light deterrent, not real
security, since anyone can read it from view-source).

## 1. Get a Google Places API key

1. Go to https://console.cloud.google.com/ and create a new project (or pick an existing one).
2. In "APIs & Services" > "Library", enable **Places API (New)**.
3. In "Billing", link a billing account (required by Google even though this
   project's usage — under ~15 search queries — stays well within the standing
   monthly free credit, so real cost should be ~$0).
4. In "APIs & Services" > "Credentials", create an API key.
5. Click the key to restrict it: under "API restrictions" choose "Restrict key"
   and select only "Places API (New)".
6. Copy the key.

## 2. Set the key locally (never commit it)

```bash
export GOOGLE_PLACES_API_KEY=your_key_here
```

## 3. Run the pipeline

```bash
cd bundoora-directory
source .venv/bin/activate
python3 fetch_businesses.py   # queries Google Places, writes data/businesses.json
python3 export_excel.py       # writes data/businesses.csv and Bundoora_Business_Directory.xlsx
```

## Output

- `data/businesses.json` — raw structured data (source of truth)
- `data/businesses.csv` — plain CSV
- `Bundoora_Business_Directory.xlsx` — spreadsheet with an "Applied?" / "Notes"
  column for tracking applications (import into Google Sheets to get filters
  for free — the AutoFilter carries over automatically)
- `site.html` — self-contained page for Claude Artifact publishing (custom SVG
  scatter map, since Artifacts can't load external map tiles)
- `index.html` — the GitHub Pages version, with a real Google Maps JS SDK map
  (street basemap + live TransitLayer for tram/train/bus routes, marker
  clustering, home icon at 566 Grimshaw St)
- `resume.html` — the resume builder (see below), linked from the Resume
  button in the header
- `resume.baseline.json` — Lolo's starting resume, fetched by `resume.html`
- `manifest.json` / `sw.js` / `icon-180.png` / `icon-512.png` — Home Screen
  install support: Add to Home Screen on iOS gets a burgundy heart icon and
  opens without Safari's address bar; `sw.js` caches `index.html` so the List
  view (search/filter/notes/applied) still works with no signal, since all
  business data is inlined in the page. The Map tab still needs a connection.
  Regenerate the icons with `python3 generate_icons.py` (needs `pillow`) only
  if the accent color ever changes — `manifest.json` is rewritten by
  `build_ghpages.py` on every run.

## 4. Get a Google Maps JavaScript API key (for index.html only)

1. In the same Google Cloud project, enable **Maps JavaScript API**.
2. Create a new API key, restrict it to **Maps JavaScript API** only.
3. Under "Application restrictions" choose **Websites** and add your Pages
   origin, e.g. `https://<username>.github.io/*`.
4. This key is *meant* to be public — it ends up in the page source by
   design, and Google's security model for it is the referrer + API
   restriction above, not secrecy.

```bash
export GMAPS_JS_KEY=your_key_here
python3 build_ghpages.py   # writes index.html
git add index.html && git commit -m "update site" && git push
```

GitHub Pages (configured via `gh api repos/<owner>/<repo>/pages`, branch
`main`, path `/`) picks up `index.html` automatically on push.

## 5. The resume builder

```bash
python3 build_resume.py   # writes resume.html (tailoring off until the Worker URL is set — see below)
```

`resume.html` is a self-contained resume editor: fill in the form on the left,
watch an A4 page render on the right, then export. It has **seven templates**
(Centered, Left, Underline, Minimal, Banner, Compact, and a two-column Sidebar),
a curated set of fonts and accent colours (plus a custom-colour picker), an
optional profile photo, a **Links** section for LinkedIn/portfolio, and a
**References** section (referee name, role, where they work, phone, email).

### Business-aware tailoring (the AI feature)

Tailoring lives in a **permanent panel** at the top of the editor column — search
the directory for a business, pick the role, hit **Tailor now**. The
**Tailor résumé** button on any card in the jobs directory deep-links here
(`resume.html?biz=<place_id>`) and simply pre-aims that panel.

The business field also takes **free text**: the directory only covers Bundoora
and nearby PT-connected suburbs, and Google Places misses plenty besides, so
whatever she types can be used verbatim (offered as *Use "…"* under the search
results). A hand-typed business has no category or suburb to lean on, so an
optional **"What kind of place is it?"** field appears to give the model
something to aim at, and the Worker is told the rest is unknown rather than
letting it assume. These save and re-open like directory ones, under an id of
`custom:<name>`.

- the **headline** and **summary** are rewritten to target that business, and
  experience items, skills, and bullets are **reordered** to surface the most
  relevant parts first;
- a matching **cover letter** is generated (toggle **Resume / Letter**), editable
  and exportable on its own;
- it's all **non-destructive** — the base resume in `localStorage` is never
  changed; tailoring is a separate layer you can **Clear**;
- each tailored version is **saved** (under `lolo_resume_tailors`); **Open saved**
  re-applies one without spending another API call;
- **Regenerate** spends a fresh call using **whatever is in the form right now** —
  so the loop is: add a certificate or a referee on the left, hit Regenerate, and
  the tailored copy accounts for it. (The panel is always on screen precisely so
  that loop doesn't require reloading a deep link, which is what the old
  dismissible notice bar forced.)

**Truthfulness is enforced, not hoped for.** The model may only rewrite the two
header fields and *reorder* existing content — it returns item ids and bullet
indices, and the Worker drops anything that doesn't match the submitted resume,
so it can't invent an employer, date, or skill.

This is the one part of the site that needs a backend: a tiny Cloudflare Worker
in [`../rr-tailor-worker/`](../rr-tailor-worker/) holds the OpenAI key and makes
the call. See that folder's README to deploy it, then rebuild with the URL:

```bash
TAILOR_WORKER_URL=https://rr-tailor.<subdomain>.workers.dev python3 build_resume.py
```

Until the Worker is deployed (`TAILOR_WORKER_URL` unset), everything else works
and the tailoring picker just says it isn't set up yet.

**Privacy.** Tailoring POSTs the resume to the Worker → OpenAI. The Worker is
stateless and stores nothing; OpenAI's API doesn't train on API-submitted data by
default. Everything else stays on the device. The photo, if added, is downscaled
in-browser and stored as a data URI — it goes on the PDF but never the Word file
(ATS-clean), and Australian employers generally don't expect one.

Two things are **stripped from the tailoring payload** before it leaves the
browser (`tailorPayload()` in `build_resume.py`): the **References** section and
the **photo**. Referees' phone numbers and emails belong to *other people* who
never agreed to an AI vendor holding them, and the photo is a large base64 blob
the model can't read. Neither is used for tailoring, so dropping them costs
nothing. Anything else added to the document model that carries a third party's
contact details should be stripped there too.

**Templates & ATS.** All seven templates print to PDF, and the **Word export now
matches the template you picked** — alignment, heading treatment, type sizes, the
Underline stub rule, and the Banner accent band. It stays **single-column for
every template** (the Sidebar maps to the left-aligned look), because two-column
DOCX parses badly in applicant tracking systems. See `DOCX_TEMPLATE` in
`build_resume.py` for the per-template spec.

Two OOXML tricks are worth knowing before editing that spec, since neither is
obvious: the Underline template's **short** stub rule is a paragraph border on an
empty paragraph *indented from the right* (a border spans the content box, so
narrowing the box narrows the rule) — no table, which keeps it ATS-clean. The
Banner band bleeds to the paper edge via **negative left/right indents** that
cancel the page margins.

> The Banner band starts at the **top margin** in Word, not the paper edge as it
> does on screen. That gap is deliberate: the only ways to bleed past the top
> margin are a first-page header — which hides her name and contact details from
> many ATS, the classic resume-parsing own goal — or a zero-top-margin section,
> which then wrecks the top of page 2. A thin white strip is the better trade.

**What it borrows.** The document model and the page layout come from
[Reactive Resume](https://github.com/amruthpillai/reactive-resume) (MIT) — the
`basics` / `summary` / `sections` / `metadata` shape from their schema, and the
single-column, centre-headed layout of their **Kakuna** template. Their app
itself is a full stack (TanStack Start, PostgreSQL, Better Auth, Docker), which
is not something this site can host — it's a static page on GitHub Pages. Taking
the schema instead means **Back up** writes JSON that Reactive Resume
recognises, so moving to the real app later needs no retyping.

**Exports.**

- **PDF** goes through the browser's own print pipeline (`window.print()` with a
  print stylesheet, `@page { size: A4; margin: 0 }`). Output keeps real,
  selectable text, which is what applicant tracking systems parse — a
  canvas-to-image PDF looks identical on screen and reads as blank to them.
  Choose "Save as PDF" as the destination.
- **Word** builds the `.docx` in the page, in vanilla JS: a `.docx` is a ZIP of
  XML parts, so the page assembles the five parts and writes the ZIP itself
  (stored entries, hand-rolled CRC32). No bundler and no CDN, which is what lets
  the page keep working offline from the Home Screen.
- **Back up / Restore** read and write the whole document as JSON.

> ⚠️ **The print-viewport trap.** While a page is printing, the browser sets the
> layout viewport to the **paper width (~794px)**, not the window width. Every
> `@media (max-width: …)` breakpoint above that therefore matches *during
> printing on every device, desktop included*. This once made the PDF come out
> **completely blank**: the responsive rule `body[data-pane="edit"]
> .preview-col { display: none }` fired mid-print and hid the very element the
> print stylesheet was trying to show. The `@media print` block now forces
> `.preview-col` back to `display: block` and hides the editor column outright.
> If you add a responsive rule that hides anything inside `#paper`'s ancestry,
> override it in the print block too — and verify with
> `chrome --headless --print-to-pdf`, not just Preview mode, because the bug is
> invisible unless the Preview pane happens to be the active one.

**The baseline.** `resume.baseline.json` is Lolo's starting resume, committed
next to the page and transcribed from her existing ATS resume. The editor
fetches it on every load and reconciles like this:

| On the device | What happens |
| --- | --- |
| Nothing saved yet | The baseline seeds the editor — she starts from her real resume, not a blank form |
| Saved edits, baseline unchanged | Her edits load; the baseline is ignored |
| Saved edits, baseline changed since she last saw it | Her edits load, plus a one-time bar offering to load the new baseline. **Dismiss** records the new signature so it does not nag again |

The **Baseline** button re-pulls it on demand (with a confirm, since it
replaces everything). A changed baseline is detected by hashing the fetched
JSON and comparing against `lolo_resume_baseline_seen`.

The baseline **never silently overwrites her edits**. That is deliberate:
"always load from GitHub" and "she is midway through editing" are the same
moment, and resolving it in the file's favour would be a data-loss bug wearing
a feature's clothes. To change what she starts from, edit
`resume.baseline.json`, push, and she gets the offer on her next load.

**Where the data lives.** Her working copy is only in `localStorage` on her
device, under `lolo_resume_v1`. Nothing is uploaded. Tell her to hit **Back up**
occasionally — clearing Safari's site data would wipe it.

**Privacy note on the baseline.** This repo is public, so everything in
`resume.baseline.json` — including her email and phone — is readable at
`https://<user>.github.io/lolo-job-hunt/resume.baseline.json`. The password gate
is client-side JS on `index.html` and does not protect a static JSON file, and
git history keeps the values even if they are removed later. This was a
considered call: it buys a complete resume on any fresh device with no retyping.

If that trade ever stops being worth it, blanking `basics.email` and
`basics.phone` in this file is enough for future visitors — she types them once
per device and `localStorage` remembers them — but scrubbing the values already
pushed needs a history rewrite (`git filter-repo`) plus a force-push, and
anything already scraped or cached is gone regardless.

**Notes for future edits.** The design tokens at the top of `build_resume.py`
are duplicated from `build_ghpages.py` (the two pages ship independently and
neither imports the other) — change the accent in both places. The page-break
dashed line in the preview marks where the printer will cut, which is the signal
that matters when the goal is keeping a casual-work resume to one page.
