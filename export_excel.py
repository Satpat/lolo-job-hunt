#!/usr/bin/env python3
"""
Convert data/businesses.json into a CSV and an Excel workbook for Lolo to
track applications. The .xlsx keeps an AutoFilter on the header row, which
Google Sheets preserves as a native filter when the file is uploaded/converted.

Usage:
    python3 export_excel.py
"""

import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

BASE = Path(__file__).parent
DATA_JSON = BASE / "data" / "businesses.json"
CSV_OUT = BASE / "data" / "businesses.csv"
XLSX_OUT = BASE / "Bundoora_Business_Directory.xlsx"

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

CATEGORY_DISPLAY = {
    "Retail (general)": "Retail",
    "Restaurant/Takeaway": "Restaurant",
    "Salon/Beauty": "Beauty",
}

COLUMNS = [
    "Business Name",
    "Group",
    "Category",
    "Suburb",
    "Distance (km)",
    "Address",
    "Phone",
    "Website",
    "Hours",
    "Applied?",
    "Notes",
]


def load_data():
    if not DATA_JSON.exists():
        raise SystemExit(f"Missing {DATA_JSON} - run fetch_businesses.py first.")
    return json.loads(DATA_JSON.read_text())


def to_row(b: dict) -> list:
    hours = "; ".join(b.get("opening_hours") or []) if b.get("opening_hours") else ""
    cat = b.get("category") or ""
    return [
        b.get("name") or "",
        GROUP_OF.get(cat, ""),
        CATEGORY_DISPLAY.get(cat, cat),
        b.get("suburb") or "",
        b.get("distance_km"),
        b.get("address") or "",
        b.get("phone") or "",
        b.get("website") or "",
        hours,
        "",  # Applied?
        "",  # Notes
    ]


def write_csv(rows):
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"Wrote {CSV_OUT}")


def write_xlsx(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Bundoora Directory"

    ws.append(COLUMNS)
    header_fill = PatternFill(start_color="8E2A52", end_color="8E2A52", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for col_idx in range(1, len(COLUMNS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font

    for row in rows:
        ws.append(row)

    widths = [28, 20, 18, 16, 12, 40, 16, 30, 45, 10, 30]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}{len(rows) + 1}"

    wb.save(XLSX_OUT)
    print(f"Wrote {XLSX_OUT}")


def main():
    data = load_data()
    data.sort(key=lambda b: (b.get("distance_km") is None, b.get("distance_km"), b.get("name") or ""))
    rows = [to_row(b) for b in data]
    write_csv(rows)
    write_xlsx(rows)
    print(f"Total businesses: {len(rows)}")


if __name__ == "__main__":
    main()
