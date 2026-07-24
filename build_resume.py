#!/usr/bin/env python3
"""Build resume.html — a self-contained resume builder for the Lolo Job Hunt site.

Design/data lineage: the document model (basics / summary / sections / metadata)
and the single-column centred layout are taken from Reactive Resume
(https://github.com/amruthpillai/reactive-resume, MIT). Exported JSON is shaped
like a Reactive Resume document, so Lolo can move to the full app later.

The page is static and loginless: state lives in localStorage, PDF prints through
the browser (real selectable text, ATS-friendly), and .docx is assembled as a
ZIP of OOXML in vanilla JS. The one dynamic piece is *business-aware tailoring*:
it POSTs the resume to a tiny Cloudflare Worker (rr-tailor-worker/) that asks an
LLM to reorder/reframe it for a chosen business — non-destructively (the base
resume is never mutated) and truthfully (the model may only reorder existing
content and rewrite the headline/summary; the Worker drops anything invented).

Run:  python3 build_resume.py
      TAILOR_WORKER_URL=https://rr-tailor.<sub>.workers.dev python3 build_resume.py
"""

import json
import os
from pathlib import Path

BASE = Path(__file__).parent
ACCENT_HEX = "#8e2a52"

# The deployed Worker URL. Empty until Veer runs `wrangler deploy` and pastes it
# back; when empty the tailoring UI shows a "not set up yet" note instead.
TAILOR_WORKER_URL = os.environ.get("TAILOR_WORKER_URL", "")

# ── fonts: (id, label, css stack, docx font name) ────────────────────────────
# One source of truth → the sheet CSS, the <select>, and the DOCX font map are
# all generated from this, so they can't drift. All stacks are system-safe so
# the page stays offline-capable (no Google Fonts fetch).
FONTS = [
    ("georgia", "Georgia", 'Georgia, "Times New Roman", serif', "Georgia"),
    ("palatino", "Palatino", '"Palatino Linotype", "Book Antiqua", Palatino, serif', "Book Antiqua"),
    ("cambria", "Cambria", "Cambria, Georgia, serif", "Cambria"),
    ("garamond", "Garamond", '"EB Garamond", Garamond, "Times New Roman", serif', "Garamond"),
    ("times", "Times", '"Times New Roman", Times, serif', "Times New Roman"),
    ("arial", "Arial", "Arial, Helvetica, sans-serif", "Arial"),
    ("calibri", "Calibri", 'Calibri, Carlito, "Segoe UI", sans-serif', "Calibri"),
    ("verdana", "Verdana", "Verdana, Geneva, sans-serif", "Verdana"),
    ("tahoma", "Tahoma", 'Tahoma, "Segoe UI", sans-serif', "Tahoma"),
]
FONT_CSS = "\n".join(f'.sheet[data-font="{i}"] {{ font-family: {stack}; }}' for i, _, stack, _ in FONTS)
FONT_OPTIONS = "\n".join(f'<option value="{i}">{label}</option>' for i, label, _, _ in FONTS)
DOCX_FONTS = {i: docx for i, _, _, docx in FONTS}
FONT_IDS = [i for i, _, _, _ in FONTS]

# ── colours: (hex, label) ────────────────────────────────────────────────────
COLOURS = [
    (ACCENT_HEX, "Burgundy"),
    ("#16181d", "Black"),
    ("#1f3a5f", "Navy"),
    ("#2f5d50", "Forest"),
    ("#0f6f74", "Teal"),
    ("#6b2d6b", "Plum"),
    ("#37474f", "Slate"),
    ("#7a1f2b", "Maroon"),
    ("#5b3a86", "Violet"),
    ("#8a5a2b", "Bronze"),
]
COLOUR_OPTIONS = "\n".join(f'<option value="{h}">{label}</option>' for h, label in COLOURS)

# ── templates: (id, label) ───────────────────────────────────────────────────
# All are hand-built CSS layouts for the on-screen/PDF sheet; the Word export
# stays single-column regardless (ATS-clean). Ordered single-column first.
TEMPLATES = [
    ("kakuna", "Centered"),
    ("onyx", "Left"),
    ("underline", "Underline"),
    ("minimal", "Minimal"),
    ("banner", "Banner"),
    ("compact", "Compact"),
    ("sidebar", "Sidebar"),
]
TEMPLATE_OPTIONS = "\n".join(f'<option value="{i}">{label}</option>' for i, label in TEMPLATES)
TEMPLATE_IDS = [i for i, _ in TEMPLATES]

# ── roles (what job Lolo wants at the business — fed into tailoring) ──────────
# (label, indicative casual pay). Pay is a hint for her only; the value sent to
# the Worker is just the role name.
ROLE_GROUPS = [
    ("Hospitality & food", [
        ("Barista / Café all-rounder", "$22–35/hr"),
        ("Waiter / Food runner", "$24–28/hr"),
        ("Kitchen hand", "$22–26/hr"),
        ("Front of house / Host", ""),
    ]),
    ("Retail & supermarkets", [
        ("Retail sales assistant", "$20–25/hr"),
        ("Supermarket team member", "$23–27/hr"),
        ("Checkout operator", ""),
        ("Night fill / Stocker", ""),
    ]),
    ("Care & education", [
        ("Tutor", "$25–40/hr"),
        ("Disability / Aged care support worker", "$28–35/hr"),
        ("Childcare assistant", ""),
    ]),
    ("Admin & campus", [
        ("Receptionist / Admin assistant", "$24–30/hr"),
        ("University / Library assistant", "$25–32/hr"),
    ]),
    ("General", [
        ("Customer service", ""),
        ("General all-rounder", ""),
    ]),
]
# A sensible default role per business group, pre-selected in the picker.
DEFAULT_ROLE_BY_GRP = {
    "Hospo": "Barista / Café all-rounder",
    "Grocery": "Supermarket team member",
    "Retail": "Retail sales assistant",
    "Health": "Receptionist / Admin assistant",
    "Fitness": "Receptionist / Admin assistant",
    "Family": "Childcare assistant",
}

# ── businesses (for the tailoring picker) ────────────────────────────────────
# Category maps duplicated from build_ghpages.py on purpose (the two pages ship
# independently). Keep in sync if categories change.
GROUP_OF = {
    "Cafe": "Hospo", "Restaurant/Takeaway": "Hospo", "Fast Food": "Hospo",
    "Supermarket": "Grocery", "Retail": "Retail", "Retail (general)": "Retail",
    "Medical Clinic": "Health", "Hospital": "Health", "Dentist": "Health",
    "Allied Health": "Health", "Pharmacy": "Health", "Gym": "Fitness",
    "Salon/Beauty": "Fitness", "Childcare": "Family", "Cinema": "Family",
}
CATEGORY_DISPLAY = {
    "Retail (general)": "Retail", "Restaurant/Takeaway": "Restaurant", "Salon/Beauty": "Beauty",
}
try:
    _biz = json.loads((BASE / "data" / "businesses.json").read_text())
except Exception:
    _biz = []
_seen = set()
BUSINESSES = []
for d in _biz:
    pid = d.get("place_id")
    if not pid or not d.get("name") or pid in _seen:
        continue
    _seen.add(pid)
    BUSINESSES.append({
        "id": pid,
        "name": d["name"],
        "cat": CATEGORY_DISPLAY.get(d["category"], d.get("category", "")),
        "grp": GROUP_OF.get(d.get("category", ""), "Other"),
        "suburb": d.get("suburb", ""),
    })
BUSINESSES_JSON = json.dumps(BUSINESSES, separators=(",", ":")).replace("</", "<\\/")

HTML = r"""<!doctype html>
<meta charset="utf-8" />
<title>Resume &mdash; Lolo Job Hunt</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="__ACCENT__" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Lolo Resume" />
<link rel="manifest" href="manifest.json" />
<link rel="apple-touch-icon" href="icon-180.png" />
<link rel="icon" href="icon-512.png" />
<style>
:root {
  --bg: #faf3f8;
  --surface: #ffffff;
  --surface-2: #f4e7f0;
  --ink: #3a1e2e;
  --ink-dim: #7c5568;
  --ink-faint: #a98ca0;
  --line: #ecd7e5;
  --line-soft: #f2e2ec;
  --accent: __ACCENT__;
  --accent-ink: #ffffff;
  --accent-soft: #f6dce7;
  --radius: 10px;

  --font-display: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
  --font-body: ui-sans-serif, system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "Roboto Mono", Menlo, Consolas, monospace;
}
:root[data-theme="dark"] {
  --bg: #1c0f17; --surface: #241620; --surface-2: #2c1b28;
  --ink: #f3e4ec; --ink-dim: #c9a8bc; --ink-faint: #93748a;
  --line: #3a2430; --line-soft: #2f1d29;
  --accent: #e8709f; --accent-ink: #2a0f1c; --accent-soft: #3a2130;
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
a { color: inherit; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }
}

/* ── app chrome ─────────────────────────────────────────────────────── */

header.top { padding: 24px 16px 14px; max-width: 1180px; margin: 0 auto; }
h1 {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(26px, 5vw, 34px);
  letter-spacing: -0.02em;
  margin: 0 0 6px;
}
.meta-line { font-family: var(--font-mono); font-size: 12px; color: var(--ink-faint); margin: 0; }

.controls {
  position: sticky;
  top: 0;
  z-index: 30;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
  padding: 10px 16px 12px;
}
.controls-inner { max-width: 1180px; margin: 0 auto; display: flex; flex-direction: column; gap: 10px; }
.tool-row { display: flex; gap: 8px; align-items: center; }
.spacer { flex: 1 1 auto; }

.chip-row-wrap { position: relative; }
.chip-row {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-right: 16px;
  mask-image: linear-gradient(to right, #000 calc(100% - 26px), transparent 100%);
  -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 26px), transparent 100%);
}
.chip-row::-webkit-scrollbar { display: none; }
.chip-label {
  display: flex; align-items: center; flex: 0 0 auto;
  font-family: var(--font-mono); font-size: 10px; font-weight: 700;
  letter-spacing: 0.09em; text-transform: uppercase; color: var(--ink-faint);
  padding-right: 2px;
}

.sheet-btn, .toggle-btn {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  height: 36px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  border-radius: var(--radius);
  text-decoration: none;
  cursor: pointer;
  white-space: nowrap;
}
.sheet-btn { border: 1px solid var(--accent); background: var(--accent); color: var(--accent-ink); }
.sheet-btn:hover { opacity: 0.9; }
.sheet-btn:disabled { opacity: 0.5; cursor: default; }
.toggle-btn { border: 1px solid var(--line); background: var(--surface); color: var(--ink-dim); }
.toggle-btn[data-active="1"] { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
.toggle-btn:disabled { opacity: 0.45; cursor: default; }
/* These set display:flex, which outranks the UA's [hidden] { display: none }. */
.sheet-btn[hidden], .toggle-btn[hidden] { display: none; }

.view-toggle {
  display: none;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
  flex: 0 0 auto;
}
.view-btn {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  height: 36px;
  padding: 0 14px;
  border: 0;
  background: var(--surface);
  color: var(--ink-dim);
  cursor: pointer;
}
.view-btn + .view-btn { border-left: 1px solid var(--line); }
.view-btn[data-active="1"] { background: var(--accent); color: var(--accent-ink); }

/* The resume/letter mode toggle reuses the view-toggle look but is always shown. */
.mode-toggle { display: flex; border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; flex: 0 0 auto; }
.mode-toggle[hidden] { display: none; }
.mode-btn {
  font-family: var(--font-mono); font-size: 13px; font-weight: 600; height: 36px; padding: 0 14px;
  border: 0; background: var(--surface); color: var(--ink-dim); cursor: pointer;
}
.mode-btn + .mode-btn { border-left: 1px solid var(--line); }
.mode-btn[data-active="1"] { background: var(--accent); color: var(--accent-ink); }

select.mini {
  font: inherit;
  font-size: 13px;
  font-family: var(--font-mono);
  height: 36px;
  padding: 0 30px 0 10px;
  flex: 0 0 auto;
  max-width: 46vw;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background-color: var(--surface);
  color: var(--ink);
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5L6 8l3.5-3.5' stroke='%237c5568' stroke-width='1.6' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}
:root[data-theme="dark"] select.mini {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5L6 8l3.5-3.5' stroke='%23c9a8bc' stroke-width='1.6' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}
.swatch {
  width: 36px; height: 36px; flex: 0 0 auto; padding: 0;
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--surface); cursor: pointer;
}
.swatch::-webkit-color-swatch-wrapper { padding: 4px; }
.swatch::-webkit-color-swatch { border: 0; border-radius: 6px; }

/* ── two-pane layout ────────────────────────────────────────────────── */

.wrap {
  max-width: 1180px;
  margin: 0 auto;
  padding: 18px 16px 80px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}
.preview-col { position: sticky; top: 96px; }
@media (max-width: 900px) {
  .wrap { grid-template-columns: minmax(0, 1fr); }
  .view-toggle { display: flex; }
  .preview-col { position: static; }
  body[data-pane="edit"] .preview-col { display: none; }
  body[data-pane="preview"] .form-col { display: none; }
}

/* ── the editor ─────────────────────────────────────────────────────── */

.notice {
  display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px;
  border: 1px solid var(--accent); background: var(--accent-soft); color: var(--ink);
  border-radius: var(--radius); padding: 10px 12px; margin-bottom: 12px;
  font-family: var(--font-mono); font-size: 11.5px; line-height: 1.45;
}
.notice span { flex: 1 1 160px; min-width: 0; }
.notice[hidden] { display: none; }
.notice.busy { border-color: var(--line); background: var(--surface-2); color: var(--ink-dim); }

.sec {
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--surface); margin-bottom: 12px; overflow: hidden;
}
.sec[data-hidden="1"] { opacity: 0.5; }
/* Section headers carry the page's scanning rhythm, so they get a tinted bar, a
   full-strength ink colour and an accent edge rather than the faint grey label
   they used to be — ~3:1 against white before, ~12:1 now, in both themes. */
.sec-head {
  display: flex; gap: 6px; align-items: center; padding: 11px 12px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--line);
  box-shadow: inset 3px 0 0 var(--accent);
}
.sec-title {
  font-family: var(--font-mono); font-size: 11.5px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink); flex: 1 1 auto; min-width: 0;
}
.sec-head + .item, .sec-head + .add-row, .sec-head + .empty-note { border-top: 0; }
.ico {
  width: 30px; height: 30px; flex: 0 0 auto; display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: 13px; line-height: 1;
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--surface); color: var(--ink-dim); cursor: pointer;
}
.ico:disabled { opacity: 0.25; cursor: default; }
.ico.on { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }
@media (hover: hover) and (pointer: fine) {
  .ico:not(:disabled):hover { border-color: var(--accent); color: var(--accent); }
}

.item { border-top: 1px solid var(--line-soft); padding: 12px; }
.item-bar { display: flex; gap: 6px; justify-content: flex-end; margin-bottom: 8px; }
.field { margin-bottom: 9px; }
.field:last-child { margin-bottom: 0; }
/* --ink-faint on white is only ~3:1, under AA — field labels and hints are text
   she has to read, so they step up to --ink-dim (~6.5:1). --ink-faint stays for
   genuinely decorative chrome (the meta line, timestamps). */
.field label {
  display: block; font-family: var(--font-mono); font-size: 10.5px; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-dim); margin-bottom: 4px;
}
.field input, .field textarea {
  width: 100%; font: inherit; font-size: 14px; padding: 8px 10px;
  border-radius: var(--radius); border: 1px solid var(--line); background: var(--surface); color: var(--ink);
}
.field textarea { min-height: 74px; resize: vertical; line-height: 1.45; }
.field textarea.tall { min-height: 220px; }
.field input:focus, .field textarea:focus {
  outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft);
}
.field .hint { font-family: var(--font-mono); font-size: 10.5px; color: var(--ink-dim); margin-top: 4px; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 9px; }
@media (max-width: 520px) { .grid2 { grid-template-columns: 1fr; } }

.add-row { border-top: 1px solid var(--line-soft); padding: 10px 12px; }
.add-btn {
  width: 100%; font-family: var(--font-mono); font-size: 12px; font-weight: 600; padding: 9px;
  border-radius: 999px; border: 1px dashed var(--line); background: transparent; color: var(--ink-dim); cursor: pointer;
}
@media (hover: hover) and (pointer: fine) {
  .add-btn:hover { border-color: var(--accent); color: var(--accent); }
}
.empty-note {
  border-top: 1px solid var(--line-soft); padding: 14px 12px;
  font-family: var(--font-mono); font-size: 11.5px; color: var(--ink-dim);
}

/* photo control */
.photo-row { display: flex; gap: 10px; align-items: center; }
.photo-thumb {
  width: 52px; height: 52px; flex: 0 0 auto; border-radius: 50%; object-fit: cover;
  border: 1px solid var(--line); background: var(--surface-2);
}
.photo-thumb.empty { display: flex; align-items: center; justify-content: center; font-size: 20px; color: var(--ink-faint); }
.mini-btn {
  font-family: var(--font-mono); font-size: 11px; font-weight: 600; padding: 6px 10px;
  border-radius: 999px; border: 1px solid var(--line); background: var(--surface); color: var(--ink-dim); cursor: pointer;
}
.mini-btn:hover { border-color: var(--accent); color: var(--accent); }

/* saved tailored versions list */
.saved-list { display: flex; flex-direction: column; gap: 6px; }
.saved-list[hidden] { display: none; }
.saved-row { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid var(--line); border-radius: var(--radius); }
.saved-row .nm { flex: 1 1 auto; min-width: 0; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.saved-row .dt { font-family: var(--font-mono); font-size: 10px; color: var(--ink-dim); flex: 0 0 auto; }
.saved-row[data-active="1"] { border-color: var(--accent); background: var(--accent-soft); }

/* ── the tailoring panel ─────────────────────────────────────────────────
   Permanently docked at the top of the editor column (it used to be a notice
   bar that vanished on Dismiss and was clobbered by every other message), so
   re-tailoring is always one tap away and never has to be re-summoned. */
#tailorPanel .sec { margin-bottom: 14px; }
.tailor-body { padding: 12px; display: flex; flex-direction: column; gap: 10px; }
.tailor-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.tailor-row > .grow { flex: 1 1 150px; min-width: 0; }
.tailor-status {
  font-family: var(--font-mono); font-size: 11.5px; line-height: 1.45; color: var(--ink);
  border: 1px solid var(--accent); background: var(--accent-soft);
  border-radius: var(--radius); padding: 8px 10px;
}
.tailor-status[data-idle="1"] { border-color: var(--line); background: var(--surface-2); color: var(--ink-dim); }
.tailor-status b { font-weight: 700; }
.tailor-hint { font-family: var(--font-mono); font-size: 10.5px; color: var(--ink-dim); }
.biz-search { position: relative; }
.biz-results {
  display: flex; flex-direction: column; gap: 4px; margin-top: 6px;
  max-height: 190px; overflow-y: auto;
}
.biz-results[hidden] { display: none; }
.biz-hit {
  display: flex; gap: 8px; align-items: baseline; text-align: left; width: 100%;
  font: inherit; font-size: 13px; padding: 7px 10px; cursor: pointer;
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--surface); color: var(--ink);
}
.biz-hit .sub { font-family: var(--font-mono); font-size: 10px; color: var(--ink-dim); margin-left: auto; flex: 0 0 auto; }
@media (hover: hover) and (pointer: fine) {
  .biz-hit:hover { border-color: var(--accent); }
}
.tailor-spin { display: inline-block; width: 11px; height: 11px; border-radius: 50%;
  border: 2px solid var(--accent); border-top-color: transparent; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── the page ───────────────────────────────────────────────────────── */

.paper-frame { overflow: hidden; }
.scaler { transform-origin: top left; }
#paper { position: relative; }

.sheet {
  width: 210mm;
  min-height: 297mm;
  padding: 12mm 14mm;
  background: #fff;
  color: #16181d;
  box-shadow: 0 1px 2px rgba(58, 30, 46, 0.12), 0 12px 34px rgba(58, 30, 46, 0.14);
  border-radius: 2px;
  font-size: 10.5pt;
  line-height: 1.42;
}
__FONT_CSS__

.rs-doc { display: block; }
.rs-head { text-align: center; margin-bottom: 6mm; }
.rs-name { font-size: 20pt; font-weight: 700; line-height: 1.15; letter-spacing: 0.01em; }
.rs-headline { font-size: 10.5pt; margin-top: 1.5mm; }
.rs-photo { width: 26mm; height: 26mm; border-radius: 50%; object-fit: cover; margin: 0 auto 3mm; display: block; }
.rs-contact {
  margin-top: 2.5mm; font-size: 9.5pt;
  display: flex; flex-wrap: wrap; justify-content: center; gap: 1mm 4mm;
}
.rs-contact a { text-decoration: none; }
.rs-sec { margin-bottom: 5mm; }
.rs-sec:last-child { margin-bottom: 0; }
/* Heavier weight and a 1pt rule (was 0.5pt, which some printers drop to a ghost
   line): the headings anchor the page for a human skim-reader. Size is unchanged
   on purpose — bumping it reflows a resume that is deliberately kept to one page. */
.rs-sec > h2 {
  font-size: 11pt; font-weight: 800; text-align: center; text-transform: uppercase;
  letter-spacing: 0.11em; margin: 0 0 2.5mm; padding-bottom: 1mm;
  color: var(--doc-accent); border-bottom: 1pt solid var(--doc-accent);
}
.rs-item { margin-bottom: 3.5mm; }
.rs-item:last-child { margin-bottom: 0; }
.rs-row { display: flex; gap: 4mm; align-items: baseline; }
.rs-row .rs-t { font-weight: 700; flex: 1 1 auto; min-width: 0; }
.rs-row .rs-d { flex: 0 0 auto; font-size: 9.5pt; white-space: nowrap; }
.rs-sub { font-size: 10pt; font-style: italic; }
.rs-body { margin: 1mm 0 0; }
.rs-body ul { margin: 0; padding-left: 4.5mm; }
.rs-body li { margin-bottom: 0.6mm; }
.rs-line { margin: 0; }
.rs-skill { margin-bottom: 1.2mm; }
.rs-skill b { font-weight: 700; }

/* onyx — left-aligned single column */
.sheet[data-template="onyx"] .rs-head { text-align: left; }
.sheet[data-template="onyx"] .rs-photo { margin: 0 0 3mm; }
.sheet[data-template="onyx"] .rs-contact { justify-content: flex-start; }
.sheet[data-template="onyx"] .rs-sec > h2 { text-align: left; }

/* compact — dense left-aligned single column */
.sheet[data-template="compact"] { font-size: 9.7pt; line-height: 1.32; padding: 10mm 12mm; }
.sheet[data-template="compact"] .rs-head { text-align: left; margin-bottom: 4mm; }
.sheet[data-template="compact"] .rs-name { font-size: 17pt; }
.sheet[data-template="compact"] .rs-photo { margin: 0 0 2mm; width: 20mm; height: 20mm; }
.sheet[data-template="compact"] .rs-contact { justify-content: flex-start; }
.sheet[data-template="compact"] .rs-sec { margin-bottom: 3.5mm; }
.sheet[data-template="compact"] .rs-sec > h2 { text-align: left; font-size: 10pt; margin-bottom: 1.5mm; }
.sheet[data-template="compact"] .rs-item { margin-bottom: 2.3mm; }

/* sidebar — two columns; left holds photo/contact/skills etc. */
.sheet[data-template="sidebar"] { padding: 0; }
.sheet[data-template="sidebar"] .rs-doc { display: flex; min-height: 297mm; }
.rs-sidebar {
  width: 64mm; flex: 0 0 64mm; padding: 12mm 8mm;
  background: color-mix(in srgb, var(--doc-accent) 12%, #fff);
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.rs-main { flex: 1 1 auto; padding: 12mm 10mm 12mm 9mm; min-width: 0; }
.rs-sidebar .rs-photo { margin: 0 auto 4mm; width: 30mm; height: 30mm; }
.rs-sidebar .rs-name { font-size: 16pt; text-align: center; }
.rs-sidebar .rs-headline { text-align: center; font-size: 9.5pt; }
.rs-sidebar .rs-contact { flex-direction: column; align-items: center; text-align: center; gap: 1mm; margin-top: 3mm; }
.rs-sidebar .rs-sec > h2 { text-align: left; font-size: 10pt; }
.rs-sidebar .rs-sec { margin-top: 5mm; margin-bottom: 0; }

/* underline — left-aligned; a short accent bar under each heading (no full rule) */
.sheet[data-template="underline"] .rs-head { text-align: left; }
.sheet[data-template="underline"] .rs-photo { margin: 0 0 3mm; }
.sheet[data-template="underline"] .rs-contact { justify-content: flex-start; }
.sheet[data-template="underline"] .rs-sec > h2 {
  text-align: left; border-bottom: none; padding-bottom: 0; margin-bottom: 2mm;
}
.sheet[data-template="underline"] .rs-sec > h2::after {
  content: ""; display: block; width: 12mm; height: 1.4pt;
  background: var(--doc-accent); margin-top: 1.2mm;
}

/* minimal — left-aligned, no rules, airy, wide-tracked headings */
.sheet[data-template="minimal"] .rs-head { text-align: left; }
.sheet[data-template="minimal"] .rs-photo { margin: 0 0 3mm; }
.sheet[data-template="minimal"] .rs-contact { justify-content: flex-start; }
.sheet[data-template="minimal"] .rs-sec { margin-bottom: 6mm; }
.sheet[data-template="minimal"] .rs-sec > h2 {
  text-align: left; border-bottom: none; padding-bottom: 0; margin-bottom: 2mm;
  font-size: 10pt; letter-spacing: 0.18em;
}

/* banner — full-bleed accent header band behind the name/contact */
.sheet[data-template="banner"] .rs-head {
  margin: -12mm -14mm 6mm;            /* cancel the sheet padding to bleed to edges */
  padding: 10mm 14mm 7mm;
  background: var(--doc-accent);
  color: #fff;
  text-align: center;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.sheet[data-template="banner"] .rs-head .rs-name,
.sheet[data-template="banner"] .rs-head .rs-headline { color: #fff; }
.sheet[data-template="banner"] .rs-head .rs-contact a { color: #fff; }
.sheet[data-template="banner"] .rs-photo { border: 2px solid rgba(255,255,255,0.6); }

/* cover letter layout */
.rs-letter { font-size: 10.5pt; line-height: 1.5; }
.rs-letter .lt-from { margin-bottom: 6mm; }
.rs-letter .lt-name { font-size: 15pt; font-weight: 700; }
.rs-letter .lt-contact { font-size: 9.5pt; color: #333; margin-top: 1mm; }
.rs-letter .lt-date { margin: 4mm 0; }
.rs-letter .lt-to { margin-bottom: 5mm; }
.rs-letter p { margin: 0 0 3mm; }
.rs-letter .lt-sign { margin-top: 5mm; }

/* on-screen page-cut guide */
.pgguide { position: absolute; left: 0; right: 0; border-top: 1px dashed var(--accent); opacity: 0.55; pointer-events: none; }
.pgguide span {
  position: absolute; right: 0; top: 3px; font-family: var(--font-mono); font-size: 9px;
  letter-spacing: 0.06em; text-transform: uppercase; color: var(--accent);
  background: var(--bg); padding: 1px 5px; border-radius: 999px;
}
.paper-meta {
  display: flex; align-items: center; gap: 8px; font-family: var(--font-mono);
  font-size: 11px; color: var(--ink-faint); margin-bottom: 8px;
}
.clear-btn {
  font-family: var(--font-mono); font-size: 11px; color: var(--accent);
  background: none; border: 0; padding: 0; text-decoration: underline; cursor: pointer;
}

footer { text-align: center; font-size: 12px; color: var(--ink-faint); padding: 8px 16px 40px; }
footer .sig { font-family: var(--font-mono); }
footer a { color: var(--ink-dim); text-decoration-color: var(--line); }

@media print {
  @page { size: A4; margin: 0; }
  html, body { background: #fff; margin: 0; padding: 0; }
  body * { visibility: hidden; }
  #paper, #paper * { visibility: visible; }
  .controls, footer, header.top, .paper-meta, .pgguide { display: none !important; }
  /* While printing, the layout viewport becomes the PAPER width (~794px), so the
     900px "mobile" query below always matches — which used to hide .preview-col
     whenever the Edit pane was active and print a blank page on every device.
     Force the sheet back on, and drop the editor chrome so nothing reserves space. */
  .form-col, #tailorPanel, .notice { display: none !important; }
  .wrap { display: block !important; padding: 0 !important; }
  .preview-col { display: block !important; }
  .preview-col, .paper-frame { position: static !important; overflow: visible !important; }
  .scaler { transform: none !important; width: auto !important; height: auto !important; }
  #paper { position: absolute; left: 0; top: 0; width: 210mm; }
  .sheet { box-shadow: none; border-radius: 0; margin: 0; min-height: 0; }
  .rs-sec, .rs-item { break-inside: avoid; page-break-inside: avoid; }
  .rs-sec > h2 { break-after: avoid; page-break-after: avoid; }
}
</style>

<header class="top">
  <h1>Build your resume</h1>
  <p class="meta-line" id="cheerLine">fill it in on the left &rarr; it updates on the right</p>
</header>

<div class="controls">
  <div class="controls-inner">
    <div class="tool-row">
      <a class="toggle-btn" href="./index.html">&larr; Jobs</a>
      <div class="view-toggle">
        <button class="view-btn" data-pane="edit" data-active="1">Edit</button>
        <button class="view-btn" data-pane="preview" data-active="0">Preview</button>
      </div>
      <div class="mode-toggle" id="modeToggle" hidden>
        <button class="mode-btn" data-mode="resume" data-active="1">Resume</button>
        <button class="mode-btn" data-mode="cover" data-active="0">Letter</button>
      </div>
      <span class="spacer"></span>
      <button class="toggle-btn" id="docxBtn">Word</button>
      <button class="sheet-btn" id="pdfBtn">PDF</button>
    </div>
    <div class="chip-row-wrap">
      <div class="chip-row">
        <span class="chip-label">Template</span>
        <select class="mini" id="templateSel" title="Page layout">
__TEMPLATE_OPTIONS__
        </select>
        <span class="chip-label">Font</span>
        <select class="mini" id="fontSel" title="Font">
__FONT_OPTIONS__
        </select>
        <span class="chip-label">Colour</span>
        <select class="mini" id="accentSel" title="Accent colour">
__COLOUR_OPTIONS__
          <option value="custom">Custom&hellip;</option>
        </select>
        <input class="swatch" type="color" id="accentPick" title="Custom colour" value="__ACCENT__" />
        <button class="toggle-btn" id="baselineBtn">Baseline</button>
        <button class="toggle-btn" id="saveJsonBtn">Back&nbsp;up</button>
        <button class="toggle-btn" id="loadJsonBtn">Restore</button>
        <input type="file" id="jsonFile" accept="application/json,.json" hidden />
        <input type="file" id="photoFile" accept="image/*" hidden />
      </div>
    </div>
  </div>
</div>

<div class="wrap">
  <div class="form-col">
    <div id="tailorPanel"></div>
    <div class="notice" id="notice" hidden></div>
    <div id="form"></div>
  </div>
  <div class="preview-col">
    <div class="paper-meta">
      <span id="pageCount"></span>
      <span class="spacer"></span>
      <span id="savedAt"></span>
    </div>
    <div class="paper-frame" id="paperFrame">
      <div class="scaler" id="scaler">
        <div id="paper"><div class="sheet" id="sheet"></div></div>
      </div>
    </div>
  </div>
</div>

<footer>
  Built on the <a href="https://github.com/amruthpillai/reactive-resume">Reactive&nbsp;Resume</a> schema (MIT).
  <br />Everything stays on this device &mdash; nothing is uploaded (tailoring aside).
  <br /><span class="sig">VeerLo&trade;</span>
</footer>

<script>
/* ══════════════════════════════════════════════════════════════════════
   Config injected at build time
   ══════════════════════════════════════════════════════════════════════ */
const ACCENT = "__ACCENT__";
const WORKER_URL = "__WORKER_URL__";
const BUSINESSES = __BUSINESSES__;
const ROLE_GROUPS = __ROLE_GROUPS__;
const DEFAULT_ROLE_BY_GRP = __DEFAULT_ROLE_BY_GRP__;
const FONT_IDS = __FONT_IDS__;
const TEMPLATE_IDS = __TEMPLATE_IDS__;
const DOCX_FONTS = __DOCX_FONTS__;

const STORE_KEY = "lolo_resume_v1";
const SEEN_KEY = "lolo_resume_baseline_seen";
const TAILORS_KEY = "lolo_resume_tailors";
const BASELINE_URL = "./resume.baseline.json";

/* ══════════════════════════════════════════════════════════════════════
   Document model
   ══════════════════════════════════════════════════════════════════════ */

const SECTION_DEFS = {
  summary: { title: "About me", single: true, fields: [
    { k: "content", label: "A few lines about you", type: "textarea",
      ph: "Friendly and reliable, currently studying at La Trobe. Happy on my feet, quick to learn, and available most evenings and weekends." },
  ] },
  experience: { title: "Experience", add: "Add a job",
    empty: "No jobs yet — volunteering, helping at a family business and school work placements all count.",
    fields: [
      { k: "position", label: "Role", ph: "Barista", half: true },
      { k: "company", label: "Where", ph: "Cafe on Grimshaw", half: true },
      { k: "location", label: "Location", ph: "Bundoora VIC", half: true },
      { k: "period", label: "When", ph: "Feb 2025 – now", half: true },
      { k: "description", label: "What you did", type: "lines",
        ph: "Served 150+ customers a shift on the coffee machine\nTrained two new starters on the POS",
        hint: "One line per bullet point. Start with a verb." },
    ] },
  education: { title: "Education", add: "Add a school or course", fields: [
    { k: "school", label: "School / uni", ph: "La Trobe University", half: true },
    { k: "degree", label: "Qualification", ph: "Bachelor of Science", half: true },
    { k: "area", label: "Subject", ph: "Computer Science", half: true },
    { k: "period", label: "When", ph: "2025 – 2027", half: true },
    { k: "description", label: "Highlights", type: "lines", ph: "Dean's list, first year" },
  ] },
  projects: { title: "Projects", add: "Add a project", fields: [
    { k: "name", label: "Name", ph: "Bundoora Job Directory", half: true },
    { k: "period", label: "When", ph: "2026", half: true },
    { k: "description", label: "What it is", type: "lines", ph: "Mapped 300+ local businesses that hire casual staff" },
  ] },
  skills: { title: "Skills", add: "Add a skill group", fields: [
    { k: "name", label: "Group", ph: "Customer service", half: true },
    { k: "keywords", label: "Skills", type: "tags", ph: "POS systems, cash handling, barista", hint: "Separate with commas.", half: true },
  ] },
  certifications: { title: "Certificates", add: "Add a certificate",
    empty: "RSA, Food Handling, First Aid and a Working with Children Check all belong here — employers screen on these.",
    fields: [
      { k: "title", label: "Certificate", ph: "Responsible Service of Alcohol (RSA)", half: true },
      { k: "issuer", label: "Issued by", ph: "VCGLR", half: true },
      { k: "date", label: "Date", ph: "March 2026", half: true },
    ] },
  languages: { title: "Languages", add: "Add a language", fields: [
    { k: "language", label: "Language", ph: "Nepali", half: true },
    { k: "fluency", label: "Level", ph: "Native", half: true },
  ] },
  availability: { title: "Availability", single: true, fields: [
    { k: "content", label: "When you can work", type: "lines",
      ph: "Weekday evenings from 5pm\nAll day Saturday and Sunday",
      hint: "Casual employers read this first. One line each." },
  ] },
  references: { title: "References", add: "Add a referee",
    empty: "Two referees is plenty — a manager, supervisor or teacher who has actually seen you work. Ask them first.",
    fields: [
      { k: "name", label: "Name", ph: "Priya Sharma", half: true },
      { k: "role", label: "Their role", ph: "Café Manager", half: true },
      { k: "company", label: "Where", ph: "Cafe on Grimshaw", half: true },
      { k: "phone", label: "Phone", type: "tel", ph: "0400 000 000", half: true },
      { k: "email", label: "Email (optional)", type: "email", ph: "priya@example.com", half: true },
    ] },
};

const ORDER = ["summary", "experience", "education", "projects", "skills", "languages", "certifications", "availability", "references"];
/* In the sidebar template, these go to the left column; the rest stay in main. */
const SIDEBAR_SECTIONS = new Set(["skills", "languages", "certifications", "availability"]);

const uid = () =>
  (crypto.randomUUID ? crypto.randomUUID() : "id-" + Math.random().toString(36).slice(2) + Date.now().toString(36));
const clone = (o) => (typeof structuredClone === "function" ? structuredClone(o) : JSON.parse(JSON.stringify(o)));

function blankItem(id) {
  const it = { id: uid(), hidden: false };
  for (const f of SECTION_DEFS[id].fields) it[f.k] = "";
  return it;
}

function blankDoc() {
  const doc = {
    basics: { name: "", headline: "", email: "", phone: "", location: "",
              website: { url: "", label: "" }, profiles: [] },
    picture: { url: "", show: false },
    summary: { title: SECTION_DEFS.summary.title, hidden: false, content: "" },
    sections: {},
    order: ORDER.slice(),
    metadata: { template: "kakuna", typography: { body: { fontFamily: "georgia" } }, design: { colors: { primary: ACCENT } } },
  };
  for (const id of ORDER) {
    if (id === "summary") continue;
    const def = SECTION_DEFS[id];
    doc.sections[id] = def.single
      ? { title: def.title, hidden: false, content: "" }
      : { title: def.title, hidden: false, items: [] };
  }
  return doc;
}

function adopt(raw) {
  const doc = blankDoc();
  if (!raw || typeof raw !== "object") return doc;
  Object.assign(doc.basics, raw.basics || {});
  const w = raw.basics && raw.basics.website;
  doc.basics.website = (w && typeof w === "object") ? { url: w.url || "", label: w.label || "" } : { url: "", label: "" };
  doc.basics.profiles = Array.isArray(raw.basics && raw.basics.profiles)
    ? raw.basics.profiles.map((p) => ({ label: String(p.label || p.network || "").trim(),
                                        url: String(p.url || (p.website && p.website.url) || "").trim() }))
        .filter((p) => p.url)
    : [];

  const pic = raw.picture;
  if (pic && typeof pic === "object" && typeof pic.url === "string" && pic.url.startsWith("data:image")) {
    doc.picture = { url: pic.url, show: pic.show !== false };
  }

  if (raw.summary) {
    doc.summary.content = stripHtml(raw.summary.content || "");
    doc.summary.hidden = !!raw.summary.hidden;
    if (raw.summary.title) doc.summary.title = raw.summary.title;
  }
  const src = raw.sections || {};
  for (const id of ORDER) {
    if (id === "summary" || !src[id]) continue;
    const s = src[id], def = SECTION_DEFS[id], dst = doc.sections[id];
    dst.hidden = !!s.hidden;
    if (s.title) dst.title = s.title;
    if (def.single) {
      dst.content = stripHtml(s.content || "");
    } else if (Array.isArray(s.items)) {
      dst.items = s.items.map((it) => {
        const out = { id: it.id || uid(), hidden: !!it.hidden };
        for (const f of def.fields) {
          const v = it[f.k];
          out[f.k] = f.type === "tags" && Array.isArray(v) ? v.join(", ")
                   : typeof v === "string" ? stripHtml(v) : "";
        }
        return out;
      });
    }
  }
  /* Respect a saved section order, but APPEND any section the saved copy predates
     (References was added later). Filtering alone would silently drop new sections
     for everyone with an existing localStorage doc — they'd never see the feature. */
  if (Array.isArray(raw.order)) {
    const known = ORDER.filter((id) => raw.order.includes(id))
      .sort((a, b) => raw.order.indexOf(a) - raw.order.indexOf(b));
    for (const id of ORDER) if (!known.includes(id)) known.push(id);
    doc.order = known;
  }

  const fam = raw.metadata && raw.metadata.typography && raw.metadata.typography.body && raw.metadata.typography.body.fontFamily;
  if (FONT_IDS.includes(fam)) doc.metadata.typography.body.fontFamily = fam;
  const tpl = raw.metadata && raw.metadata.template;
  if (TEMPLATE_IDS.includes(tpl)) doc.metadata.template = tpl;
  const col = raw.metadata && raw.metadata.design && raw.metadata.design.colors && raw.metadata.design.colors.primary;
  if (typeof col === "string" && /^#[0-9a-f]{6}$/i.test(col)) doc.metadata.design.colors.primary = col;
  return doc;
}

function stripHtml(s) {
  if (typeof s !== "string") return "";
  if (!/[<&]/.test(s)) return s;
  const t = s.replace(/<\/(li|p|div|h[1-6])>/gi, "\n").replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]*>/g, "");
  const d = document.createElement("textarea");
  d.innerHTML = t;
  return d.value.replace(/\n{3,}/g, "\n\n").trim();
}

let doc = blankDoc();
let activeTailor = null;   // { businessId, name, business, fields } or null
let mode = "resume";       // "resume" | "cover"

/* ══════════════════════════════════════════════════════════════════════
   Tailoring — non-destructive view over the base resume
   ══════════════════════════════════════════════════════════════════════ */

function reorderById(section, orderIds) {
  if (!section || !Array.isArray(section.items) || !Array.isArray(orderIds)) return;
  const byId = new Map(section.items.map((it) => [it.id, it]));
  const out = [];
  for (const id of orderIds) if (byId.has(id)) { out.push(byId.get(id)); byId.delete(id); }
  for (const it of section.items) if (byId.has(it.id)) out.push(it); // keep any not listed
  section.items = out;
}
function reorderLines(text, order) {
  const ls = String(text || "").split("\n");
  const nonEmpty = ls.map((l, i) => [l, i]).filter(([l]) => l.trim());
  if (!Array.isArray(order) || !order.length) return text;
  const picked = order.filter((i) => Number.isInteger(i) && i >= 0 && i < ls.length).map((i) => ls[i]);
  // append any lines the order omitted, preserving original order
  const used = new Set(order);
  for (let i = 0; i < ls.length; i++) if (!used.has(i) && ls[i].trim()) picked.push(ls[i]);
  return picked.join("\n");
}

/* The single source of truth for what renders/exports: base doc, or a tailored
   derivation. Never mutates `doc`. */
function viewDoc() {
  if (!activeTailor) return doc;
  const f = activeTailor.fields || {};
  const v = clone(doc);
  if (f.headline && f.headline.trim()) v.basics.headline = f.headline.trim();
  if (f.summary && f.summary.trim()) v.summary.content = f.summary.trim();
  if (v.sections.experience) reorderById(v.sections.experience, f.experienceOrder);
  if (v.sections.skills) reorderById(v.sections.skills, f.skillsOrder);
  if (f.bulletOrder && v.sections.experience) {
    for (const it of v.sections.experience.items) {
      if (f.bulletOrder[it.id]) it.description = reorderLines(it.description, f.bulletOrder[it.id]);
    }
  }
  return v;
}

function loadTailors() {
  try { return JSON.parse(localStorage.getItem(TAILORS_KEY) || "{}") || {}; } catch (e) { return {}; }
}
function saveTailors(map) {
  try { localStorage.setItem(TAILORS_KEY, JSON.stringify(map)); } catch (e) {}
}
function persistActiveTailor() {
  if (!activeTailor) return;
  const map = loadTailors();
  map[activeTailor.businessId] = {
    name: activeTailor.name, business: activeTailor.business, role: activeTailor.role || "",
    fields: activeTailor.fields, at: Date.now(),
  };
  saveTailors(map);
}

/* ══════════════════════════════════════════════════════════════════════
   Persistence (base resume)
   ══════════════════════════════════════════════════════════════════════ */

let saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(doc));
      const t = new Date();
      document.getElementById("savedAt").textContent =
        "saved " + String(t.getHours()).padStart(2, "0") + ":" + String(t.getMinutes()).padStart(2, "0");
    } catch (e) {
      document.getElementById("savedAt").textContent = "couldn't save";
    }
  }, 400);
}
function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (!raw) return false;
    doc = adopt(JSON.parse(raw));
    return true;
  } catch (e) { return false; }
}

/* ══════════════════════════════════════════════════════════════════════
   Small DOM helpers
   ══════════════════════════════════════════════════════════════════════ */

const el = (tag, cls, txt) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (txt != null) n.textContent = txt;
  return n;
};
function iconBtn(label, title, onClick, opts = {}) {
  const b = el("button", "ico" + (opts.on ? " on" : ""), label);
  b.title = title; b.setAttribute("aria-label", title);
  if (opts.disabled) b.disabled = true;
  b.addEventListener("click", onClick);
  return b;
}
const lines = (s) => (s || "").split("\n").map((l) => l.trim()).filter(Boolean);
const has = (...vals) => vals.some((v) => (v || "").trim());
const join = (sep, ...parts) => parts.filter((p) => (p || "").trim()).join(sep);

/* ══════════════════════════════════════════════════════════════════════
   Editor
   ══════════════════════════════════════════════════════════════════════ */

function fieldNode(def, value, onInput) {
  const wrap = el("div", "field");
  wrap.appendChild(el("label", null, def.label));
  const multiline = def.type === "textarea" || def.type === "lines";
  const input = document.createElement(multiline ? "textarea" : "input");
  if (!multiline) input.type = def.type === "email" ? "email" : def.type === "tel" ? "tel" : "text";
  input.value = value || "";
  input.placeholder = def.ph || "";
  if (def.type === "lines") input.rows = Math.max(3, (value || "").split("\n").length + 1);
  input.addEventListener("input", () => onInput(input.value));
  wrap.appendChild(input);
  if (def.hint) wrap.appendChild(el("div", "hint", def.hint));
  return wrap;
}
function layoutFields(container, defs, get, set) {
  let row = null;
  for (const f of defs) {
    const node = fieldNode(f, get(f.k), (v) => { set(f.k, v); onChange(); });
    if (f.half) {
      if (!row) { row = el("div", "grid2"); container.appendChild(row); }
      row.appendChild(node);
      if (row.children.length === 2) row = null;
    } else { row = null; container.appendChild(node); }
  }
}

const BASICS_FIELDS = [
  { k: "name", label: "Full name", ph: "Lolo Panigrahi" },
  { k: "headline", label: "One-line pitch", ph: "Hospitality & retail · available now" },
  { k: "email", label: "Email", type: "email", ph: "you@example.com", half: true },
  { k: "phone", label: "Phone", type: "tel", ph: "0400 000 000", half: true },
  { k: "location", label: "Suburb", ph: "Bundoora VIC 3083", half: true },
  { k: "websiteUrl", label: "Website (optional)", ph: "yoursite.com", half: true },
];

function photoSection() {
  const sec = el("div", "sec");
  const head = el("div", "sec-head");
  head.appendChild(el("div", "sec-title", "Photo (optional)"));
  sec.appendChild(head);
  const body = el("div", "item");
  const row = el("div", "photo-row");
  const thumb = doc.picture.url
    ? Object.assign(document.createElement("img"), { className: "photo-thumb", src: doc.picture.url })
    : el("div", "photo-thumb empty", "☺");
  row.appendChild(thumb);
  const col = el("div"); col.style.flex = "1 1 auto";
  const pick = el("button", "mini-btn", doc.picture.url ? "Change" : "Upload");
  pick.addEventListener("click", () => document.getElementById("photoFile").click());
  col.appendChild(pick);
  if (doc.picture.url) {
    const show = el("button", "mini-btn", doc.picture.show ? "Hide on resume" : "Show on resume");
    show.style.marginLeft = "6px";
    show.addEventListener("click", () => { doc.picture.show = !doc.picture.show; onChange(); renderForm(); });
    col.appendChild(show);
    const rm = el("button", "mini-btn", "Remove");
    rm.style.marginLeft = "6px";
    rm.addEventListener("click", () => { doc.picture = { url: "", show: false }; onChange(); renderForm(); });
    col.appendChild(rm);
  }
  const note = el("div", "hint", "Most Australian employers don't expect a photo — it's optional. Shown on the resume PDF only, never the Word file.");
  col.appendChild(note);
  row.appendChild(col);
  body.appendChild(row);
  sec.appendChild(body);
  return sec;
}

function profilesSection() {
  const sec = el("div", "sec");
  const head = el("div", "sec-head");
  head.appendChild(el("div", "sec-title", "Links"));
  sec.appendChild(head);
  (doc.basics.profiles || []).forEach((p, i) => {
    const box = el("div", "item");
    const bar = el("div", "item-bar");
    bar.appendChild(iconBtn("✕", "Remove link", () => { doc.basics.profiles.splice(i, 1); onChange(); renderForm(); }));
    box.appendChild(bar);
    layoutFields(box, [
      { k: "label", label: "Label", ph: "LinkedIn", half: true },
      { k: "url", label: "URL", ph: "linkedin.com/in/…", half: true },
    ], (k) => p[k], (k, v) => { p[k] = v; });
    sec.appendChild(box);
  });
  const addRow = el("div", "add-row");
  const add = el("button", "add-btn", "Add a link");
  add.addEventListener("click", () => { doc.basics.profiles.push({ label: "", url: "" }); onChange(); renderForm(); });
  addRow.appendChild(add);
  sec.appendChild(addRow);
  return sec;
}

function coverEditor() {
  const sec = el("div", "sec");
  const head = el("div", "sec-head");
  head.appendChild(el("div", "sec-title", "Cover letter — " + activeTailor.name));
  sec.appendChild(head);
  const body = el("div", "item");
  const wrap = el("div", "field");
  wrap.appendChild(el("label", null, "Edit the letter"));
  const ta = document.createElement("textarea");
  ta.className = "tall";
  ta.value = activeTailor.fields.coverLetter || "";
  ta.addEventListener("input", () => { activeTailor.fields.coverLetter = ta.value; persistActiveTailor(); renderPreview(); });
  wrap.appendChild(ta);
  wrap.appendChild(el("div", "hint", "Truthful and specific to " + activeTailor.name + ". One blank line between paragraphs."));
  body.appendChild(wrap);
  sec.appendChild(body);
  return sec;
}

function renderForm() {
  const root = document.getElementById("form");
  root.textContent = "";

  if (mode === "cover" && activeTailor) { root.appendChild(coverEditor()); return; }

  const bs = el("div", "sec");
  const bh = el("div", "sec-head");
  bh.appendChild(el("div", "sec-title", "Your details"));
  bs.appendChild(bh);
  const bbody = el("div", "item");
  layoutFields(bbody, BASICS_FIELDS,
    (k) => (k === "websiteUrl" ? doc.basics.website.url : doc.basics[k]),
    (k, v) => { if (k === "websiteUrl") doc.basics.website.url = v; else doc.basics[k] = v; });
  bs.appendChild(bbody);
  root.appendChild(bs);

  root.appendChild(profilesSection());
  root.appendChild(photoSection());

  doc.order.forEach((id, idx) => {
    const def = SECTION_DEFS[id];
    const data = id === "summary" ? doc.summary : doc.sections[id];
    const sec = el("div", "sec");
    sec.dataset.hidden = data.hidden ? "1" : "0";

    const head = el("div", "sec-head");
    head.appendChild(el("div", "sec-title", data.title));
    head.appendChild(iconBtn("↑", "Move section up", () => moveSection(idx, -1), { disabled: idx === 0 }));
    head.appendChild(iconBtn("↓", "Move section down", () => moveSection(idx, 1), { disabled: idx === doc.order.length - 1 }));
    head.appendChild(iconBtn(data.hidden ? "✕" : "◉", data.hidden ? "Show this section" : "Hide this section",
      () => { data.hidden = !data.hidden; onChange(); renderForm(); }));
    sec.appendChild(head);

    if (def.single) {
      const body = el("div", "item");
      layoutFields(body, def.fields, () => data.content, (_k, v) => { data.content = v; });
      sec.appendChild(body);
    } else {
      data.items.forEach((item, i) => {
        const box = el("div", "item");
        const bar = el("div", "item-bar");
        bar.appendChild(iconBtn("↑", "Move up", () => moveItem(data.items, i, -1), { disabled: i === 0 }));
        bar.appendChild(iconBtn("↓", "Move down", () => moveItem(data.items, i, 1), { disabled: i === data.items.length - 1 }));
        bar.appendChild(iconBtn("✕", "Remove", () => { data.items.splice(i, 1); onChange(); renderForm(); }));
        box.appendChild(bar);
        layoutFields(box, def.fields, (k) => item[k], (k, v) => { item[k] = v; });
        sec.appendChild(box);
      });
      if (!data.items.length && def.empty) sec.appendChild(el("div", "empty-note", def.empty));
      const addRow = el("div", "add-row");
      const add = el("button", "add-btn", def.add || "Add");
      add.addEventListener("click", () => { data.items.push(blankItem(id)); onChange(); renderForm(); });
      addRow.appendChild(add);
      sec.appendChild(addRow);
    }
    root.appendChild(sec);
  });
}

function moveSection(idx, delta) {
  const to = idx + delta;
  if (to < 0 || to >= doc.order.length) return;
  const [x] = doc.order.splice(idx, 1);
  doc.order.splice(to, 0, x);
  onChange(); renderForm();
}
function moveItem(arr, idx, delta) {
  const to = idx + delta;
  if (to < 0 || to >= arr.length) return;
  const [x] = arr.splice(idx, 1);
  arr.splice(to, 0, x);
  onChange(); renderForm();
}

/* ══════════════════════════════════════════════════════════════════════
   Preview
   ══════════════════════════════════════════════════════════════════════ */

function bulletNode(text) {
  const ls = lines(text);
  if (!ls.length) return null;
  const body = el("div", "rs-body");
  if (ls.length === 1) body.appendChild(el("p", "rs-line", ls[0]));
  else { const ul = document.createElement("ul"); for (const l of ls) ul.appendChild(el("li", null, l)); body.appendChild(ul); }
  return body;
}
function twoUp(title, date) {
  const row = el("div", "rs-row");
  row.appendChild(el("span", "rs-t", title));
  if ((date || "").trim()) row.appendChild(el("span", "rs-d", date));
  return row;
}
const ITEM_RENDER = {
  experience: (it) => {
    const box = el("div", "rs-item");
    box.appendChild(twoUp(it.position || it.company, it.period));
    const sub = join(" · ", it.position ? it.company : "", it.location);
    if (sub) box.appendChild(el("div", "rs-sub", sub));
    const b = bulletNode(it.description); if (b) box.appendChild(b);
    return has(it.position, it.company, it.period, it.description) ? box : null;
  },
  education: (it) => {
    const box = el("div", "rs-item");
    box.appendChild(twoUp(it.school, it.period));
    const sub = join(" · ", it.degree, it.area);
    if (sub) box.appendChild(el("div", "rs-sub", sub));
    const b = bulletNode(it.description); if (b) box.appendChild(b);
    return has(it.school, it.degree, it.area, it.period) ? box : null;
  },
  projects: (it) => {
    const box = el("div", "rs-item");
    box.appendChild(twoUp(it.name, it.period));
    const b = bulletNode(it.description); if (b) box.appendChild(b);
    return has(it.name, it.description) ? box : null;
  },
  skills: (it) => {
    if (!has(it.name, it.keywords)) return null;
    const p = el("p", "rs-skill");
    if ((it.name || "").trim()) p.appendChild(el("b", null, it.name + (it.keywords.trim() ? ": " : "")));
    p.appendChild(document.createTextNode(it.keywords || ""));
    return p;
  },
  languages: (it) => {
    if (!has(it.language, it.fluency)) return null;
    const p = el("p", "rs-skill");
    p.appendChild(el("b", null, it.language + (it.fluency.trim() ? ": " : "")));
    p.appendChild(document.createTextNode(it.fluency || ""));
    return p;
  },
  certifications: (it) => {
    if (!has(it.title, it.issuer, it.date)) return null;
    const box = el("div", "rs-item");
    box.appendChild(twoUp(it.title, it.date));
    if ((it.issuer || "").trim()) box.appendChild(el("div", "rs-sub", it.issuer));
    return box;
  },
  references: (it) => {
    if (!has(it.name, it.role, it.company, it.phone, it.email)) return null;
    const box = el("div", "rs-item");
    box.appendChild(twoUp(it.name, it.phone));
    const sub = join(" · ", it.role, it.company);
    if (sub) box.appendChild(el("div", "rs-sub", sub));
    if ((it.email || "").trim()) {
      const p = el("p", "rs-line");
      p.appendChild(linkNode(it.email, "mailto:" + it.email));
      box.appendChild(p);
    }
    return box;
  },
};

function linkNode(text, href) {
  const a = el("a", null, text);
  a.href = href;
  a.target = "_blank"; a.rel = "noopener";
  return a;
}
function contactNodes(d) {
  const out = [];
  if ((d.basics.email || "").trim()) out.push(linkNode(d.basics.email, "mailto:" + d.basics.email));
  if ((d.basics.phone || "").trim()) out.push(el("span", null, d.basics.phone));
  if ((d.basics.location || "").trim()) out.push(el("span", null, d.basics.location));
  const url = (d.basics.website && d.basics.website.url || "").trim();
  if (url) out.push(linkNode(url.replace(/^https?:\/\//, ""), /^https?:\/\//.test(url) ? url : "https://" + url));
  for (const p of d.basics.profiles || []) {
    const u = (p.url || "").trim();
    if (!u) continue;
    const href = /^https?:\/\//.test(u) ? u : "https://" + u;
    const text = (p.label || "").trim() ? p.label + ": " + u.replace(/^https?:\/\//, "") : u.replace(/^https?:\/\//, "");
    out.push(linkNode(text, href));
  }
  return out;
}

function headerNode(d) {
  const head = el("div", "rs-head");
  if (d.picture && d.picture.url && d.picture.show) {
    const img = document.createElement("img");
    img.className = "rs-photo"; img.src = d.picture.url;
    head.appendChild(img);
  }
  head.appendChild(el("div", "rs-name", d.basics.name || "Your name"));
  if ((d.basics.headline || "").trim()) head.appendChild(el("div", "rs-headline", d.basics.headline));
  const cn = contactNodes(d);
  if (cn.length) { const row = el("div", "rs-contact"); for (const n of cn) row.appendChild(n); head.appendChild(row); }
  return head;
}

function sectionNode(id, d) {
  const def = SECTION_DEFS[id];
  const data = id === "summary" ? d.summary : d.sections[id];
  if (!data || data.hidden) return null;
  let body;
  if (def.single) { body = bulletNode(data.content); if (!body) return null; }
  else {
    const nodes = data.items.filter((it) => !it.hidden).map((it) => ITEM_RENDER[id](it)).filter(Boolean);
    if (!nodes.length) return null;
    body = el("div"); for (const n of nodes) body.appendChild(n);
  }
  const sec = el("section", "rs-sec");
  sec.appendChild(el("h2", null, data.title));
  sec.appendChild(body);
  return sec;
}

function renderResume(sheet, d) {
  const tpl = d.metadata.template || "kakuna";
  const root = el("div", "rs-doc");
  if (tpl === "sidebar") {
    const side = el("div", "rs-sidebar");
    const main = el("div", "rs-main");
    // header split: photo/contact in sidebar, name/headline atop main
    if (d.picture && d.picture.url && d.picture.show) {
      const img = document.createElement("img"); img.className = "rs-photo"; img.src = d.picture.url; side.appendChild(img);
    }
    const nameWrap = el("div", "rs-head");
    nameWrap.appendChild(el("div", "rs-name", d.basics.name || "Your name"));
    if ((d.basics.headline || "").trim()) nameWrap.appendChild(el("div", "rs-headline", d.basics.headline));
    main.appendChild(nameWrap);
    const cn = contactNodes(d);
    if (cn.length) { const row = el("div", "rs-contact"); for (const n of cn) row.appendChild(n); side.appendChild(row); }
    for (const id of d.order) {
      const node = sectionNode(id, d);
      if (!node) continue;
      (SIDEBAR_SECTIONS.has(id) ? side : main).appendChild(node);
    }
    root.appendChild(side); root.appendChild(main);
  } else {
    root.appendChild(headerNode(d));
    for (const id of d.order) { const node = sectionNode(id, d); if (node) root.appendChild(node); }
  }
  sheet.appendChild(root);
}

function renderLetter(sheet, d) {
  const wrap = el("div", "rs-letter");
  const from = el("div", "lt-from");
  from.appendChild(el("div", "lt-name", d.basics.name || "Your name"));
  const contact = [d.basics.email, d.basics.phone, d.basics.location].filter((c) => (c || "").trim()).join("  ·  ");
  if (contact) from.appendChild(el("div", "lt-contact", contact));
  wrap.appendChild(from);

  const today = new Date().toLocaleDateString("en-AU", { day: "numeric", month: "long", year: "numeric" });
  wrap.appendChild(el("div", "lt-date", today));

  const biz = activeTailor.business || {};
  const to = el("div", "lt-to");
  to.appendChild(el("div", null, biz.name || ""));
  if (biz.suburb) to.appendChild(el("div", null, biz.suburb));
  wrap.appendChild(to);

  const text = (activeTailor.fields.coverLetter || "").trim();
  const paras = text ? text.split(/\n\s*\n/) : ["(Generate a tailored letter, or write one here.)"];
  for (const p of paras) {
    const node = el("p");
    /* Single newlines inside a paragraph (e.g. a sign-off) become line breaks. */
    p.split("\n").forEach((ln, i) => {
      if (i) node.appendChild(document.createElement("br"));
      node.appendChild(document.createTextNode(ln));
    });
    wrap.appendChild(node);
  }
  sheet.appendChild(wrap);
}

function renderPreview() {
  const d = viewDoc();
  const sheet = document.getElementById("sheet");
  sheet.textContent = "";
  sheet.dataset.font = d.metadata.typography.body.fontFamily;
  sheet.dataset.template = (mode === "cover") ? "letter" : (d.metadata.template || "kakuna");
  sheet.style.setProperty("--doc-accent", d.metadata.design.colors.primary);
  if (mode === "cover" && activeTailor) renderLetter(sheet, d);
  else renderResume(sheet, d);
  fitPaper();
}

function fitPaper() {
  const frame = document.getElementById("paperFrame");
  const scaler = document.getElementById("scaler");
  const paper = document.getElementById("paper");
  const sheet = document.getElementById("sheet");
  scaler.style.transform = "none";
  scaler.style.height = "";
  const sheetW = sheet.offsetWidth;
  const avail = frame.clientWidth;
  if (!sheetW || !avail) return;
  const scale = Math.min(1, avail / sheetW);
  scaler.style.transform = "scale(" + scale + ")";
  scaler.style.width = sheetW + "px";
  scaler.style.height = paper.offsetHeight * scale + "px";
  paper.querySelectorAll(".pgguide").forEach((n) => n.remove());
  const pageH = mmToPx(297);
  const total = sheet.offsetHeight;
  const pages = Math.max(1, Math.ceil(total / pageH - 0.02));
  for (let i = 1; i < pages; i++) {
    const g = el("div", "pgguide");
    g.style.top = pageH * i + "px";
    g.appendChild(el("span", null, "page " + (i + 1)));
    paper.appendChild(g);
  }
  document.getElementById("pageCount").textContent =
    (mode === "cover") ? "cover letter" : (pages === 1 ? "1 page — nice and tight" : pages + " pages");
}

let mmProbe = null;
function mmToPx(mm) {
  if (!mmProbe) {
    mmProbe = document.createElement("div");
    mmProbe.style.cssText = "position:absolute;visibility:hidden;height:100mm;width:0";
    document.body.appendChild(mmProbe);
  }
  return (mmProbe.offsetHeight / 100) * mm;
}

function onChange() { renderPreview(); save(); }

/* ══════════════════════════════════════════════════════════════════════
   PDF
   ══════════════════════════════════════════════════════════════════════ */

function slug(s) { return (s || "").trim().replace(/[^\w\s-]/g, "").replace(/\s+/g, "_"); }
function fileStem() {
  const name = slug(doc.basics.name) || "Resume";
  const suffix = activeTailor ? "_" + (slug(activeTailor.business && activeTailor.business.name) || "Tailored") : "";
  return name + (mode === "cover" ? "_Cover_Letter" : "_Resume") + suffix;
}

document.getElementById("pdfBtn").addEventListener("click", () => {
  const prev = document.title;
  document.title = fileStem();
  const restore = () => { document.title = prev; window.removeEventListener("afterprint", restore); };
  window.addEventListener("afterprint", restore);
  window.print();
  setTimeout(restore, 8000);
});

/* ══════════════════════════════════════════════════════════════════════
   DOCX — a .docx is a ZIP of OOXML parts, assembled here (stored entries)
   ══════════════════════════════════════════════════════════════════════ */

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let i = 0; i < 256; i++) { let c = i; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[i] = c >>> 0; }
  return t;
})();
function crc32(bytes) { let c = 0xffffffff; for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }

function zip(files) {
  const enc = new TextEncoder();
  const now = new Date();
  const dosTime = ((now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1)) & 0xffff;
  const dosDate = (((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate()) & 0xffff;
  const parts = [], central = [];
  let offset = 0;
  for (const f of files) {
    const name = enc.encode(f.name), data = enc.encode(f.data), crc = crc32(data);
    const local = new DataView(new ArrayBuffer(30));
    local.setUint32(0, 0x04034b50, true); local.setUint16(4, 20, true); local.setUint16(6, 0x0800, true);
    local.setUint16(8, 0, true); local.setUint16(10, dosTime, true); local.setUint16(12, dosDate, true);
    local.setUint32(14, crc, true); local.setUint32(18, data.length, true); local.setUint32(22, data.length, true);
    local.setUint16(26, name.length, true); local.setUint16(28, 0, true);
    parts.push(new Uint8Array(local.buffer), name, data);
    const cd = new DataView(new ArrayBuffer(46));
    cd.setUint32(0, 0x02014b50, true); cd.setUint16(4, 20, true); cd.setUint16(6, 20, true); cd.setUint16(8, 0x0800, true);
    cd.setUint16(10, 0, true); cd.setUint16(12, dosTime, true); cd.setUint16(14, dosDate, true);
    cd.setUint32(16, crc, true); cd.setUint32(20, data.length, true); cd.setUint32(24, data.length, true);
    cd.setUint16(28, name.length, true); cd.setUint32(42, offset, true);
    central.push(new Uint8Array(cd.buffer), name);
    offset += 30 + name.length + data.length;
  }
  const cdStart = offset;
  let cdSize = 0; for (const c of central) cdSize += c.length;
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, files.length, true); end.setUint16(10, files.length, true);
  end.setUint32(12, cdSize, true); end.setUint32(16, cdStart, true);
  return new Blob([...parts, ...central, new Uint8Array(end.buffer)],
    { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
}

const xmlEsc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");

const MARGIN_X = 794, MARGIN_Y = 680;
const CONTENT_W = 11906 - MARGIN_X * 2;

function run(text, o = {}) {
  const rpr = [];
  if (o.b) rpr.push("<w:b/>");
  if (o.i) rpr.push("<w:i/>");
  if (o.sz) rpr.push('<w:sz w:val="' + o.sz + '"/><w:szCs w:val="' + o.sz + '"/>');
  if (o.color) rpr.push('<w:color w:val="' + o.color + '"/>');
  if (o.caps) rpr.push("<w:caps/>");
  if (o.spacing) rpr.push('<w:spacing w:val="' + o.spacing + '"/>');
  return "<w:r>" + (rpr.length ? "<w:rPr>" + rpr.join("") + "</w:rPr>" : "") +
    '<w:t xml:space="preserve">' + xmlEsc(text) + "</w:t></w:r>";
}
function para(runs, o = {}) {
  const ppr = [];
  if (o.align) ppr.push('<w:jc w:val="' + o.align + '"/>');
  /* `rule` draws a full-width hairline; `barW` (twips) draws a SHORT accent bar by
     indenting the paragraph from the right — a paragraph border spans the content
     box, so narrowing the box narrows the border. That is how the Underline
     template's stub rule is reproduced without a table. */
  if (o.barW) ppr.push('<w:ind w:right="' + Math.max(0, CONTENT_W - o.barW) + '"/>');
  else if (o.bullet) ppr.push('<w:ind w:left="284" w:hanging="284"/>');
  if (o.rule) ppr.push('<w:pBdr><w:bottom w:val="single" w:sz="' + (o.ruleSz || 6) +
    '" w:space="' + (o.ruleGap == null ? 2 : o.ruleGap) + '" w:color="' + o.rule + '"/></w:pBdr>');
  if (o.shd) ppr.push('<w:shd w:val="clear" w:color="auto" w:fill="' + o.shd + '"/>');
  if (o.tabRight) ppr.push('<w:tabs><w:tab w:val="right" w:pos="' + CONTENT_W + '"/></w:tabs>');
  const sp = [];
  if (o.before != null) sp.push('w:before="' + o.before + '"');
  if (o.after != null) sp.push('w:after="' + o.after + '"');
  if (sp.length) ppr.push("<w:spacing " + sp.join(" ") + "/>");
  if (o.markSz) ppr.push('<w:rPr><w:sz w:val="' + o.markSz + '"/><w:szCs w:val="' + o.markSz + '"/></w:rPr>');
  return "<w:p>" + (ppr.length ? "<w:pPr>" + ppr.join("") + "</w:pPr>" : "") + runs + "</w:p>";
}
const bullet = (text, sz) => para(run("•\t" + text, { sz }), { bullet: true, after: 20 });
const B = 21; // 10.5pt body, half-points

/* ── Word styling per template ───────────────────────────────────────────────
   The Word export stays SINGLE-COLUMN for every template (two-column .docx
   parses badly in applicant tracking systems), but it now mirrors the template
   she actually picked and previewed: alignment, heading treatment, type sizes
   and the banner's accent band. `sidebar` has no single-column equivalent, so it
   maps to the left-aligned look — the closest honest match. */
const DOCX_TEMPLATE = {
  kakuna:    { head: "center", sec: "center", rule: true },
  onyx:      { head: "left",   sec: "left",   rule: true },
  underline: { head: "left",   sec: "left",   rule: false, bar: 680 },
  minimal:   { head: "left",   sec: "left",   rule: false, track: 60, before: 260, after: 120 },
  banner:    { head: "center", sec: "center", rule: true, band: true },
  compact:   { head: "left",   sec: "left",   rule: true, body: 19, name: 34, secSz: 20,
               before: 140, after: 60, itemGap: 90, tight: true },
  sidebar:   { head: "left",   sec: "left",   rule: true },
};
function docxSpec(id) {
  const t = DOCX_TEMPLATE[id] || DOCX_TEMPLATE.kakuna;
  return {
    head: t.head, sec: t.sec, rule: t.rule !== false, bar: t.bar || 0, band: !!t.band,
    track: t.track || 22, body: t.body || B, name: t.name || 40, secSz: t.secSz || 22,
    before: t.before == null ? 200 : t.before, after: t.after == null ? 100 : t.after,
    itemGap: t.itemGap || 120, tight: !!t.tight,
  };
}

/* Resume DOCX — always single-column and ATS-clean (no photo, no columns), but
   styled to match the template selected in the toolbar. See DOCX_TEMPLATE. */
function buildDocxBody() {
  const d = viewDoc();
  const accent = d.metadata.design.colors.primary.replace("#", "").toUpperCase();
  const t = docxSpec(d.metadata.template || "kakuna");
  const out = [];

  /* Header. The Banner template paints an accent band behind it: paragraph
     shading plus white text, with zero-height shaded spacers top and bottom so
     the block reads as one band rather than three striped lines. */
  const bandPad = (o) => para("", { shd: accent, align: t.head, after: 0, before: 0, markSz: 8, ...o });
  const hOpt = (o) => (t.band ? { align: t.head, shd: accent, ...o } : { align: t.head, ...o });
  const hInk = t.band ? "FFFFFF" : null;

  if (t.band) out.push(bandPad({ before: 60 }));
  out.push(para(run(d.basics.name || "Your name", { b: true, sz: t.name, color: hInk }),
    hOpt({ after: t.band ? 0 : 20 })));
  if ((d.basics.headline || "").trim()) {
    out.push(para(run(d.basics.headline, { sz: t.body, color: hInk }), hOpt({ after: t.band ? 0 : 20 })));
  }
  const contacts = [d.basics.email, d.basics.phone, d.basics.location];
  if (d.basics.website && d.basics.website.url) contacts.push(d.basics.website.url);
  for (const p of d.basics.profiles || []) if ((p.url || "").trim()) contacts.push((p.label ? p.label + ": " : "") + p.url);
  const cc = contacts.filter((c) => (c || "").trim());
  if (cc.length) out.push(para(run(cc.join("   ·   "), { sz: 19, color: hInk }), hOpt({ after: t.band ? 0 : 40 })));
  if (t.band) { out.push(bandPad({ after: 0, markSz: 8 })); out.push(para("", { after: 0, markSz: 8 })); }

  /* Section heading. Underline swaps the full-width rule for a short accent bar;
     Minimal drops the rule entirely and widens the letter tracking instead. */
  const heading = (txt) => {
    out.push(para(run(txt, { b: true, sz: t.secSz, color: accent, caps: true, spacing: t.track }),
      { align: t.sec, rule: t.rule ? accent : null, before: t.before, after: t.bar ? 40 : t.after }));
    if (t.bar) out.push(para("", { barW: t.bar, rule: accent, ruleSz: 12, ruleGap: 0, after: t.after, markSz: 8 }));
  };
  const titleDate = (title, date, gap) => {
    const o = { after: 0, before: gap ? t.itemGap : 0 };
    if (!(date || "").trim()) return para(run(title, { b: true, sz: t.body }), o);
    o.tabRight = true;
    return para(run(title, { b: true, sz: t.body }) + "<w:r><w:tab/></w:r>" + run(date, { sz: 19 }), o);
  };
  const sub = (txt) => out.push(para(run(txt, { i: true, sz: t.tight ? 19 : 20 }), { after: t.tight ? 0 : 20 }));
  const bullets = (text) => { for (const l of lines(text)) out.push(bullet(l, t.body)); };

  for (const id of d.order) {
    const def = SECTION_DEFS[id];
    const data = id === "summary" ? d.summary : d.sections[id];
    if (data.hidden) continue;
    if (def.single) {
      const ls = lines(data.content);
      if (!ls.length) continue;
      heading(data.title);
      if (ls.length === 1) out.push(para(run(ls[0], { sz: t.body }), { after: 40 }));
      else bullets(data.content);
      continue;
    }
    const useful = data.items.filter((it) => !it.hidden && Object.entries(it)
      .some(([k, v]) => k !== "id" && k !== "hidden" && (v || "").trim()));
    if (!useful.length) continue;
    heading(data.title);
    useful.forEach((it, i) => {
      if (id === "experience") {
        out.push(titleDate(it.position || it.company, it.period, i));
        const s = join(" · ", it.position ? it.company : "", it.location); if (s) sub(s);
        bullets(it.description);
      } else if (id === "education") {
        out.push(titleDate(it.school, it.period, i));
        const s = join(" · ", it.degree, it.area); if (s) sub(s);
        bullets(it.description);
      } else if (id === "projects") {
        out.push(titleDate(it.name, it.period, i)); bullets(it.description);
      } else if (id === "certifications") {
        out.push(titleDate(it.title, it.date, i)); if ((it.issuer || "").trim()) sub(it.issuer);
      } else if (id === "references") {
        /* Name (+ phone right-aligned), then role · where, then email — the same
           three lines the preview draws, so the two exports agree. */
        out.push(titleDate(it.name, it.phone, i));
        const s = join(" · ", it.role, it.company); if (s) sub(s);
        if ((it.email || "").trim()) out.push(para(run(it.email, { sz: 19 }), { after: 20 }));
      } else if (id === "skills") {
        out.push(para(run(it.name + (it.keywords.trim() ? ": " : ""), { b: true, sz: t.body }) + run(it.keywords, { sz: t.body }), { after: 30 }));
      } else if (id === "languages") {
        out.push(para(run(it.language + (it.fluency.trim() ? ": " : ""), { b: true, sz: t.body }) + run(it.fluency, { sz: t.body }), { after: 30 }));
      }
    });
  }
  out.push(sectPr());
  return out.join("");
}

function buildCoverLetterBody() {
  const d = viewDoc();
  const out = [];
  out.push(para(run(d.basics.name || "Your name", { b: true, sz: 30 }), { after: 20 }));
  const contact = [d.basics.email, d.basics.phone, d.basics.location].filter((c) => (c || "").trim()).join("   ·   ");
  if (contact) out.push(para(run(contact, { sz: 19 }), { after: 120 }));
  const today = new Date().toLocaleDateString("en-AU", { day: "numeric", month: "long", year: "numeric" });
  out.push(para(run(today, { sz: B }), { after: 120 }));
  const biz = (activeTailor && activeTailor.business) || {};
  if (biz.name) out.push(para(run(biz.name, { sz: B }), { after: 0 }));
  if (biz.suburb) out.push(para(run(biz.suburb, { sz: B }), { after: 120 }));
  const text = ((activeTailor && activeTailor.fields.coverLetter) || "").trim();
  const paras = text ? text.split(/\n\s*\n/) : [];
  for (const p of paras) out.push(para(run(p.replace(/\n/g, " "), { sz: B }), { after: 120 }));
  out.push(sectPr());
  return out.join("");
}

function sectPr() {
  return '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>' +
    '<w:pgMar w:top="' + MARGIN_Y + '" w:right="' + MARGIN_X + '" w:bottom="' + MARGIN_Y +
    '" w:left="' + MARGIN_X + '" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr>';
}

function docxPackage(bodyXml) {
  const font = DOCX_FONTS[viewDoc().metadata.typography.body.fontFamily] || "Georgia";
  const head = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n';
  const W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"';
  return zip([
    { name: "[Content_Types].xml", data: head +
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
      '<Default Extension="xml" ContentType="application/xml"/>' +
      '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>' +
      '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>' +
      "</Types>" },
    { name: "_rels/.rels", data: head +
      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>' +
      "</Relationships>" },
    { name: "word/_rels/document.xml.rels", data: head +
      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' +
      "</Relationships>" },
    { name: "word/styles.xml", data: head +
      "<w:styles " + W + "><w:docDefaults><w:rPrDefault><w:rPr>" +
      '<w:rFonts w:ascii="' + font + '" w:hAnsi="' + font + '" w:cs="' + font + '"/>' +
      '<w:sz w:val="21"/><w:szCs w:val="21"/></w:rPr></w:rPrDefault>' +
      '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault>' +
      "</w:docDefaults>" +
      '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>' +
      "</w:styles>" },
    { name: "word/document.xml", data: head + "<w:document " + W + "><w:body>" + bodyXml + "</w:body></w:document>" },
  ]);
}

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

document.getElementById("docxBtn").addEventListener("click", () => {
  const body = (mode === "cover" && activeTailor) ? buildCoverLetterBody() : buildDocxBody();
  download(docxPackage(body), fileStem() + ".docx");
});

/* ══════════════════════════════════════════════════════════════════════
   Backup / restore
   ══════════════════════════════════════════════════════════════════════ */

document.getElementById("saveJsonBtn").addEventListener("click", () => {
  download(new Blob([JSON.stringify(doc, null, 2)], { type: "application/json" }), (slug(doc.basics.name) || "Resume") + "_Resume.json");
});
document.getElementById("loadJsonBtn").addEventListener("click", () => document.getElementById("jsonFile").click());
document.getElementById("jsonFile").addEventListener("change", (e) => {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  const r = new FileReader();
  r.onload = () => {
    try { doc = adopt(JSON.parse(r.result)); clearTailor(); syncControls(); renderForm(); onChange(); }
    catch (err) { alert("That file didn't look like a resume backup."); }
  };
  r.readAsText(file);
  e.target.value = "";
});

document.getElementById("photoFile").addEventListener("change", (e) => {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const img = new Image();
    img.onload = () => {
      const max = 400;
      const scale = Math.min(1, max / Math.max(img.width, img.height));
      const w = Math.round(img.width * scale), h = Math.round(img.height * scale);
      const cv = document.createElement("canvas");
      cv.width = w; cv.height = h;
      cv.getContext("2d").drawImage(img, 0, 0, w, h);
      doc.picture = { url: cv.toDataURL("image/jpeg", 0.82), show: true };
      onChange(); renderForm();
    };
    img.onerror = () => alert("Couldn't read that image.");
    img.src = reader.result;
  };
  reader.readAsDataURL(file);
  e.target.value = "";
});

/* ══════════════════════════════════════════════════════════════════════
   Baseline
   ══════════════════════════════════════════════════════════════════════ */

function stamp(s) { let h = 5381; for (let i = 0; i < s.length; i++) h = (((h << 5) + h) ^ s.charCodeAt(i)) >>> 0; return h.toString(36); }
function applyBaseline(raw, sig) {
  doc = adopt(raw);
  try { localStorage.setItem(SEEN_KEY, sig); } catch (e) {}
  clearTailor(); hideNotice(); syncControls(); renderForm(); onChange();
}
function hideNotice() { document.getElementById("notice").hidden = true; }
function showNotice(message, actionLabel, onAction, onDismiss, busy) {
  const n = document.getElementById("notice");
  n.className = "notice" + (busy ? " busy" : "");
  n.textContent = "";
  n.appendChild(el("span", null, message));
  if (actionLabel) { const go = el("button", "clear-btn", actionLabel); go.addEventListener("click", onAction); n.appendChild(go); }
  if (!busy) { const no = el("button", "clear-btn", "Dismiss"); no.addEventListener("click", () => { hideNotice(); if (onDismiss) onDismiss(); }); n.appendChild(no); }
  n.hidden = false;
}
async function fetchBaseline() {
  const res = await fetch(BASELINE_URL, { cache: "no-store" });
  if (!res.ok) throw new Error("HTTP " + res.status);
  const raw = await res.json();
  return { raw, sig: stamp(JSON.stringify(raw)) };
}
async function syncBaseline(hadLocal) {
  let got;
  try { got = await fetchBaseline(); } catch (e) { return; }
  if (!hadLocal) { applyBaseline(got.raw, got.sig); return; }
  let seen = null;
  try { seen = localStorage.getItem(SEEN_KEY); } catch (e) {}
  if (seen === got.sig) return;
  showNotice("The saved baseline was updated.", "Load it (replaces your edits)",
    () => { if (confirm("Replace everything here with the baseline resume?")) applyBaseline(got.raw, got.sig); },
    () => { try { localStorage.setItem(SEEN_KEY, got.sig); } catch (e) {} });
}
document.getElementById("baselineBtn").addEventListener("click", async () => {
  let got;
  try { got = await fetchBaseline(); } catch (e) { showNotice("Couldn't reach the baseline file — you may be offline."); return; }
  if (confirm("Replace everything here with the baseline resume?")) applyBaseline(got.raw, got.sig);
});

/* ══════════════════════════════════════════════════════════════════════
   Tailoring UI
   ══════════════════════════════════════════════════════════════════════ */

/* The tailoring controls live in a PERMANENT panel at the top of the editor
   column (#tailorPanel). They used to be a notice bar that disappeared on
   Dismiss and was overwritten by any other message, so re-tailoring meant
   reloading the deep link. The panel is always there, always aimed at a
   business, and "Regenerate" re-runs against the live form contents. */
function bizById(id) { return BUSINESSES.find((b) => b.id === id) || null; }

function setModeToggle() {
  const mt = document.getElementById("modeToggle");
  mt.hidden = !activeTailor;
  if (!activeTailor && mode === "cover") mode = "resume";
  mt.querySelectorAll(".mode-btn").forEach((b) => (b.dataset.active = b.dataset.mode === mode ? "1" : "0"));
}
function clearTailor() {
  activeTailor = null; mode = "resume";
  setModeToggle(); syncTailorPanel();
}
const tailorLabel = (name, role) => name + ((role || "").trim() ? " · " + role : "");

function activateTailor(id, entry) {
  const biz = (entry && entry.business) || bizById(id);
  activeTailor = { businessId: id, name: (biz && biz.name) || "Business", business: biz, role: entry.role || "", fields: entry.fields };
  setModeToggle();
  renderForm(); renderPreview(); syncTailorPanel();
}

function buildRoleSelect(grp) {
  const sel = el("select", "mini");
  sel.style.maxWidth = "100%";
  sel.style.width = "100%";
  for (const [label, roles] of ROLE_GROUPS) {
    const og = document.createElement("optgroup");
    og.label = label;
    for (const [role, pay] of roles) {
      const o = document.createElement("option");
      o.value = role;
      o.textContent = pay ? role + "  (" + pay + ")" : role;
      og.appendChild(o);
    }
    sel.appendChild(og);
  }
  const cog = document.createElement("optgroup"); cog.label = "—";
  const co = document.createElement("option"); co.value = "__custom__"; co.textContent = "✎ Type my own…";
  cog.appendChild(co); sel.appendChild(cog);
  const def = DEFAULT_ROLE_BY_GRP[grp];
  if (def) sel.value = def;
  sel.addEventListener("change", () => {
    if (sel.value !== "__custom__") return;
    const t = (prompt("What role?") || "").trim();
    if (t) {
      const o = document.createElement("option"); o.value = t; o.textContent = t; o.selected = true;
      sel.insertBefore(o, sel.firstChild); sel.value = t;
    } else { sel.value = def || sel.options[0].value; }
  });
  return sel;
}

/* What actually gets POSTed. The model may only reorder experience/skills and
   rewrite the headline/summary, so two things are stripped before the resume
   leaves the device:
     · references — a referee's phone and email are a THIRD PARTY's contact
       details, and they never consented to an AI vendor holding them;
     · picture    — a base64 photo the model cannot read anyway, and easily the
       largest thing in the payload.
   Neither is used for tailoring, so removing them costs nothing. */
function tailorPayload() {
  const p = clone(doc);
  if (p.sections) delete p.sections.references;
  p.order = (p.order || []).filter((id) => id !== "references");
  p.picture = { url: "", show: false };
  return p;
}

/* `force` skips the saved-version shortcut and spends a fresh API call. That is
   what "Regenerate" does, and it is the whole point of the panel: the payload is
   built from `doc`, which the form mutates synchronously on every keystroke, so
   a regenerate always reflects the fields she just added on the left. */
async function tailorFor(id, role, force) {
  const biz = bizById(id);
  if (!biz || tailorBusy) return;
  if (!WORKER_URL) { syncTailorPanel(); return; }
  if (!force) {
    const saved = loadTailors()[id];
    if (saved && saved.fields) { activateTailor(id, saved); return; }
  }

  hideNotice();
  tailorBusy = true; syncTailorPanel();
  try {
    const res = await fetch(WORKER_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume: tailorPayload(), business: biz, role: role || "" }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const fields = await res.json();
    if (fields.error) throw new Error(fields.error);
    activeTailor = { businessId: id, name: biz.name, business: biz, role: role || "", fields };
    persistActiveTailor();
    setModeToggle();
    renderForm(); renderPreview();
  } catch (e) {
    showNotice("Couldn't tailor just now (" + String(e.message || e).slice(0, 60) + "). Your resume is unchanged.");
  } finally {
    tailorBusy = false; syncTailorPanel();
  }
}

/* ── the panel ───────────────────────────────────────────────────────────
   Built once at boot; syncTailorPanel() then updates labels/state in place so
   typing in the business search never loses focus. `tailorPick` (what the panel
   is aimed at) is deliberately separate from `activeTailor` (what is applied) —
   she can line up the next business without dropping the current tailoring. */
let tailorPick = null;
let tailorBusy = false;
let savedOpen = false;
const TP = {};

function currentRole() {
  const v = TP.role ? TP.role.value : "";
  return v === "__custom__" ? "" : v;
}
function selectRole(sel, role) {
  if (!sel || !(role || "").trim()) return;
  if (![...sel.options].some((o) => o.value === role)) {
    const o = document.createElement("option");
    o.value = role; o.textContent = role;
    sel.insertBefore(o, sel.firstChild);
  }
  sel.value = role;
}
function setRoleSelect(grp, preset) {
  TP.roleSlot.textContent = "";
  TP.role = buildRoleSelect(grp);
  TP.roleSlot.appendChild(TP.role);
  selectRole(TP.role, preset);
}

function pickBusiness(b) {
  tailorPick = b;
  TP.input.value = b.name;
  TP.hits.hidden = true;
  const saved = loadTailors()[b.id];
  setRoleSelect(b.grp, saved && saved.role);
  syncTailorPanel();
}

function renderHits() {
  const q = TP.input.value.trim().toLowerCase();
  TP.hits.textContent = "";
  if (!q || (tailorPick && tailorPick.name.toLowerCase() === q)) { TP.hits.hidden = true; return; }
  const hits = [];
  for (const b of BUSINESSES) {
    if (b.name.toLowerCase().includes(q)) hits.push(b);
    if (hits.length >= 8) break;
  }
  if (!hits.length) {
    TP.hits.appendChild(el("div", "tailor-hint", "Nothing in the directory matches that."));
    TP.hits.hidden = false;
    return;
  }
  for (const b of hits) {
    const btn = el("button", "biz-hit");
    btn.appendChild(el("span", null, b.name));
    const sub = join(" · ", b.cat, b.suburb);
    if (sub) btn.appendChild(el("span", "sub", sub));
    btn.addEventListener("click", () => pickBusiness(b));
    TP.hits.appendChild(btn);
  }
  TP.hits.hidden = false;
}

function renderSavedList() {
  TP.savedWrap.textContent = "";
  if (!savedOpen) { TP.savedWrap.hidden = true; return; }
  const map = loadTailors();
  const ids = Object.keys(map).sort((a, z) => map[z].at - map[a].at);
  if (!ids.length) {
    TP.savedWrap.appendChild(el("div", "tailor-hint", "No saved versions yet — tailor for a business to make one."));
    TP.savedWrap.hidden = false;
    return;
  }
  for (const id of ids) {
    const entry = map[id];
    const row = el("div", "saved-row");
    if (activeTailor && activeTailor.businessId === id) row.dataset.active = "1";
    row.appendChild(el("div", "nm", tailorLabel((entry.business && entry.business.name) || entry.name || "Business", entry.role)));
    row.appendChild(el("div", "dt", new Date(entry.at).toLocaleDateString("en-AU", { day: "numeric", month: "short" })));
    const open = el("button", "mini-btn", "Open");
    open.addEventListener("click", () => {
      const biz = entry.business || bizById(id);
      if (biz) pickBusiness(biz);
      activateTailor(id, entry);
    });
    row.appendChild(open);
    const del = el("button", "mini-btn", "✕");
    del.title = "Delete this saved version";
    del.addEventListener("click", () => {
      const m = loadTailors(); delete m[id]; saveTailors(m);
      if (activeTailor && activeTailor.businessId === id) { clearTailor(); renderForm(); renderPreview(); }
      syncTailorPanel();
    });
    row.appendChild(del);
    TP.savedWrap.appendChild(row);
  }
  TP.savedWrap.hidden = false;
}

function syncTailorPanel() {
  if (!TP.status) return;                     // panel not built yet (early boot)
  const map = loadTailors();
  const count = Object.keys(map).length;
  const savedForPick = tailorPick ? map[tailorPick.id] : null;
  const isActivePick = !!(tailorPick && activeTailor && activeTailor.businessId === tailorPick.id);

  TP.savedBtn.textContent = count ? "Saved · " + count : "Saved";

  TP.status.textContent = "";
  if (tailorBusy) {
    TP.status.dataset.idle = "0";
    TP.status.appendChild(el("span", "tailor-spin"));
    TP.status.appendChild(document.createTextNode(
      "  Tailoring for " + tailorLabel(tailorPick ? tailorPick.name : "…", currentRole()) + " — 15–30 seconds."));
  } else if (activeTailor) {
    TP.status.dataset.idle = "0";
    TP.status.appendChild(el("b", null, "Applied: " + tailorLabel(activeTailor.name, activeTailor.role)));
    TP.status.appendChild(el("div", null, "Your saved resume is untouched — Clear removes this layer."));
  } else {
    TP.status.dataset.idle = "1";
    TP.status.textContent = WORKER_URL
      ? "Showing your base resume. Pick a business to tailor it."
      : "Tailoring isn't set up yet — the AI helper still needs deploying.";
  }

  TP.go.disabled = !WORKER_URL || !tailorPick || tailorBusy;
  TP.go.textContent = tailorBusy ? "Working…" : (savedForPick ? "Regenerate" : "Tailor now");
  TP.go.title = savedForPick
    ? "Spend a fresh call, using what's in the form right now"
    : "Tailor this resume for the selected business";

  TP.open.hidden = !(savedForPick && !isActivePick) || tailorBusy;
  TP.clear.disabled = !activeTailor || tailorBusy;

  renderSavedList();
}

function initTailorPanel() {
  const root = document.getElementById("tailorPanel");
  root.textContent = "";
  const sec = el("div", "sec");

  const head = el("div", "sec-head");
  head.appendChild(el("div", "sec-title", "Tailor"));
  TP.savedBtn = el("button", "mini-btn", "Saved");
  TP.savedBtn.addEventListener("click", () => { savedOpen = !savedOpen; syncTailorPanel(); });
  head.appendChild(TP.savedBtn);
  sec.appendChild(head);

  const body = el("div", "tailor-body");
  TP.status = el("div", "tailor-status");
  body.appendChild(TP.status);
  TP.savedWrap = el("div", "saved-list");
  TP.savedWrap.hidden = true;
  body.appendChild(TP.savedWrap);

  const search = el("div", "biz-search");
  const bf = el("div", "field");
  bf.appendChild(el("label", null, "Business"));
  TP.input = document.createElement("input");
  TP.input.type = "text";
  TP.input.placeholder = "Search the directory…";
  TP.input.addEventListener("input", () => { tailorPick = null; renderHits(); syncTailorPanel(); });
  TP.input.addEventListener("focus", renderHits);
  bf.appendChild(TP.input);
  search.appendChild(bf);
  TP.hits = el("div", "biz-results");
  TP.hits.hidden = true;
  search.appendChild(TP.hits);
  body.appendChild(search);

  const rf = el("div", "field");
  rf.appendChild(el("label", null, "Role you're after"));
  TP.roleSlot = el("div");
  rf.appendChild(TP.roleSlot);
  body.appendChild(rf);
  setRoleSelect(null);

  const row = el("div", "tailor-row");
  TP.go = el("button", "sheet-btn", "Tailor now");
  TP.go.addEventListener("click", () => {
    if (tailorPick) tailorFor(tailorPick.id, currentRole(), true);
  });
  row.appendChild(TP.go);
  TP.open = el("button", "toggle-btn", "Open saved");
  TP.open.title = "Re-apply the saved version without spending another call";
  TP.open.addEventListener("click", () => {
    if (!tailorPick) return;
    const entry = loadTailors()[tailorPick.id];
    if (entry && entry.fields) activateTailor(tailorPick.id, entry);
  });
  row.appendChild(TP.open);
  TP.clear = el("button", "toggle-btn", "Clear");
  TP.clear.addEventListener("click", () => { clearTailor(); renderForm(); renderPreview(); });
  row.appendChild(TP.clear);
  body.appendChild(row);

  body.appendChild(el("div", "tailor-hint",
    "Regenerate reads the form as it is right now — add or edit anything on the left first, then run it again."));

  sec.appendChild(body);
  root.appendChild(sec);
  syncTailorPanel();
}

/* ══════════════════════════════════════════════════════════════════════
   Theming controls
   ══════════════════════════════════════════════════════════════════════ */

document.getElementById("templateSel").addEventListener("change", (e) => { doc.metadata.template = e.target.value; onChange(); });
document.getElementById("fontSel").addEventListener("change", (e) => { doc.metadata.typography.body.fontFamily = e.target.value; onChange(); });
document.getElementById("accentSel").addEventListener("change", (e) => {
  if (e.target.value === "custom") { document.getElementById("accentPick").click(); return; }
  doc.metadata.design.colors.primary = e.target.value;
  document.getElementById("accentPick").value = e.target.value; // keep the swatch in step
  onChange();
});
document.getElementById("accentPick").addEventListener("input", (e) => {
  doc.metadata.design.colors.primary = e.target.value;
  document.getElementById("accentSel").value = presetColour(e.target.value) ? e.target.value : "custom";
  onChange();
});
function presetColour(hex) {
  return [...document.getElementById("accentSel").options].some((o) => o.value.toLowerCase() === (hex || "").toLowerCase());
}

document.querySelectorAll(".view-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    document.body.dataset.pane = btn.dataset.pane;
    document.querySelectorAll(".view-btn").forEach((b) => (b.dataset.active = b === btn ? "1" : "0"));
    if (btn.dataset.pane === "preview") requestAnimationFrame(fitPaper);
  }));
document.querySelectorAll(".mode-btn").forEach((btn) =>
  btn.addEventListener("click", () => {
    if (btn.dataset.mode === "cover" && !activeTailor) return;
    mode = btn.dataset.mode;
    setModeToggle();
    renderForm(); renderPreview();
  }));

function syncControls() {
  document.getElementById("templateSel").value = doc.metadata.template || "kakuna";
  document.getElementById("fontSel").value = doc.metadata.typography.body.fontFamily;
  const col = doc.metadata.design.colors.primary;
  document.getElementById("accentPick").value = /^#[0-9a-f]{6}$/i.test(col) ? col : ACCENT;
  document.getElementById("accentSel").value = presetColour(col) ? col : "custom";
}

/* ══════════════════════════════════════════════════════════════════════
   Boot
   ══════════════════════════════════════════════════════════════════════ */

document.body.dataset.pane = "edit";
if (window.ResizeObserver) new ResizeObserver(() => fitPaper()).observe(document.getElementById("paperFrame"));
window.addEventListener("resize", fitPaper);

const hadLocal = load();
syncControls();
setModeToggle();
initTailorPanel();
renderForm();
renderPreview();
document.getElementById("savedAt").textContent = "";

/* Deep link from a business card: resume.html?biz=<place_id> aims the panel at
   that business (and re-applies a saved version if there is one). Runs AFTER the
   baseline sync settles so a fresh device has her real resume to tailor from. */
function handleBizParam() {
  const id = new URLSearchParams(location.search).get("biz");
  if (!id) return;
  const biz = bizById(id);
  if (!biz) return;
  pickBusiness(biz);
  const saved = loadTailors()[id];
  if (saved && saved.fields) activateTailor(id, saved);
}
syncBaseline(hadLocal).then(handleBizParam, handleBizParam);

if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => {});
</script>
"""

out = BASE / "resume.html"
html = (HTML
        .replace("__ACCENT__", ACCENT_HEX)
        .replace("__FONT_CSS__", FONT_CSS)
        .replace("__FONT_OPTIONS__", FONT_OPTIONS)
        .replace("__COLOUR_OPTIONS__", COLOUR_OPTIONS)
        .replace("__TEMPLATE_OPTIONS__", TEMPLATE_OPTIONS)
        .replace("__WORKER_URL__", TAILOR_WORKER_URL)
        .replace("__BUSINESSES__", BUSINESSES_JSON)
        .replace("__ROLE_GROUPS__", json.dumps(ROLE_GROUPS).replace("</", "<\\/"))
        .replace("__DEFAULT_ROLE_BY_GRP__", json.dumps(DEFAULT_ROLE_BY_GRP))
        .replace("__FONT_IDS__", json.dumps(FONT_IDS))
        .replace("__TEMPLATE_IDS__", json.dumps(TEMPLATE_IDS))
        .replace("__DOCX_FONTS__", json.dumps(DOCX_FONTS)))
out.write_text(html, encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)  ·  worker={'set' if TAILOR_WORKER_URL else 'UNSET'}  ·  {len(BUSINESSES)} businesses")
