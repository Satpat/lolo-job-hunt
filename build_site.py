#!/usr/bin/env python3
"""Build the self-contained shareable HTML directory from data/businesses.json."""

import json
from pathlib import Path

BASE = Path(__file__).parent
DATA = json.loads((BASE / "data" / "businesses.json").read_text())

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

TOTAL = len(slim)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1E2w-MA5pfL-udws7pqbvqN6rxHSjilcvV4nRia2WlLQ/edit?usp=sharing"

HTML = f"""<meta charset="utf-8" />
<title>Lolo Job Hunt</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
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
  --accent: #8e2a52;
  --accent-ink: #ffffff;
  --accent-soft: #f6dce7;
  --radius: 10px;

  --cat-food: #c2447a;      --cat-food-bg: #fbe3ed;
  --cat-grocery: #b33f93;   --cat-grocery-bg: #f6e0f1;
  --cat-retail: #8465c7;    --cat-retail-bg: #ece5f9;
  --cat-health: #6b3f76;    --cat-health-bg: #eae0f0;
  --cat-fitness: #9c2255;   --cat-fitness-bg: #f5dce6;
  --cat-family: #7a1f3d;    --cat-family-bg: #f1dce3;

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
  --accent: #8e2a52; --accent-ink: #ffffff; --accent-soft: #f6dce7;
  --cat-food: #c2447a; --cat-food-bg: #fbe3ed;
  --cat-grocery: #b33f93; --cat-grocery-bg: #f6e0f1;
  --cat-retail: #8465c7; --cat-retail-bg: #ece5f9;
  --cat-health: #6b3f76; --cat-health-bg: #eae0f0;
  --cat-fitness: #9c2255; --cat-fitness-bg: #f5dce6;
  --cat-family: #7a1f3d; --cat-family-bg: #f1dce3;
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
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--ink-dim);
  text-decoration: none;
  cursor: pointer;
}}
.sheet-btn:hover {{ border-color: var(--accent); color: var(--accent); }}

.chip-row {{
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-right: 16px;
  -webkit-mask-image: linear-gradient(to right, black calc(100% - 28px), transparent 100%);
  mask-image: linear-gradient(to right, black calc(100% - 28px), transparent 100%);
}}
.chip-row::-webkit-scrollbar {{ display: none; }}
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
.card[data-applied="1"] {{ opacity: 0.5; }}
.card-top {{ display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }}
.card-name {{
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

.applied-btn {{
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid var(--line);
  background: var(--surface);
  color: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}}
.applied-btn svg {{ width: 13px; height: 13px; }}
.applied-btn[aria-pressed="true"] {{
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-ink);
}}
.applied-btn:hover {{ border-color: var(--accent); }}
.applied-btn:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
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
  gap: 10px;
  flex-wrap: wrap;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-dim);
}}
.map-legend .lg-item {{ display: flex; align-items: center; gap: 4px; }}
.map-legend .lg-dot {{ width: 8px; height: 8px; border-radius: 50%; flex: 0 0 auto; }}
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
  touch-action: none;
  height: 60vh;
  min-height: 340px;
  max-height: 560px;
}}
#mapSvg {{ width: 100%; height: 100%; display: block; cursor: grab; }}
#mapSvg:active {{ cursor: grabbing; }}
.map-pin {{ cursor: pointer; stroke: var(--surface); stroke-width: 1; vector-effect: non-scaling-stroke; }}
.map-pin:hover {{ stroke-width: 1.75; }}
.map-pin[data-applied="1"] {{ opacity: 0.35; }}
.map-ref-ring {{ fill: none; stroke: var(--line); stroke-dasharray: 4 4; vector-effect: non-scaling-stroke; }}
.map-ref-pin {{ fill: var(--accent); stroke: var(--surface); stroke-width: 1.5; vector-effect: non-scaling-stroke; }}

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
      </select>
      <div class="view-toggle">
        <button class="view-btn" data-view="list" data-active="1">List</button>
        <button class="view-btn" data-view="map" data-active="0">Map</button>
      </div>
      <a class="sheet-btn" href="{SHEET_URL}" target="_blank" rel="noopener">Sheet</a>
    </div>
    <div class="chip-row" id="groupChips"></div>
    <div class="chip-row" id="suburbChips"></div>
  </div>
</div>

<div class="wrap">
  <div class="count-row">
    <span id="countLabel"></span>
    <span id="appliedLabel"></span>
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
      <svg id="mapSvg" xmlns="http://www.w3.org/2000/svg"></svg>
    </div>
    <div class="map-info" id="mapInfo">
      <p class="map-info-empty">tap a pin to see who they are &#128205;</p>
    </div>
  </div>
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

const state = {{ q: "", group: "All", suburb: "All", sort: "dist", visible: 40, view: "list" }};
const PAGE = 40;
const applied = new Set(JSON.parse(localStorage.getItem("bundoora_applied") || "[]"));

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

function encouragementFor(n) {{
  if (n === 0) return "no applications yet &mdash; let's find your first &#10024;";
  if (n < 3) return `${{n}} sent &mdash; great start!`;
  if (n < 6) return `${{n}} sent &mdash; you're on a roll &#128293;`;
  if (n < 10) return `${{n}} sent &mdash; go get 'em!`;
  return `${{n}} sent &mdash; unstoppable &#127881;`;
}}

function saveApplied() {{
  localStorage.setItem("bundoora_applied", JSON.stringify([...applied]));
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
  if (state.q) {{
    const q = state.q.toLowerCase();
    rows = rows.filter((d) => d.name.toLowerCase().includes(q));
  }}
  rows = rows.slice();
  if (state.sort === "dist") rows.sort((a, b) => (a.dist ?? 1e9) - (b.dist ?? 1e9));
  else if (state.sort === "name") rows.sort((a, b) => a.name.localeCompare(b.name));
  else if (state.sort === "rating") rows.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
  return rows;
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

const CHECK_SVG =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5l3.2 3.2L13 5"/></svg>';
const STAR_SVG =
  '<svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 1.6l2.47 5.24 5.63.78-4.08 4.06.99 5.72L10 14.5l-5.01 2.9.99-5.72L1.9 7.62l5.63-.78L10 1.6z"/></svg>';
function ratingChip(rating) {{
  if (!rating) return "";
  return `<span class="rating">${{STAR_SVG}}${{rating}}</span>`;
}}

function card(d) {{
  const k = catColorVar(d.grp);
  const isApplied = applied.has(d.id);
  const phoneHtml = d.phone
    ? `<a class="btn primary" href="tel:${{d.phone.replace(/[^+\\d]/g, "")}}">Call ${{d.phone}}</a>`
    : `<span class="btn disabled">No phone listed</span>`;
  const siteHtml = d.site ? `<a class="btn" href="${{d.site}}" target="_blank" rel="noopener">Website</a>` : "";
  return `
  <div class="card" data-applied="${{isApplied ? 1 : 0}}">
    <div class="card-top">
      <div class="card-name">${{d.name}}</div>
      <button class="applied-btn" data-id="${{d.id}}" aria-pressed="${{isApplied}}" aria-label="Mark as applied" title="Mark as applied">${{CHECK_SVG}}</button>
    </div>
    <div class="tag-row">
      <span class="tag" style="background:var(--cat-${{k}}-bg);color:var(--cat-${{k}})">${{d.cat}}</span>
      <span class="tag suburb">${{d.suburb}}</span>
      ${{ratingChip(d.rating)}}
      <span class="dist-badge">${{d.dist != null ? d.dist.toFixed(1) + " km" : ""}}</span>
    </div>
    <div class="addr">${{d.addr}}</div>
    <div class="action-row">
      ${{phoneHtml}}
      <a class="btn" href="${{mapsUrl(d)}}" target="_blank" rel="noopener">Directions</a>
      ${{siteHtml}}
    </div>
  </div>`;
}}

function setApplied(id, nowApplied) {{
  if (nowApplied) applied.add(id);
  else applied.delete(id);
  saveApplied();
  document.getElementById("appliedLabel").innerHTML = encouragementFor(applied.size);
}}

function render() {{
  const rows = filtered();
  document.getElementById("emptyState").style.display = rows.length ? "none" : "block";
  document.getElementById("appliedLabel").innerHTML = encouragementFor(applied.size);
  if (state.view === "map") {{
    document.getElementById("countLabel").textContent = `${{rows.length}} pinned`;
    renderMap(rows);
  }} else {{
    renderList(rows);
  }}
}}

function renderList(rows) {{
  const grid = document.getElementById("grid");
  const slice = rows.slice(0, state.visible);
  grid.innerHTML = slice.map(card).join("");
  document.getElementById("countLabel").textContent = `showing ${{slice.length}} of ${{rows.length}}`;
  document.getElementById("loadMoreRow").style.display = rows.length > slice.length ? "flex" : "none";

  grid.querySelectorAll(".applied-btn").forEach((btn) =>
    btn.addEventListener("click", () => {{
      const id = btn.dataset.id;
      const nowApplied = !applied.has(id);
      setApplied(id, nowApplied);
      btn.setAttribute("aria-pressed", String(nowApplied));
      btn.closest(".card").dataset.applied = nowApplied ? "1" : "0";
    }})
  );
}}

/* ---- Map view: self-contained SVG scatter plot (no external tiles —
   Artifact pages can't load remote map imagery), projected as a flat
   local approximation since the whole dataset spans ~10km. ---- */
const REF = {{ lat: -37.7000101, lng: 145.0615908 }};
const KM_PER_DEG_LAT = 110.574;
function kmPerDegLng(lat) {{ return 111.320 * Math.cos((lat * Math.PI) / 180); }}
function project(lat, lng) {{
  return {{
    x: (lng - REF.lng) * kmPerDegLng(REF.lat),
    y: (REF.lat - lat) * KM_PER_DEG_LAT,
  }};
}}

let mapBuilt = false;
let viewBox = {{ x: -6, y: -6, w: 12, h: 12 }};
const svgEl = () => document.getElementById("mapSvg");

function applyViewBox() {{
  svgEl().setAttribute("viewBox", `${{viewBox.x}} ${{viewBox.y}} ${{viewBox.w}} ${{viewBox.h}}`);
}}

function fitViewBoxToData() {{
  const pts = DATA.map((d) => project(d.lat, d.lng));
  const xs = pts.map((p) => p.x).concat([0]);
  const ys = pts.map((p) => p.y).concat([0]);
  const minX = Math.min(...xs) - 1, maxX = Math.max(...xs) + 1;
  const minY = Math.min(...ys) - 1, maxY = Math.max(...ys) + 1;
  viewBox = {{ x: minX, y: minY, w: maxX - minX, h: maxY - minY }};
}}

const LEGEND = [
  ["Hospo", "food"],
  ["Grocery", "grocery"],
  ["Retail", "retail"],
  ["Health", "health"],
  ["Fitness", "fitness"],
  ["Family", "family"],
];
function renderLegend() {{
  document.getElementById("mapLegend").innerHTML = LEGEND.map(
    ([label, k]) => `<span class="lg-item"><span class="lg-dot" style="background:var(--cat-${{k}})"></span>${{label}}</span>`
  ).join("");
}}

function mapInfoHtml(d) {{
  const isApplied = applied.has(d.id);
  const phoneHtml = d.phone
    ? `<a class="btn primary" href="tel:${{d.phone.replace(/[^+\\d]/g, "")}}">Call ${{d.phone}}</a>`
    : `<span class="btn disabled">No phone listed</span>`;
  const siteHtml = d.site ? `<a class="btn" href="${{d.site}}" target="_blank" rel="noopener">Website</a>` : "";
  const k = catColorVar(d.grp);
  return `
    <div class="card-top">
      <div class="card-name">${{d.name}}</div>
      <button class="applied-btn" data-id="${{d.id}}" aria-pressed="${{isApplied}}" aria-label="Mark as applied" title="Mark as applied">${{CHECK_SVG}}</button>
    </div>
    <div class="tag-row">
      <span class="tag" style="background:var(--cat-${{k}}-bg);color:var(--cat-${{k}})">${{d.cat}}</span>
      <span class="tag suburb">${{d.suburb}}</span>
      <span class="dist-badge">${{d.dist != null ? d.dist.toFixed(1) + " km" : ""}}</span>
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
  info.querySelector(".applied-btn").addEventListener("click", (e) => {{
    const btn = e.currentTarget;
    const nowApplied = !applied.has(d.id);
    setApplied(d.id, nowApplied);
    btn.setAttribute("aria-pressed", String(nowApplied));
    const pin = svgEl().querySelector(`.map-pin[data-id="${{CSS.escape(d.id)}}"]`);
    if (pin) pin.dataset.applied = nowApplied ? "1" : "0";
  }});
}}

function renderMap(rows) {{
  renderLegend();
  if (!mapBuilt) {{
    fitViewBoxToData();
    applyViewBox();
    wireMapInteractions();
    mapBuilt = true;
  }}
  const r = 0.09;
  const refPt = project(REF.lat, REF.lng);
  const pins = rows
    .map((d) => {{
      const p = project(d.lat, d.lng);
      const k = catColorVar(d.grp);
      const isApplied = applied.has(d.id) ? 1 : 0;
      return `<circle class="map-pin" data-id="${{d.id}}" data-applied="${{isApplied}}" cx="${{p.x.toFixed(4)}}" cy="${{p.y.toFixed(4)}}" r="${{r}}" fill="var(--cat-${{k}})"><title>${{d.name}}</title></circle>`;
    }})
    .join("");
  const rings = [2, 5, 10]
    .map((km) => `<circle class="map-ref-ring" cx="${{refPt.x}}" cy="${{refPt.y}}" r="${{km}}"></circle>`)
    .join("");
  svgEl().innerHTML = `${{rings}}${{pins}}<circle class="map-ref-pin" cx="${{refPt.x}}" cy="${{refPt.y}}" r="0.16"><title>566 Grimshaw Street (you are here)</title></circle>`;

  svgEl().querySelectorAll(".map-pin").forEach((pin) =>
    pin.addEventListener("click", () => {{
      const d = DATA.find((x) => x.id === pin.dataset.id);
      if (d) showMapInfo(d);
    }})
  );
}}

function zoomBy(factor, cx, cy) {{
  const nw = viewBox.w * factor;
  const nh = viewBox.h * factor;
  viewBox = {{
    x: cx - (cx - viewBox.x) * factor,
    y: cy - (cy - viewBox.y) * factor,
    w: nw,
    h: nh,
  }};
  applyViewBox();
}}

function wireMapInteractions() {{
  const svg = svgEl();
  let dragging = false;
  let last = {{ x: 0, y: 0 }};

  svg.addEventListener("wheel", (e) => {{
    e.preventDefault();
    const rect = svg.getBoundingClientRect();
    const px = viewBox.x + ((e.clientX - rect.left) / rect.width) * viewBox.w;
    const py = viewBox.y + ((e.clientY - rect.top) / rect.height) * viewBox.h;
    zoomBy(e.deltaY > 0 ? 1.15 : 0.87, px, py);
  }}, {{ passive: false }});

  svg.addEventListener("pointerdown", (e) => {{
    dragging = true;
    last = {{ x: e.clientX, y: e.clientY }};
    svg.setPointerCapture(e.pointerId);
  }});
  svg.addEventListener("pointermove", (e) => {{
    if (!dragging) return;
    const rect = svg.getBoundingClientRect();
    const dx = ((e.clientX - last.x) / rect.width) * viewBox.w;
    const dy = ((e.clientY - last.y) / rect.height) * viewBox.h;
    viewBox = {{ ...viewBox, x: viewBox.x - dx, y: viewBox.y - dy }};
    last = {{ x: e.clientX, y: e.clientY }};
    applyViewBox();
  }});
  ["pointerup", "pointercancel", "pointerleave"].forEach((ev) =>
    svg.addEventListener(ev, () => {{ dragging = false; }})
  );

  document.getElementById("zoomInBtn").addEventListener("click", () =>
    zoomBy(0.8, viewBox.x + viewBox.w / 2, viewBox.y + viewBox.h / 2)
  );
  document.getElementById("zoomOutBtn").addEventListener("click", () =>
    zoomBy(1.25, viewBox.x + viewBox.w / 2, viewBox.y + viewBox.h / 2)
  );
  document.getElementById("zoomResetBtn").addEventListener("click", () => {{
    fitViewBoxToData();
    applyViewBox();
  }});
}}

document.querySelectorAll(".view-btn").forEach((btn) =>
  btn.addEventListener("click", () => {{
    state.view = btn.dataset.view;
    document.querySelectorAll(".view-btn").forEach((b) => (b.dataset.active = b === btn ? "1" : "0"));
    const isMap = state.view === "map";
    document.getElementById("grid").style.display = isMap ? "none" : "grid";
    document.getElementById("mapSection").style.display = isMap ? "block" : "none";
    document.getElementById("loadMoreRow").style.display = isMap ? "none" : document.getElementById("loadMoreRow").style.display;
    render();
  }})
);

document.getElementById("search").addEventListener("input", (e) => {{
  state.q = e.target.value.trim();
  state.visible = PAGE;
  render();
}});
document.getElementById("sortSel").addEventListener("change", (e) => {{
  state.sort = e.target.value;
  render();
}});
document.getElementById("loadMoreBtn").addEventListener("click", () => {{
  state.visible += PAGE;
  render();
}});

pickCheer();
renderChips();
render();
</script>
"""

out = BASE / "site.html"
out.write_text(HTML, encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
