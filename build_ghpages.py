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
    "Cafe": "Food & Drink",
    "Restaurant/Takeaway": "Food & Drink",
    "Fast Food": "Food & Drink",
    "Supermarket": "Supermarket & Grocery",
    "Retail": "Retail",
    "Retail (general)": "Retail",
    "Medical Clinic": "Health & Wellness",
    "Hospital": "Health & Wellness",
    "Dentist": "Health & Wellness",
    "Allied Health": "Health & Wellness",
    "Pharmacy": "Health & Wellness",
    "Gym": "Fitness & Beauty",
    "Salon/Beauty": "Fitness & Beauty",
    "Childcare": "Family & Leisure",
    "Cinema": "Family & Leisure",
}

GROUP_ORDER = [
    "Food & Drink",
    "Supermarket & Grocery",
    "Retail",
    "Health & Wellness",
    "Fitness & Beauty",
    "Family & Leisure",
]

CAT_HEX = {
    "food": "#c2447a",
    "grocery": "#b33f93",
    "retail": "#8465c7",
    "health": "#6b3f76",
    "fitness": "#9c2255",
    "family": "#7a1f3d",
}
ACCENT_HEX = "#8e2a52"

slim = []
for d in DATA:
    cat = d["category"]
    if cat == "Retail (general)":
        cat = "Retail"
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
  padding: 0 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
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

.chip-row {{
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
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
  border-radius: 5px;
  letter-spacing: 0.01em;
}}
.tag.suburb {{
  background: var(--surface-2);
  color: var(--ink-dim);
  border: 1px solid var(--line-soft);
  font-weight: 500;
}}
.addr {{ color: var(--ink-dim); font-size: 13px; }}
.rating {{ font-family: var(--font-mono); font-size: 12px; color: var(--ink-faint); }}

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
.map-legend .lg-line {{ width: 14px; height: 2px; flex: 0 0 auto; margin-top: 1px; }}
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
  <p class="eyebrow">Lolo Job Hunt &middot; near RMIT Bundoora</p>
  <h1>Go get 'em, Lolo &#128156;</h1>
  <p class="sub">
    <b>{TOTAL:,} places</b> within a tram, train or bus ride of RMIT Bundoora that actually
    hire casual and part-time staff &mdash; sorted nearest-first from
    <b>566 Grimshaw Street, Bundoora</b>. Every application is one step closer.
  </p>
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
      <div id="gmap"></div>
    </div>
    <div class="map-info" id="mapInfo">
      <p class="map-info-empty">tap a pin to see who they are &#128205;</p>
    </div>
  </div>
</div>

<footer>
  Data pulled from Google Places API (New), {TOTAL:,} operational listings across Bundoora,
  Reservoir, Preston, Thomastown, Epping, South Morang, Mill Park, Watsonia, Macleod
  and Greensborough &mdash; suburbs with a direct tram, train or SmartBus link to Bundoora.
  Map shows live transit routes via Google Maps. Built for Lolo's job hunt.
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
      "Food & Drink": "food",
      "Supermarket & Grocery": "grocery",
      Retail: "retail",
      "Health & Wellness": "health",
      "Fitness & Beauty": "fitness",
      "Family & Leisure": "family",
    }}[grp] || "food"
  );
}}

function mapsUrl(d) {{
  if (d.lat && d.lng) return `https://www.google.com/maps/search/?api=1&query=${{d.lat}},${{d.lng}}`;
  return `https://www.google.com/maps/search/?api=1&query=${{encodeURIComponent(d.addr)}}`;
}}

const CHECK_SVG =
  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8.5l3.2 3.2L13 5"/></svg>';

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
      ${{d.rating ? `<span class="rating">&#9733; ${{d.rating}}</span>` : ""}}
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

/* ---- Map view: real Google Maps JS SDK — street basemap + live transit
   layer (tram/train/bus routes), category-coloured markers, clustered for
   performance across 1500+ points, plus a home pin at Lolo's address. ---- */
const LEGEND = [
  ["Food & Drink", "food"],
  ["Supermarket & Grocery", "grocery"],
  ["Retail", "retail"],
  ["Health & Wellness", "health"],
  ["Fitness & Beauty", "fitness"],
  ["Family & Leisure", "family"],
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
    origin: "Bundoora RMIT tram terminus, VIC",
    destination: "Northcote Plaza, Northcote VIC",
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
      opacity: applied.has(d.id) ? 0.45 : 1,
    }});
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
<script src="https://unpkg.com/@googlemaps/markerclusterer@2.5.3/dist/index.min.js"></script>
<script async defer src="https://maps.googleapis.com/maps/api/js?key={GMAPS_KEY}&callback=initMap&loading=async"></script>
"""

out = BASE / "index.html"
out.write_text(HTML, encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
