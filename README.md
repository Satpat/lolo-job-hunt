# Bundoora Business Directory

A directory of businesses in Bundoora VIC 3083 that typically hire casual/part-time
staff (cafes, restaurants, retail, supermarkets, gyms, pharmacies, salons,
childcare, cinemas, healthcare) — built to help with job hunting.

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
  column for tracking applications
- A shareable web page is published separately as a Claude Artifact once the
  data is fetched.
