"""
Build a CSV summary of all UAE occupations from scraped HTML files.

Reads from html/<slug>.html (MOHRE/FCSC/career pages), writes to occupations.csv.

UAE-specific fields:
  - isco_code: ISCO-08 4-digit occupation code (used by MOHRE UAE)
  - sector: UAE economic sector (Finance, Construction, Hospitality, etc.)
  - median_pay_annual_aed: Median annual pay in AED
  - emiratisation_rate: % UAE national workforce (Emiratisation/Nafis data)

Data sources:
  - MOHRE: https://www.mohre.gov.ae/
  - FCSC: https://www.fcsc.gov.ae/
  - Wage Protection System / CBUAE data

Usage:
  uv run python make_csv.py
"""

import csv
import json
import os
import re
from bs4 import BeautifulSoup


def clean(text):
    return re.sub(r'\s+', ' ', text).strip()


def parse_aed_pay(value):
    """Parse pay in AED from MOHRE/FCSC data."""
    annual_aed = ""
    monthly_aed = ""
    value_clean = re.sub(r'[AEDaed,\s]', '', value)
    amounts = re.findall(r'[\d]+(?:\.\d+)?', value_clean)
    if "per year" in value.lower() or "annual" in value.lower():
        if amounts:
            annual_aed = amounts[0]
    elif "per month" in value.lower() or "monthly" in value.lower():
        if amounts:
            monthly_aed = amounts[0]
            annual_aed = str(round(float(monthly_aed) * 12))
    elif amounts:
        val = float(amounts[0])
        if val > 50000:
            annual_aed = amounts[0]
        else:
            monthly_aed = amounts[0]
            annual_aed = str(round(val * 12))
    return annual_aed, monthly_aed


def parse_outlook(value):
    m = re.match(r'(-?\d+)%\s*\((.+)\)', value)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r'(-?\d+)%', value)
    if m:
        return m.group(1), ""
    return "", value


def parse_number(value):
    cleaned = re.sub(r'[,\s]', '', str(value)).strip()
    if re.match(r'^-?\d+$', cleaned):
        return cleaned
    return value.strip()


def extract_occupation(html_path, occ_meta):
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    row = {
        "title": occ_meta["title"],
        "category": occ_meta["category"],
        "slug": occ_meta["slug"],
        "isco_code": occ_meta.get("isco_code", ""),
        "sector": occ_meta.get("sector", ""),
        "url": occ_meta.get("url", ""),
        "median_pay_annual_aed": "",
        "median_pay_monthly_aed": "",
        "entry_education": "",
        "num_jobs": "",
        "emiratisation_rate": "",
        "growth_outlook_pct": "",
        "growth_outlook_desc": "",
    }

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            field = clean(cells[0].get_text()).lower()
            value = clean(cells[1].get_text())
            if not value or value == "-":
                continue
            if any(k in field for k in ["salary", "pay", "wage", "earn", "aed"]):
                row["median_pay_annual_aed"], row["median_pay_monthly_aed"] = parse_aed_pay(value)
            elif any(k in field for k in ["education", "qualification"]):
                row["entry_education"] = value
            elif any(k in field for k in ["employment", "jobs", "workforce"]):
                row["num_jobs"] = parse_number(value)
            elif any(k in field for k in ["emiratisation", "nafis", "national"]):
                row["emiratisation_rate"] = value
            elif any(k in field for k in ["outlook", "growth", "projection"]):
                row["growth_outlook_pct"], row["growth_outlook_desc"] = parse_outlook(value)

    return row


def main():
    with open("occupations.json", encoding="utf-8") as f:
        occupations = json.load(f)

    fieldnames = [
        "title", "category", "slug", "isco_code", "sector",
        "median_pay_annual_aed", "median_pay_monthly_aed",
        "entry_education", "num_jobs", "emiratisation_rate",
        "growth_outlook_pct", "growth_outlook_desc",
        "url",
    ]

    rows = []
    missing = 0
    for occ in occupations:
        html_path = f"html/{occ['slug']}.html"
        if not os.path.exists(html_path):
            missing += 1
            row = {f: occ.get(f, "") for f in fieldnames}
            row.update({"median_pay_annual_aed": "", "median_pay_monthly_aed": "",
                        "entry_education": "", "num_jobs": "", "emiratisation_rate": "",
                        "growth_outlook_pct": "", "growth_outlook_desc": ""})
            rows.append(row)
            continue
        rows.append(extract_occupation(html_path, occ))

    with open("occupations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to occupations.csv (missing HTML: {missing})")
    for r in rows[:3]:
        pay = r['median_pay_annual_aed']
        print(f"  {r['title']}: AED {pay or 'unknown'}/yr, sector: {r['sector']}")


if __name__ == "__main__":
    main()
