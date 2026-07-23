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
