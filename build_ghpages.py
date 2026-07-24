#!/usr/bin/env python3
"""
Build index.html for GitHub Pages — same directory/list UI as build_site.py,
but the Map tab uses the real Google Maps JavaScript SDK (street basemap +
live TransitLayer for tram/train/bus routes) instead of the Artifact-safe
custom SVG scatter plot, since a real website isn't limited by Artifact CSP.

Requires env var GMAPS_JS_KEY (a Maps JavaScript API key restricted to that
API and to the github.io referrer — see README).

Usage:
    export GMAPS_JS_KEY=your_key_here
    python3 build_ghpages.py
"""

import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).parent
DATA = json.loads((BASE / "data" / "businesses.json").read_text())

GMAPS_KEY = os.environ.get("GMAPS_JS_KEY")
if not GMAPS_KEY:
    sys.exit("ERROR: set GMAPS_JS_KEY environment variable first (Maps JavaScript API key).")

GROUP_OF = {
    "Cafe": "Hospo",
    "Restaurant/Takeaway": "Hospo",
    "Fast Food": "Hospo",
    "Supermarket": "Grocery",
    "Retail": "Retail",
    "Retail (general)": "Retail",
    "Medical Clinic": "Health",
    "Hospital": "Health",
    "Dentist": "Health",
    "Allied Health": "Health",
    "Pharmacy": "Health",
    "Gym": "Fitness",
    "Salon/Beauty": "Fitness",
    "Childcare": "Family",
    "Cinema": "Family",
}

GROUP_ORDER = [
    "Hospo",
    "Grocery",
    "Retail",
    "Health",
    "Fitness",
    "Family",
]

# Shorter, broader display labels for categories with slash-separated names.
CATEGORY_DISPLAY = {
    "Retail (general)": "Retail",
    "Restaurant/Takeaway": "Restaurant",
    "Salon/Beauty": "Beauty",
}

CAT_HEX = {
    "food": "#c2447a",
    "grocery": "#b33f93",
    "retail": "#8465c7",
    "health": "#6b3f76",
    "fitness": "#9c2255",
    "family": "#7a1f3d",
}
ACCENT_HEX = "#8e2a52"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1OcQTgpYp7mQKCtV6wE6hOf2PEHbO_gUX7GXuAIghMl4/edit?usp=sharing"

slim = []
for d in DATA:
    cat = CATEGORY_DISPLAY.get(d["category"], d["category"])
    slim.append(
        {
            "id": d["place_id"],
            "name": d["name"],
            "cat": cat,
            "grp": GROUP_OF[d["category"]],
            "suburb": d["suburb"],
            "addr": d["address"],
            "phone": d["phone"],
            "site": d["website"],
            "rating": d["rating"],
            "lat": d["lat"],
            "lng": d["lng"],
            "dist": d["distance_km"],
        }
    )

suburbs = sorted({s["suburb"] for s in slim}, key=lambda s: min(x["dist"] for x in slim if x["suburb"] == s))
DATA_JSON = json.dumps(slim, separators=(",", ":"))
GROUP_ORDER_JSON = json.dumps(GROUP_ORDER)
SUBURBS_JSON = json.dumps(suburbs)
CAT_HEX_JSON = json.dumps(CAT_HEX)

TOTAL = len(slim)

HTML = f"""<!doctype html>
<meta charset="utf-8" />
<title>Lolo Job Hunt</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="{ACCENT_HEX}" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Lolo Job Hunt" />
<link rel="manifest" href="manifest.json" />
<link rel="apple-touch-icon" href="icon-180.png" />
<link rel="icon" href="icon-512.png" />
<style>
:root {{
  --bg: #faf3f8;
  --surface: #ffffff;
  --surface-2: #f4e7f0;
  --ink: #3a1e2e;
  --ink-dim: #7c5568;
  --ink-faint: #a98ca0;
  --line: #ecd7e5;
  --line-soft: #f2e2ec;
  --accent: {ACCENT_HEX};
  --accent-ink: #ffffff;
  --accent-soft: #f6dce7;
  --radius: 10px;

  --cat-food: {CAT_HEX["food"]};      --cat-food-bg: #fbe3ed;
  --cat-grocery: {CAT_HEX["grocery"]};   --cat-grocery-bg: #f6e0f1;
  --cat-retail: {CAT_HEX["retail"]};    --cat-retail-bg: #ece5f9;
  --cat-health: {CAT_HEX["health"]};    --cat-health-bg: #eae0f0;
  --cat-fitness: {CAT_HEX["fitness"]};   --cat-fitness-bg: #f5dce6;
  --cat-family: {CAT_HEX["family"]};    --cat-family-bg: #f1dce3;

  --font-display: -apple-system, "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
  --font-body: ui-sans-serif, system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "Roboto Mono", Menlo, Consolas, monospace;
}}

/* Light is the default regardless of OS scheme (Lolo's preference) —
   dark only applies when explicitly toggled via [data-theme="dark"]. */
:root[data-theme="dark"] {{
  --bg: #1c0f17; --surface: #241620; --surface-2: #2c1b28;
  --ink: #f3e4ec; --ink-dim: #c9a8bc; --ink-faint: #93748a;
  --line: #3a2430; --line-soft: #2f1d29;
  --accent: #e8709f; --accent-ink: #2a0f1c; --accent-soft: #3a2130;
  --cat-food: #f0a0c0; --cat-food-bg: #3a2030;
  --cat-grocery: #e6a0dc; --cat-grocery-bg: #3a2038;
  --cat-retail: #c3b0f0; --cat-retail-bg: #2e2540;
  --cat-health: #c9a8d6; --cat-health-bg: #2e2035;
  --cat-fitness: #f090b5; --cat-fitness-bg: #3a1e2c;
  --cat-family: #e8a0b8; --cat-family-bg: #351c26;
}}
:root[data-theme="light"] {{
  --bg: #faf3f8; --surface: #ffffff; --surface-2: #f4e7f0;
  --ink: #3a1e2e; --ink-dim: #7c5568; --ink-faint: #a98ca0;
  --line: #ecd7e5; --line-soft: #f2e2ec;
  --accent: {ACCENT_HEX}; --accent-ink: #ffffff; --accent-soft: #f6dce7;
  --cat-food: {CAT_HEX["food"]}; --cat-food-bg: #fbe3ed;
  --cat-grocery: {CAT_HEX["grocery"]}; --cat-grocery-bg: #f6e0f1;
  --cat-retail: {CAT_HEX["retail"]}; --cat-retail-bg: #ece5f9;
  --cat-health: {CAT_HEX["health"]}; --cat-health-bg: #eae0f0;
  --cat-fitness: {CAT_HEX["fitness"]}; --cat-fitness-bg: #f5dce6;
  --cat-family: {CAT_HEX["family"]}; --cat-family-bg: #f1dce3;
}}

* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }}
}}

.wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 16px 64px; }}

header.top {{
  padding: 28px 16px 18px;
  max-width: 1080px;
  margin: 0 auto;
}}
.eyebrow {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 8px;
}}
h1 {{
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(26px, 6vw, 38px);
  letter-spacing: -0.01em;
  line-height: 1.08;
  margin: 0 0 8px;
  text-wrap: balance;
}}
.sub {{
  color: var(--ink-dim);
  font-size: 14.5px;
  max-width: 62ch;
  margin: 0 0 4px;
}}
.sub b {{ color: var(--ink); font-weight: 600; }}
.meta-line {{
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--ink-faint);
  margin-top: 10px;
}}

.controls {{
  position: sticky;
  top: 0;
  z-index: 5;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
  padding: 10px 16px 12px;
}}
.controls-inner {{ max-width: 1080px; margin: 0 auto; display: flex; flex-direction: column; gap: 10px; }}

.search-row {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.search-row #search {{ min-width: 140px; }}
#search {{
  flex: 1;
  font: inherit;
  font-size: 15px;
  padding: 10px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
}}
#search:focus {{
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}}
select#sortSel {{
  font: inherit;
  font-size: 13.5px;
  font-family: var(--font-mono);
  padding: 0 30px 0 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background-color: var(--surface);
  color: var(--ink);
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5L6 8l3.5-3.5' stroke='%237c5568' stroke-width='1.6' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}}
:root[data-theme="dark"] select#sortSel {{
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5L6 8l3.5-3.5' stroke='%23c9a8bc' stroke-width='1.6' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
}}

.view-toggle {{
  display: flex;
  flex: 0 0 auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
}}
.view-btn {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  padding: 0 14px;
  border: none;
  background: var(--surface);
  color: var(--ink-dim);
  cursor: pointer;
}}
.view-btn + .view-btn {{ border-left: 1px solid var(--line); }}
.view-btn[data-active="1"] {{ background: var(--accent); color: var(--accent-ink); }}

.sheet-btn {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  padding: 0 14px;
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  background: var(--accent);
  color: var(--accent-ink);
  text-decoration: none;
  cursor: pointer;
}}
.sheet-btn:hover {{ opacity: 0.9; }}

.toggle-btn {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  padding: 0 14px;
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--ink-dim);
  cursor: pointer;
}}
.toggle-btn[data-active="1"] {{ background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }}

.chip-row-wrap {{ position: relative; }}
.chip-row {{
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-right: 16px;
}}
.chip-row::-webkit-scrollbar {{ display: none; }}
/* Blurred fade at the scroll edge — a soft cutoff instead of a hard clip,
   echoing the same backdrop-blur the sticky controls bar already uses */
.chip-row-wrap::after {{
  content: "";
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 40px;
  background: linear-gradient(to right, transparent, color-mix(in srgb, var(--bg) 92%, transparent) 65%);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  pointer-events: none;
}}
.chip {{
  flex: 0 0 auto;
  font-family: var(--font-mono);
  font-size: 12.5px;
  font-weight: 600;
  padding: 7px 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink-dim);
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}}
.chip[data-active="1"] {{
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-ink);
}}
.chip .n {{ opacity: 0.7; margin-left: 3px; }}

.count-row {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--ink-faint);
  padding: 14px 2px 10px;
}}

.grid {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}}
@media (min-width: 620px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
@media (min-width: 980px) {{ .grid {{ grid-template-columns: 1fr 1fr 1fr; }} }}

.card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.card[data-viewed="1"] {{ opacity: 0.5; }}
.card-top {{ display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }}
.card-name {{
  flex: 1;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 16px;
  line-height: 1.25;
  text-wrap: balance;
}}
.dist-badge {{
  font-family: var(--font-mono);
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
  color: var(--ink-faint);
  white-space: nowrap;
  padding-top: 2px;
}}

.tag-row {{ display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }}
.tag {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
  letter-spacing: 0.01em;
}}
.tag.suburb {{
  background: var(--surface-2);
  color: var(--ink-dim);
  border: 1px solid var(--line-soft);
  font-weight: 500;
}}
.addr {{ color: var(--ink-dim); font-size: 13px; }}
.rating {{
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--ink-dim);
  background: var(--surface-2);
  border: 1px solid var(--line-soft);
  padding: 3px 8px 3px 6px;
  border-radius: 999px;
}}
.rating svg {{ width: 10px; height: 10px; color: #d6a032; flex: 0 0 auto; }}
:root[data-theme="dark"] .rating svg {{ color: #e8bc63; }}
:root[data-theme="light"] .rating svg {{ color: #d6a032; }}

.action-row {{ display: flex; gap: 8px; margin-top: 2px; flex-wrap: wrap; }}
.btn {{
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  padding: 7px 12px;
  border-radius: 999px;
  text-decoration: none;
  border: 1px solid var(--line);
  color: var(--ink);
  background: var(--surface-2);
}}
.btn.primary {{ background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }}
.btn.disabled {{ opacity: 0.35; pointer-events: none; }}

.load-more-row {{ display: flex; justify-content: center; padding: 22px 0 6px; }}
#loadMoreBtn {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
  cursor: pointer;
}}
#loadMoreBtn:hover {{ border-color: var(--accent); color: var(--accent); }}

.empty {{
  text-align: center;
  color: var(--ink-faint);
  padding: 48px 16px;
  font-size: 14px;
}}

.map-toolbar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 4px 2px 10px;
}}
.map-legend {{
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}}
.map-legend .lg-item {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-dim);
  background: var(--surface-2);
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  padding: 4px 10px 4px 8px;
}}
.map-legend .lg-dot {{ width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }}
.map-legend .lg-line {{ width: 14px; height: 2px; flex: 0 0 auto; }}
.map-zoom-btns {{ display: flex; border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; flex: 0 0 auto; }}
.map-zoom-btns button {{
  width: 32px;
  height: 30px;
  border: none;
  background: var(--surface);
  color: var(--ink);
  font-size: 15px;
  cursor: pointer;
}}
.map-zoom-btns button + button {{ border-left: 1px solid var(--line); }}
.map-zoom-btns button:hover {{ background: var(--surface-2); }}

.map-wrap {{
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
  height: 60vh;
  min-height: 340px;
  max-height: 560px;
}}
#gmap {{ width: 100%; height: 100%; }}

.map-info {{
  margin-top: 10px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px;
  min-height: 74px;
}}
.map-info-empty {{ color: var(--ink-faint); font-size: 13px; margin: 0; text-align: center; padding: 14px 0; }}
.map-info .card-name {{ margin-bottom: 2px; }}

footer {{
  max-width: 1080px;
  margin: 36px auto 0;
  padding: 16px;
  border-top: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--ink-faint);
  line-height: 1.7;
  text-align: center;
}}
footer .sig {{
  display: inline-block;
  margin-top: 4px;
  color: var(--accent);
  font-weight: 700;
  letter-spacing: 0.04em;
}}
a {{ color: inherit; }}

.lock-screen {{
  position: fixed;
  inset: 0;
  z-index: 999;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}}
.lock-card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 28px 26px;
  max-width: 320px;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 30px color-mix(in srgb, var(--accent) 12%, transparent);
}}
.lock-card h2 {{
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 800;
  margin: 4px 0 6px;
}}
.lock-hint {{
  color: var(--ink-dim);
  font-size: 13.5px;
  margin: 0 0 18px;
}}
#lockInput {{
  width: 100%;
  font: inherit;
  font-size: 15px;
  padding: 10px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: var(--surface-2);
  color: var(--ink);
  text-align: center;
  margin-bottom: 10px;
}}
#lockInput:focus {{
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}}
#lockBtn {{
  width: 100%;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 700;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: var(--accent-ink);
  cursor: pointer;
}}
#lockError {{
  display: none;
  color: var(--accent);
  font-size: 12.5px;
  margin-top: 10px;
}}

/* iPhone: inputs under 16px make Safari auto-zoom the page on focus */
@media (max-width: 480px) {{
  #search, #lockInput {{ font-size: 16px; }}
}}

/* MacBook / wide desktop: use the extra width instead of leaving it as
   dead gutters either side of a centered 1080px column */
@media (min-width: 1400px) {{
  .wrap, .controls-inner, header.top, footer {{ max-width: 1320px; }}
  .grid {{ grid-template-columns: repeat(4, 1fr); }}
}}

/* Desktop-only hover affordances — gated on real pointers so a touch tap
   doesn't leave a "stuck" hover state on iPhone */
@media (hover: hover) and (pointer: fine) {{
  .card {{ transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease; }}
  .card:hover {{
    border-color: var(--accent);
    box-shadow: 0 6px 20px color-mix(in srgb, var(--accent) 10%, transparent);
    transform: translateY(-1px);
  }}
  .chip:hover:not([data-active="1"]) {{ border-color: var(--accent); color: var(--accent); }}
  .toggle-btn:hover:not([data-active="1"]) {{ border-color: var(--accent); color: var(--accent); }}
  #search:hover {{ border-color: var(--ink-faint); }}
}}

/* Viewed checkbox — square, single control per card. Checking it dims the
   card and persists (localStorage), and also feeds the bulk-copy list. */
.viewed-box {{ position: relative; flex: 0 0 auto; width: 24px; height: 24px; margin-top: 1px; cursor: pointer; }}
.viewed-box input {{ position: absolute; inset: 0; opacity: 0; margin: 0; cursor: pointer; }}
.viewed-mark {{
  position: absolute;
  inset: 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--surface);
  display: flex;
  align-items: center;
  justify-content: center;
}}
.viewed-box input:checked + .viewed-mark {{ background: var(--accent); border-color: var(--accent); }}
.viewed-box input:checked + .viewed-mark::after {{
  content: "";
  width: 9px;
  height: 5px;
  margin-top: -2px;
  border-left: 2px solid var(--accent-ink);
  border-bottom: 2px solid var(--accent-ink);
  transform: rotate(-45deg);
}}
.viewed-box input:focus-visible + .viewed-mark {{ outline: 2px solid var(--accent); outline-offset: 2px; }}

/* Per-business note toggle + box */
.btn.note-btn.has-note {{ border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }}
.note-box {{
  width: 100%;
  font: inherit;
  font-size: 13px;
  color: var(--ink);
  background: var(--surface-2);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius);
  padding: 8px 10px;
  min-height: 56px;
  resize: vertical;
}}
.note-box:focus {{ outline: none; border-color: var(--accent); }}

/* Inline "clear filters" link injected into the count row once any
   filter/search/toggle differs from the default state */
.clear-btn {{
  font: inherit;
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--accent);
  background: none;
  border: none;
  padding: 0 0 0 6px;
  cursor: pointer;
  text-decoration: underline;
}}

/* Floating bulk-copy bar for the select-for-export checkboxes */
.export-bar {{
  position: fixed;
  left: 50%;
  bottom: calc(20px + env(safe-area-inset-bottom));
  transform: translateX(-50%);
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 8px 8px 16px;
  box-shadow: 0 10px 30px color-mix(in srgb, var(--ink) 18%, transparent);
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: var(--ink-dim);
}}
.export-bar .btn {{ padding: 6px 14px; }}
.export-bar .btn svg {{ width: 13px; height: 13px; vertical-align: -2px; margin-right: 4px; }}
</style>

<div class="lock-screen" id="lockScreen">
  <div class="lock-card">
    <div style="font-size:26px">&#128274;</div>
    <h2>This one's just for you</h2>
    <p class="lock-hint">hint: it is your favourite kutta</p>
    <input id="lockInput" type="password" placeholder="Password" autocomplete="off" />
    <button id="lockBtn">Unlock</button>
    <p id="lockError">not quite &mdash; try again</p>
  </div>
</div>

<header class="top">
  <h1>Go get 'em, Lolo &#128156;</h1>
  <p class="meta-line" id="cheerLine">tap a card &rarr; call or get directions</p>
</header>

<div class="controls">
  <div class="controls-inner">
    <div class="search-row">
      <input id="search" type="text" placeholder="Search by name&hellip;" autocomplete="off" />
      <select id="sortSel">
        <option value="dist">Nearest first</option>
        <option value="name">A&ndash;Z</option>
        <option value="rating">Highest rated</option>
        <option value="me">Near me now</option>
      </select>
      <div class="view-toggle">
        <button class="view-btn" data-view="list" data-active="1">List</button>
        <button class="view-btn" data-view="map" data-active="0">Map</button>
      </div>
      <a class="sheet-btn" href="{SHEET_URL}" target="_blank" rel="noopener">Sheet</a>
      <button id="viewedOnlyBtn" class="toggle-btn" data-active="0">Viewed only</button>
    </div>
    <div class="chip-row-wrap"><div class="chip-row" id="groupChips"></div></div>
    <div class="chip-row-wrap"><div class="chip-row" id="suburbChips"></div></div>
  </div>
</div>

<div class="wrap">
  <div class="count-row">
    <span id="countLabel"></span>
  </div>
  <div class="grid" id="grid"></div>
  <div class="load-more-row" id="loadMoreRow" style="display:none">
    <button id="loadMoreBtn">Show more</button>
  </div>
  <div class="empty" id="emptyState" style="display:none">No businesses match that search.</div>

  <div id="mapSection" style="display:none">
    <div class="map-toolbar">
      <div class="map-legend" id="mapLegend"></div>
      <div class="map-zoom-btns">
        <button id="zoomOutBtn" title="Zoom out">&minus;</button>
        <button id="zoomResetBtn" title="Reset view">&#8982;</button>
        <button id="zoomInBtn" title="Zoom in">+</button>
      </div>
    </div>
    <div class="map-wrap" id="mapWrap">
      <div id="gmap"></div>
    </div>
    <div class="map-info" id="mapInfo">
      <p class="map-info-empty">tap a pin to see who they are &#128205;</p>
    </div>
  </div>
</div>

<div class="export-bar" id="exportBar" style="display:none">
  <span id="exportCount"></span>
  <button id="exportCopyBtn" class="btn primary">Copy</button>
</div>

<footer>
  Data pulled from Google Places API.
  <br />Built with love, for Lolo.
  <br /><span class="sig">VeerLo&trade;</span>
</footer>

<script>
const UNLOCK_KEY = "lolo_unlocked";
const UNLOCK_PASSWORD = "veer";
function checkUnlock() {{
  if (localStorage.getItem(UNLOCK_KEY) === "1") {{
    document.getElementById("lockScreen").style.display = "none";
  }}
}}
function tryUnlock() {{
  const input = document.getElementById("lockInput");
  if (input.value.trim().toLowerCase() === UNLOCK_PASSWORD) {{
    localStorage.setItem(UNLOCK_KEY, "1");
    document.getElementById("lockScreen").style.display = "none";
  }} else {{
    document.getElementById("lockError").style.display = "block";
    input.value = "";
    input.focus();
  }}
}}
document.getElementById("lockBtn").addEventListener("click", tryUnlock);
document.getElementById("lockInput").addEventListener("keydown", (e) => {{
  if (e.key === "Enter") tryUnlock();
}});
checkUnlock();

const DATA = {DATA_JSON};
const GROUP_ORDER = {GROUP_ORDER_JSON};
const SUBURBS = {SUBURBS_JSON};
const CAT_HEX = {CAT_HEX_JSON};
const ACCENT_HEX = "{ACCENT_HEX}";
const REF = {{ lat: -37.7000101, lng: 145.0615908 }};

const state = {{ q: "", group: "All", suburb: "All", sort: "dist", visible: 40, view: "list", viewedOnly: false }};
const PAGE = 40;

/* "viewed" replaces the old separate "applied" (status/dimming) and
   "selected" (export) concepts with one persisted checkbox per card.
   One-time migration: anyone who already marked businesses "applied" on
   the live site keeps that progress instead of it silently resetting. */
const VIEWED_KEY = "bundoora_viewed";
const LEGACY_APPLIED_KEY = "bundoora_applied";
let viewedSeed = localStorage.getItem(VIEWED_KEY);
if (viewedSeed === null) {{
  viewedSeed = localStorage.getItem(LEGACY_APPLIED_KEY) || "[]";
}}
const viewed = new Set(JSON.parse(viewedSeed));
function saveViewed() {{
  localStorage.setItem(VIEWED_KEY, JSON.stringify([...viewed]));
}}
function setViewed(id, isViewed) {{
  if (isViewed) viewed.add(id);
  else viewed.delete(id);
  saveViewed();
  updateExportBar();
}}

const notes = JSON.parse(localStorage.getItem("bundoora_notes") || "{{}}");
function saveNotes() {{
  localStorage.setItem("bundoora_notes", JSON.stringify(notes));
}}
let myPos = null;
function haversine(p, d) {{
  const R = 6371;
  const dLat = ((d.lat - p.lat) * Math.PI) / 180;
  const dLng = ((d.lng - p.lng) * Math.PI) / 180;
  const s = Math.sin(dLat / 2) ** 2 + Math.cos((p.lat * Math.PI) / 180) * Math.cos((d.lat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}}

const CHEER_LINES = [
  "tap a card &rarr; call or get directions",
  "you don't need to be ready, just brave &#128156;",
  "worst case: they say no. best case: your first shift &#10024;",
  "small suburb, big opportunities &#127793;",
  "coffee in one hand, resume in the other &#9749;",
  "one good chat is all it takes",
];
function pickCheer() {{
  const el = document.getElementById("cheerLine");
  if (el) el.innerHTML = CHEER_LINES[Math.floor(Math.random() * CHEER_LINES.length)];
}}

function groupCounts() {{
  const c = {{}};
  for (const d of DATA) c[d.grp] = (c[d.grp] || 0) + 1;
  return c;
}}
function suburbCounts() {{
  const c = {{}};
  for (const d of DATA) c[d.suburb] = (c[d.suburb] || 0) + 1;
  return c;
}}

function renderChips() {{
  const gc = groupCounts();
  const groupChips = document.getElementById("groupChips");
  const chips = [{{ key: "All", label: "All", n: DATA.length }}].concat(
    GROUP_ORDER.map((g) => ({{ key: g, label: g, n: gc[g] || 0 }}))
  );
  groupChips.innerHTML = chips
    .map(
      (c) =>
        `<button class="chip" data-key="${{c.key}}" data-active="${{state.group === c.key ? 1 : 0}}">${{c.label}}<span class="n">${{c.n}}</span></button>`
    )
    .join("");
  groupChips.querySelectorAll(".chip").forEach((el) =>
    el.addEventListener("click", () => {{
      state.group = el.dataset.key;
      state.visible = PAGE;
      renderChips();
      render();
    }})
  );

  const sc = suburbCounts();
  const suburbChips = document.getElementById("suburbChips");
  const schips = [{{ key: "All", label: "All suburbs", n: DATA.length }}].concat(
    SUBURBS.map((s) => ({{ key: s, label: s, n: sc[s] || 0 }}))
  );
  suburbChips.innerHTML = schips
    .map(
      (c) =>
        `<button class="chip" data-key="${{c.key}}" data-active="${{state.suburb === c.key ? 1 : 0}}">${{c.label}}<span class="n">${{c.n}}</span></button>`
    )
    .join("");
  suburbChips.querySelectorAll(".chip").forEach((el) =>
    el.addEventListener("click", () => {{
      state.suburb = el.dataset.key;
      state.visible = PAGE;
      renderChips();
      render();
    }})
  );
}}

function filtered() {{
  let rows = DATA;
  if (state.group !== "All") rows = rows.filter((d) => d.grp === state.group);
  if (state.suburb !== "All") rows = rows.filter((d) => d.suburb === state.suburb);
  if (state.viewedOnly) rows = rows.filter((d) => viewed.has(d.id));
  if (state.q) {{
    const q = state.q.toLowerCase();
    rows = rows.filter((d) => d.name.toLowerCase().includes(q));
  }}
  rows = rows.slice();
  if (state.sort === "dist") rows.sort((a, b) => (a.dist ?? 1e9) - (b.dist ?? 1e9));
  else if (state.sort === "name") rows.sort((a, b) => a.name.localeCompare(b.name));
  else if (state.sort === "rating") rows.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
  else if (state.sort === "me" && myPos) {{
    rows.forEach((d) => {{ d._liveDist = haversine(myPos, d); }});
    rows.sort((a, b) => a._liveDist - b._liveDist);
  }}
  return rows;
}}

function hasActiveFilters() {{
  return state.group !== "All" || state.suburb !== "All" || !!state.q || state.viewedOnly;
}}
function clearFiltersBtnHtml() {{
  return hasActiveFilters() ? ` <button id="clearFiltersBtn" class="clear-btn">clear filters</button>` : "";
}}
function wireClearFilters() {{
  const btn = document.getElementById("clearFiltersBtn");
  if (!btn) return;
  btn.addEventListener("click", () => {{
    state.group = "All";
    state.suburb = "All";
    state.q = "";
    state.viewedOnly = false;
    state.visible = PAGE;
    document.getElementById("search").value = "";
    document.getElementById("viewedOnlyBtn").dataset.active = "0";
    renderChips();
    render();
  }});
}}

function catColorVar(grp) {{
  return (
    {{
      "Hospo": "food",
      "Grocery": "grocery",
      Retail: "retail",
      "Health": "health",
      "Fitness": "fitness",
      "Family": "family",
    }}[grp] || "food"
  );
}}

function mapsUrl(d) {{
  const q = encodeURIComponent(`${{d.name}} ${{d.addr}}`);
  if (d.id) return `https://www.google.com/maps/search/?api=1&query=${{q}}&query_place_id=${{d.id}}`;
  if (d.lat && d.lng) return `https://www.google.com/maps/search/?api=1&query=${{d.lat}},${{d.lng}}`;
  return `https://www.google.com/maps/search/?api=1&query=${{encodeURIComponent(d.addr)}}`;
}}

const STAR_SVG =
  '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 1.6l2.47 5.24 5.63.78-4.08 4.06.99 5.72L10 14.5l-5.01 2.9.99-5.72L1.9 7.62l5.63-.78L10 1.6z"/></svg>';
const CLIPBOARD_SVG =
  '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="4" width="10" height="14" rx="1.5"/><path d="M8 4V3a1 1 0 011-1h2a1 1 0 011 1v1"/><path d="M8 10h4M8 13h4"/></svg>';
function ratingChip(rating) {{
  if (!rating) return "";
  return `<span class="rating">${{STAR_SVG}}${{rating}}</span>`;
}}

function card(d) {{
  const k = catColorVar(d.grp);
  const isViewed = viewed.has(d.id);
  const hasNote = !!notes[d.id];
  const dist = d._liveDist != null ? d._liveDist : d.dist;
  const phoneHtml = d.phone
    ? `<a class="btn primary" href="tel:${{d.phone.replace(/[^+\\d]/g, "")}}">Call ${{d.phone}}</a>`
    : `<span class="btn disabled">No phone listed</span>`;
  const siteHtml = d.site ? `<a class="btn" href="${{d.site}}" target="_blank" rel="noopener">Website</a>` : "";
  return `
  <div class="card" data-viewed="${{isViewed ? 1 : 0}}">
    <div class="card-top">
      <label class="viewed-box" title="Mark viewed / select for export">
        <input type="checkbox" class="viewed-cb" data-id="${{d.id}}" ${{isViewed ? "checked" : ""}} />
        <span class="viewed-mark"></span>
      </label>
      <div class="card-name">${{d.name}}</div>
    </div>
    <div class="tag-row">
      <span class="tag" style="background:var(--cat-${{k}}-bg);color:var(--cat-${{k}})">${{d.cat}}</span>
      <span class="tag suburb">${{d.suburb}}</span>
      ${{ratingChip(d.rating)}}
      <span class="dist-badge">${{dist != null ? dist.toFixed(1) + " km" : ""}}</span>
    </div>
    <div class="addr">${{d.addr}}</div>
    <div class="action-row">
      ${{phoneHtml}}
      <a class="btn" href="${{mapsUrl(d)}}" target="_blank" rel="noopener">Directions</a>
      ${{siteHtml}}
      <button class="btn note-btn ${{hasNote ? "has-note" : ""}}" data-id="${{d.id}}">${{hasNote ? "Note &#9998;" : "Add note"}}</button>
    </div>
    <textarea class="note-box" data-id="${{d.id}}" placeholder="e.g. asked for manager, follow up Tues" style="display:${{hasNote ? "block" : "none"}}">${{notes[d.id] || ""}}</textarea>
  </div>`;
}}

function render() {{
  const rows = filtered();
  document.getElementById("emptyState").style.display = rows.length ? "none" : "block";
  if (state.view === "map") {{
    document.getElementById("countLabel").innerHTML = `${{rows.length}} pinned${{clearFiltersBtnHtml()}}`;
    wireClearFilters();
    renderMap(rows);
  }} else {{
    renderList(rows);
  }}
}}

function renderList(rows) {{
  const grid = document.getElementById("grid");
  const slice = rows.slice(0, state.visible);
  grid.innerHTML = slice.map(card).join("");
  document.getElementById("countLabel").innerHTML = `showing ${{slice.length}} of ${{rows.length}}${{clearFiltersBtnHtml()}}`;
  wireClearFilters();
  document.getElementById("loadMoreRow").style.display = rows.length > slice.length ? "flex" : "none";

  grid.querySelectorAll(".viewed-cb").forEach((cb) =>
    cb.addEventListener("change", () => {{
      const id = cb.dataset.id;
      setViewed(id, cb.checked);
      cb.closest(".card").dataset.viewed = cb.checked ? "1" : "0";
    }})
  );

  grid.querySelectorAll(".note-btn").forEach((btn) =>
    btn.addEventListener("click", () => {{
      const box = btn.closest(".card").querySelector(".note-box");
      const isOpen = box.style.display !== "none";
      box.style.display = isOpen ? "none" : "block";
      if (!isOpen) box.focus();
    }})
  );

  grid.querySelectorAll(".note-box").forEach((box) =>
    box.addEventListener("input", () => {{
      const id = box.dataset.id;
      if (box.value.trim()) notes[id] = box.value;
      else delete notes[id];
      saveNotes();
      const btn = box.closest(".card").querySelector(".note-btn");
      btn.textContent = notes[id] ? "Note \\u270e" : "Add note";
      btn.classList.toggle("has-note", !!notes[id]);
    }})
  );
}}

/* ---- Map view: real Google Maps JS SDK — street basemap + live transit
   layer (tram/train/bus routes), category-coloured markers, clustered for
   performance across 1500+ points, plus a home pin at Lolo's address. ---- */
const LEGEND = [
  ["Hospo", "food"],
  ["Grocery", "grocery"],
  ["Retail", "retail"],
  ["Health", "health"],
  ["Fitness", "fitness"],
  ["Family", "family"],
];
const ROUTE_LEGEND = [
  ["Tram 86", "{ACCENT_HEX}", false],
  ["Bus 903", "{CAT_HEX["retail"]}", true],
  ["Bus 561", "{CAT_HEX["health"]}", true],
];
function renderLegend() {{
  const catHtml = LEGEND.map(
    ([label, k]) => `<span class="lg-item"><span class="lg-dot" style="background:var(--cat-${{k}})"></span>${{label}}</span>`
  ).join("");
  const routeHtml = ROUTE_LEGEND.map(
    ([label, color, dash]) =>
      `<span class="lg-item"><span class="lg-line" style="background:${{dash ? "none" : color}};border-top:${{dash ? "2px dashed " + color : "none"}}"></span>${{label}}</span>`
  ).join("");
  document.getElementById("mapLegend").innerHTML = catHtml + routeHtml;
}}

function mapInfoHtml(d) {{
  const isViewed = viewed.has(d.id);
  const phoneHtml = d.phone
    ? `<a class="btn primary" href="tel:${{d.phone.replace(/[^+\\d]/g, "")}}">Call ${{d.phone}}</a>`
    : `<span class="btn disabled">No phone listed</span>`;
  const siteHtml = d.site ? `<a class="btn" href="${{d.site}}" target="_blank" rel="noopener">Website</a>` : "";
  const k = catColorVar(d.grp);
  const dist = d._liveDist != null ? d._liveDist : d.dist;
  return `
    <div class="card-top">
      <label class="viewed-box" title="Mark viewed / select for export">
        <input type="checkbox" class="viewed-cb-map" data-id="${{d.id}}" ${{isViewed ? "checked" : ""}} />
        <span class="viewed-mark"></span>
      </label>
      <div class="card-name">${{d.name}}</div>
    </div>
    <div class="tag-row">
      <span class="tag" style="background:var(--cat-${{k}}-bg);color:var(--cat-${{k}})">${{d.cat}}</span>
      <span class="tag suburb">${{d.suburb}}</span>
      ${{ratingChip(d.rating)}}
      <span class="dist-badge">${{dist != null ? dist.toFixed(1) + " km" : ""}}</span>
    </div>
    <div class="addr">${{d.addr}}</div>
    <div class="action-row">
      ${{phoneHtml}}
      <a class="btn" href="${{mapsUrl(d)}}" target="_blank" rel="noopener">Directions</a>
      ${{siteHtml}}
    </div>`;
}}

function showMapInfo(d) {{
  const info = document.getElementById("mapInfo");
  info.innerHTML = mapInfoHtml(d);
  info.querySelector(".viewed-cb-map").addEventListener("change", (e) => {{
    const cb = e.currentTarget;
    setViewed(d.id, cb.checked);
    const marker = mapMarkers.find((m) => m.__id === d.id);
    if (marker) marker.setOpacity(cb.checked ? 0.45 : 1);
  }});
}}

function dotIcon(hex) {{
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18'><circle cx='9' cy='9' r='6.5' fill='${{hex}}' fill-opacity='0.88' stroke='white' stroke-width='2'/></svg>`;
  return {{
    url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
    scaledSize: new google.maps.Size(18, 18),
    anchor: new google.maps.Point(9, 9),
  }};
}}
function homeIcon() {{
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='36' height='36'><circle cx='18' cy='18' r='17' fill='white' stroke='${{ACCENT_HEX}}' stroke-width='2'/><path d='M18 8 L29 17 V28 H21 V20 H15 V28 H7 V17 Z' fill='${{ACCENT_HEX}}'/></svg>`;
  return {{
    url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
    scaledSize: new google.maps.Size(36, 36),
    anchor: new google.maps.Point(18, 18),
  }};
}}

/* Cluster heatmap: same pink→burgundy palette as the rest of the site,
   diluted with low opacity so the transit lines/labels underneath (the
   actual point of the map) stay the visual focus, not the pin blobs. */
const CLUSTER_STOPS = [
  [246, 220, 231], // light pink, --accent-soft
  [194, 68, 122], // rose, --cat-food
  [90, 21, 48], // deep burgundy, near --cat-family
];
function lerp(a, b, t) {{ return a + (b - a) * t; }}
function clusterColor(t) {{
  const seg = t < 0.5 ? [CLUSTER_STOPS[0], CLUSTER_STOPS[1], t * 2] : [CLUSTER_STOPS[1], CLUSTER_STOPS[2], (t - 0.5) * 2];
  const [c0, c1, tt] = seg;
  return [Math.round(lerp(c0[0], c1[0], tt)), Math.round(lerp(c0[1], c1[1], tt)), Math.round(lerp(c0[2], c1[2], tt))];
}}
let clusterGradId = 0;
class PaletteClusterRenderer {{
  render({{ count, position }}, stats) {{
    const maxCount = Math.max(stats.clusters.markers.max || count, 2);
    const t = Math.log(count + 1) / Math.log(maxCount + 1);
    const [r, g, b] = clusterColor(t);
    const rad = 15 + 11 * Math.sqrt(t);
    const canvasR = rad * 1.7;
    const d = canvasR * 2;
    const gid = `cg${{clusterGradId++}}`;
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${{d}}' height='${{d}}'>
      <defs><radialGradient id='${{gid}}' cx='50%' cy='50%' r='50%'>
        <stop offset='0%' stop-color='rgba(${{r}},${{g}},${{b}},0.42)'/>
        <stop offset='55%' stop-color='rgba(${{r}},${{g}},${{b}},0.22)'/>
        <stop offset='100%' stop-color='rgba(${{r}},${{g}},${{b}},0)'/>
      </radialGradient></defs>
      <circle cx='${{canvasR}}' cy='${{canvasR}}' r='${{canvasR}}' fill='url(#${{gid}})'/>
    </svg>`;
    return new google.maps.Marker({{
      position,
      icon: {{
        url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
        scaledSize: new google.maps.Size(d, d),
        anchor: new google.maps.Point(canvasR, canvasR),
      }},
      label: {{ text: String(count), color: "{ACCENT_HEX}", fontSize: "12px", fontWeight: "700" }},
      zIndex: 500 + count,
    }});
  }}
}}

let gmap = null;
let clusterer = null;
let mapMarkers = [];
let homeMarker = null;
let gmapsReady = false;

/* Named route overlays. Tram 86 runs on fixed tracks, so transit directions
   between its two termini reliably trace the real line. Bus routes run on
   roads, so these are Google's best transit path between two real stops on
   that route near Bundoora — a close approximation, not an official GTFS
   shape (Maps JS API doesn't expose individual route geometry). */
const TRANSIT_ROUTES = [
  {{
    name: "Tram 86",
    mode: "TRAM",
    origin: "Plenty Rd & McKimmies Rd, Bundoora VIC",
    destination: "Waterfront City, Docklands VIC",
    color: "{ACCENT_HEX}",
    weight: 4,
    dash: false,
  }},
  {{
    name: "Bus 903 (SmartBus)",
    mode: "BUS",
    origin: "La Trobe University, Bundoora VIC",
    destination: "Greensborough Plaza, Greensborough VIC",
    color: "{CAT_HEX["retail"]}",
    weight: 3,
    dash: true,
  }},
  {{
    name: "Bus 561",
    mode: "BUS",
    origin: "La Trobe University, Bundoora VIC",
    destination: "Northland Shopping Centre, Preston VIC",
    color: "{CAT_HEX["health"]}",
    weight: 3,
    dash: true,
  }},
];
const dashedLine = {{
  path: "M 0,-1 0,1",
  strokeOpacity: 0,
  scale: 3,
}};

function renderTransitRoutes() {{
  const directionsService = new google.maps.DirectionsService();
  TRANSIT_ROUTES.forEach((route) => {{
    directionsService.route(
      {{
        origin: route.origin,
        destination: route.destination,
        travelMode: "TRANSIT",
        transitOptions: {{ modes: [route.mode] }},
      }},
      (result, status) => {{
        if (status !== "OK") {{
          console.warn(`Transit route "${{route.name}}" unavailable: ${{status}}`);
          return;
        }}
        new google.maps.DirectionsRenderer({{
          map: gmap,
          directions: result,
          suppressMarkers: true,
          suppressInfoWindows: true,
          preserveViewport: true,
          polylineOptions: route.dash
            ? {{
                strokeOpacity: 0,
                strokeColor: route.color,
                icons: [{{ icon: {{ ...dashedLine, strokeColor: route.color, strokeOpacity: 0.85 }}, offset: "0", repeat: "14px" }}],
                zIndex: 50,
              }}
            : {{
                strokeColor: route.color,
                strokeOpacity: 0.85,
                strokeWeight: route.weight,
                zIndex: 50,
              }},
        }});
      }}
    );
  }});
}}

function initMap() {{
  gmap = new google.maps.Map(document.getElementById("gmap"), {{
    center: REF,
    zoom: 14,
    streetViewControl: false,
    fullscreenControl: false,
    mapTypeControl: false,
    gestureHandling: "greedy",
    clickableIcons: false,
  }});
  new google.maps.TransitLayer().setMap(gmap);
  renderTransitRoutes();
  homeMarker = new google.maps.Marker({{
    position: REF,
    map: gmap,
    icon: homeIcon(),
    title: "566 Grimshaw Street \\u2014 you are here",
    zIndex: 999,
  }});
  gmapsReady = true;
  if (state.view === "map") renderMap(filtered());
}}
window.initMap = initMap;

function clearMarkers() {{
  if (clusterer) {{
    clusterer.clearMarkers();
    clusterer = null;
  }}
  mapMarkers.forEach((m) => m.setMap(null));
  mapMarkers = [];
}}

function renderMap(rows) {{
  renderLegend();
  if (!gmapsReady) return;
  clearMarkers();

  mapMarkers = rows.map((d) => {{
    const k = catColorVar(d.grp);
    const marker = new google.maps.Marker({{
      position: {{ lat: d.lat, lng: d.lng }},
      icon: dotIcon(CAT_HEX[k]),
      title: d.name,
      opacity: viewed.has(d.id) ? 0.45 : 1,
    }});
    marker.__id = d.id;
    marker.addListener("click", () => showMapInfo(d));
    return marker;
  }});

  if (window.markerClusterer) {{
    clusterer = new window.markerClusterer.MarkerClusterer({{
      map: gmap,
      markers: mapMarkers,
      renderer: new PaletteClusterRenderer(),
    }});
  }} else {{
    mapMarkers.forEach((m) => m.setMap(gmap));
  }}
}}

function fitMapToData(rows) {{
  if (!gmapsReady) return;
  const bounds = new google.maps.LatLngBounds();
  bounds.extend(REF);
  rows.forEach((d) => bounds.extend({{ lat: d.lat, lng: d.lng }}));
  gmap.fitBounds(bounds, 40);
}}

document.getElementById("zoomInBtn").addEventListener("click", () => {{
  if (gmap) gmap.setZoom(gmap.getZoom() + 1);
}});
document.getElementById("zoomOutBtn").addEventListener("click", () => {{
  if (gmap) gmap.setZoom(gmap.getZoom() - 1);
}});
document.getElementById("zoomResetBtn").addEventListener("click", () => {{
  fitMapToData(filtered());
}});

document.querySelectorAll(".view-btn").forEach((btn) =>
  btn.addEventListener("click", () => {{
    state.view = btn.dataset.view;
    document.querySelectorAll(".view-btn").forEach((b) => (b.dataset.active = b === btn ? "1" : "0"));
    const isMap = state.view === "map";
    document.getElementById("grid").style.display = isMap ? "none" : "grid";
    document.getElementById("mapSection").style.display = isMap ? "block" : "none";
    document.getElementById("loadMoreRow").style.display = isMap ? "none" : document.getElementById("loadMoreRow").style.display;
    render();
    if (isMap && gmapsReady) {{
      google.maps.event.trigger(gmap, "resize");
      if (!renderMap.fittedOnce) {{
        fitMapToData(filtered());
        renderMap.fittedOnce = true;
      }}
    }}
  }})
);

document.getElementById("search").addEventListener("input", (e) => {{
  state.q = e.target.value.trim();
  state.visible = PAGE;
  render();
}});
document.getElementById("sortSel").addEventListener("change", (e) => {{
  const val = e.target.value;
  if (val === "me") {{
    const prevSort = state.sort;
    if (!navigator.geolocation) {{
      alert("Location isn't available in this browser.");
      e.target.value = prevSort;
      return;
    }}
    document.getElementById("cheerLine").textContent = "finding you\\u2026";
    navigator.geolocation.getCurrentPosition(
      (pos) => {{
        myPos = {{ lat: pos.coords.latitude, lng: pos.coords.longitude }};
        state.sort = "me";
        pickCheer();
        render();
      }},
      () => {{
        alert("Couldn't get your location \\u2014 check location permissions for this site and try again.");
        e.target.value = prevSort;
      }},
      {{ timeout: 8000, maximumAge: 60000 }}
    );
    return;
  }}
  state.sort = val;
  render();
}});
document.getElementById("viewedOnlyBtn").addEventListener("click", (e) => {{
  state.viewedOnly = !state.viewedOnly;
  e.currentTarget.dataset.active = state.viewedOnly ? "1" : "0";
  state.visible = PAGE;
  render();
}});
document.getElementById("loadMoreBtn").addEventListener("click", () => {{
  state.visible += PAGE;
  render();
}});

/* Copies the checked ("viewed") cards' info (name/category/address/phone/
   site/note) to the clipboard as plain text, for pasting into Notes or a
   message. */
function exportText() {{
  return DATA.filter((d) => viewed.has(d.id))
    .map((d) => {{
      const lines = [`${{d.name}} \\u2014 ${{d.cat}}, ${{d.suburb}}`, d.addr];
      if (d.phone) lines.push(d.phone);
      if (d.site) lines.push(d.site);
      if (notes[d.id]) lines.push(`Note: ${{notes[d.id]}}`);
      return lines.join("\\n");
    }})
    .join("\\n\\n");
}}
function updateExportBar() {{
  const bar = document.getElementById("exportBar");
  const n = viewed.size;
  bar.style.display = n ? "flex" : "none";
  document.getElementById("exportCount").textContent = `${{n}} viewed`;
}}
document.getElementById("exportCopyBtn").addEventListener("click", async (e) => {{
  const btn = e.currentTarget;
  try {{
    await navigator.clipboard.writeText(exportText());
    btn.textContent = "Copied \\u2713";
  }} catch (err) {{
    btn.textContent = "Couldn't copy";
  }}
  setTimeout(() => {{
    btn.innerHTML = `${{CLIPBOARD_SVG}} Copy`;
  }}, 1500);
}});

/* MacBook: "/" jumps to search like GitHub's search shortcut, Escape drops
   focus back out. Skipped while already typing so it doesn't eat a literal "/". */
document.addEventListener("keydown", (e) => {{
  const tag = (e.target.tagName || "").toLowerCase();
  const typing = tag === "input" || tag === "select" || tag === "textarea";
  const search = document.getElementById("search");
  if (e.key === "/" && !typing) {{
    e.preventDefault();
    search.focus();
  }} else if (e.key === "Escape" && document.activeElement === search) {{
    search.blur();
  }}
}});

document.getElementById("exportCopyBtn").innerHTML = `${{CLIPBOARD_SVG}} Copy`;
updateExportBar();

if ("serviceWorker" in navigator) {{
  window.addEventListener("load", () => {{
    navigator.serviceWorker.register("sw.js").catch(() => {{}});
  }});
}}

pickCheer();
renderChips();
render();
</script>
<script src="https://unpkg.com/@googlemaps/markerclusterer@2.5.3/dist/index.min.js"></script>
<script async defer src="https://maps.googleapis.com/maps/api/js?key={GMAPS_KEY}&callback=initMap&loading=async"></script>
"""

out = BASE / "index.html"
out.write_text(HTML, encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")

MANIFEST = {
    "name": "Lolo Job Hunt",
    "short_name": "Job Hunt",
    "start_url": "./index.html",
    "scope": "./",
    "display": "standalone",
    "background_color": "#faf3f8",
    "theme_color": ACCENT_HEX,
    "icons": [
        {"src": "icon-180.png", "sizes": "180x180", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    ],
}
manifest_out = BASE / "manifest.json"
manifest_out.write_text(json.dumps(MANIFEST, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {manifest_out}")
