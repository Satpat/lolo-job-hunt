#!/usr/bin/env python3
"""
Fetch job-relevant businesses in Bundoora VIC 3083 and nearby suburbs with
direct public transport access to Bundoora/La Trobe University, using the
Google Places API (New). Results are tagged with straight-line distance
(km) from a reference address.

Requires env var GOOGLE_PLACES_API_KEY.

Usage:
    export GOOGLE_PLACES_API_KEY=your_key_here
    python3 fetch_businesses.py
"""

import json
import math
import os
import sys
import time
from pathlib import Path

import requests

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
if not API_KEY:
    sys.exit("ERROR: set GOOGLE_PLACES_API_KEY environment variable first.")

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
REFERENCE_ADDRESS = "566 Grimshaw Street, Bundoora, VIC 3083, Australia"

FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.types",
        "places.regularOpeningHours",
        "places.websiteUri",
        "places.rating",
        "places.location",
        "places.businessStatus",
    ]
)

# category label -> search term (suburb is appended per-suburb at query time)
CATEGORY_TERMS = {
    "Cafe": "cafe",
    "Restaurant/Takeaway": "restaurant",
    "Fast Food": "fast food",
    "Retail": "clothing store",
    "Retail (general)": "retail store",
    "Supermarket": "supermarket",
    "Gym": "gym",
    "Pharmacy": "pharmacy",
    "Salon/Beauty": "hair salon",
    "Childcare": "childcare",
    "Cinema": "cinema",
    "Medical Clinic": "medical clinic",
    "Hospital": "hospital",
    "Dentist": "dentist",
    "Allied Health": "allied health",
}

# Suburbs with a direct, low-transfer public transport link to Bundoora /
# La Trobe University (tram 86, Mernda/Hurstbridge train lines, or the 903
# SmartBus orbital that runs through Bundoora), each with its own postcode
# for address filtering.
SUBURBS = [
    ("Bundoora", "3083"),
    ("Reservoir", "3073"),
    ("Preston", "3072"),
    ("Thomastown", "3074"),
    ("Epping", "3076"),
    ("South Morang", "3752"),
    ("Mill Park", "3082"),
    ("Watsonia", "3087"),
    ("Macleod", "3085"),
    ("Greensborough", "3088"),
]


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def places_request(query: str) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": query, "regionCode": "AU"}
    resp = requests.post(SEARCH_URL, headers=headers, json=body, timeout=30)
    if resp.status_code != 200:
        print(f"  ! {query}: HTTP {resp.status_code} - {resp.text[:300]}")
        return []
    return resp.json().get("places", [])


def get_reference_point() -> tuple[float, float]:
    places = places_request(REFERENCE_ADDRESS)
    if not places:
        sys.exit("ERROR: could not geocode reference address via Places API.")
    loc = places[0]["location"]
    print(f"Reference point ({REFERENCE_ADDRESS}): {loc['latitude']}, {loc['longitude']}")
    return loc["latitude"], loc["longitude"]


def search_category(label: str, suburb: str, postcode: str) -> list[dict]:
    term = CATEGORY_TERMS[label]
    query = f"{term} in {suburb} VIC {postcode}"
    places = places_request(query)
    # Match on "VIC <postcode>" specifically (not a bare suburb-name substring,
    # which false-positives on street names like "Macleod St, Bairnsdale").
    postcode_marker = f"vic {postcode}"
    results = []
    for p in places:
        addr = (p.get("formattedAddress") or "").lower()
        if postcode_marker not in addr:
            continue
        results.append(
            {
                "place_id": p.get("id"),
                "name": p.get("displayName", {}).get("text"),
                "category": label,
                "suburb": suburb,
                "types": p.get("types", []),
                "address": p.get("formattedAddress"),
                "phone": p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber"),
                "website": p.get("websiteUri"),
                "rating": p.get("rating"),
                "business_status": p.get("businessStatus"),
                "opening_hours": (p.get("regularOpeningHours") or {}).get("weekdayDescriptions"),
                "lat": (p.get("location") or {}).get("latitude"),
                "lng": (p.get("location") or {}).get("longitude"),
            }
        )
    return results


def main():
    ref_lat, ref_lng = get_reference_point()
    time.sleep(0.2)

    all_places: dict[str, dict] = {}
    for suburb, postcode in SUBURBS:
        for label in CATEGORY_TERMS:
            print(f"Searching: {label} in {suburb}")
            results = search_category(label, suburb, postcode)
            print(f"  -> {len(results)}")
            for r in results:
                pid = r["place_id"]
                if pid not in all_places:
                    all_places[pid] = r
            time.sleep(0.15)

    for r in all_places.values():
        if r.get("lat") is not None and r.get("lng") is not None:
            r["distance_km"] = round(haversine_km(ref_lat, ref_lng, r["lat"], r["lng"]), 2)
        else:
            r["distance_km"] = None

    ordered = sorted(
        all_places.values(),
        key=lambda r: (r["distance_km"] is None, r["distance_km"]),
    )

    out_dir = Path(__file__).parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_json = out_dir / "businesses.json"
    out_json.write_text(json.dumps(ordered, indent=2))

    print(f"\nTotal unique businesses: {len(ordered)}")
    print(f"Saved to {out_json}")


if __name__ == "__main__":
    main()
