"""
Parse UAE occupations using ISCO-08 (the international standard used by MOHRE UAE).

The UAE uses ISCO-08 (International Standard Classification of Occupations) adapted
for the UAE context, published by MOHRE (Ministry of Human Resources and Emiratisation).

ISCO-08 Structure:
  - 10 Major Groups (1-digit)
  - 43 Sub-Major Groups (2-digit)
  - 130 Minor Groups (3-digit)
  - 436 Unit Groups (4-digit)

Data sources:
  - UAE MOHRE: https://www.mohre.gov.ae/
  - FCSC Labour Force Survey: https://www.fcsc.gov.ae/
  - ILO ISCO-08: https://www.ilo.org/public/english/bureau/stat/isco/isco08/

Usage:
  uv run python parse_occupations.py
"""

from bs4 import BeautifulSoup
import json
import re

ISCO_MAJOR_GROUPS = {
    "1": "Managers",
    "2": "Professionals",
    "3": "Technicians and Associate Professionals",
    "4": "Clerical Support Workers",
    "5": "Service and Sales Workers",
    "6": "Skilled Agricultural, Forestry and Fishery Workers",
    "7": "Craft and Related Trades Workers",
    "8": "Plant and Machine Operators and Assemblers",
    "9": "Elementary Occupations",
    "0": "Armed Forces Occupations",
}

UAE_SECTORS = {
    "1": "Finance and Professional Services",
    "2": "Knowledge Economy",
    "3": "Technology and Engineering",
    "4": "Administration and Government",
    "5": "Hospitality and Retail",
    "6": "Agriculture (minimal)",
    "7": "Construction and Trades",
    "8": "Transport and Logistics",
    "9": "Domestic and Support Services",
    "0": "Defence",
}

def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return re.sub(r'-+', '-', slug)

def build_default_occupations():
    """
    Key UAE occupations from ISCO-08, weighted by UAE labour force composition.
    The UAE workforce is ~5.3M, dominated by expatriates (~88%),
    concentrated in construction, hospitality, retail, finance, and tech.
    """
    occupations = [
        # Major Group 1: Managers
        {"title": "Chief Executives and Senior Officials", "isco_code": "1111", "category": ISCO_MAJOR_GROUPS["1"], "sector": UAE_SECTORS["1"]},
        {"title": "Finance Managers", "isco_code": "1211", "category": ISCO_MAJOR_GROUPS["1"], "sector": UAE_SECTORS["1"]},
        {"title": "HR Managers", "isco_code": "1212", "category": ISCO_MAJOR_GROUPS["1"], "sector": UAE_SECTORS["1"]},
        {"title": "Hotel and Restaurant Managers", "isco_code": "1411", "category": ISCO_MAJOR_GROUPS["1"], "sector": UAE_SECTORS["5"]},
        {"title": "Retail and Wholesale Trade Managers", "isco_code": "1420", "category": ISCO_MAJOR_GROUPS["1"], "sector": UAE_SECTORS["5"]},
        {"title": "Real Estate Managers", "isco_code": "1219", "category": ISCO_MAJOR_GROUPS["1"], "sector": UAE_SECTORS["1"]},
        # Major Group 2: Professionals
        {"title": "Software and Applications Developers", "isco_code": "2512", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["3"]},
        {"title": "Database and Network Professionals", "isco_code": "2521", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["3"]},
        {"title": "AI and Data Scientists", "isco_code": "2511", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["2"]},
        {"title": "Medical Doctors", "isco_code": "2211", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["2"]},
        {"title": "Nursing Professionals", "isco_code": "2221", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["2"]},
        {"title": "Financial Analysts and Advisors", "isco_code": "2411", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["1"]},
        {"title": "Accountants", "isco_code": "2411", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["1"]},
        {"title": "Lawyers and Legal Professionals", "isco_code": "2611", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["1"]},
        {"title": "Civil Engineers", "isco_code": "2142", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["7"]},
        {"title": "Mechanical Engineers", "isco_code": "2144", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["3"]},
        {"title": "Petroleum Engineers", "isco_code": "2145", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["3"]},
        {"title": "Architects", "isco_code": "2161", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["7"]},
        {"title": "University Lecturers", "isco_code": "2310", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["2"]},
        {"title": "School Teachers", "isco_code": "2330", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["2"]},
        {"title": "Marketing and Public Relations Professionals", "isco_code": "2431", "category": ISCO_MAJOR_GROUPS["2"], "sector": UAE_SECTORS["2"]},
        # Major Group 3: Technicians and Associate Professionals
        {"title": "IT Operations Technicians", "isco_code": "3513", "category": ISCO_MAJOR_GROUPS["3"], "sector": UAE_SECTORS["3"]},
        {"title": "Financial Associate Professionals", "isco_code": "3311", "category": ISCO_MAJOR_GROUPS["3"], "sector": UAE_SECTORS["1"]},
        {"title": "Real Estate Agents", "isco_code": "3324", "category": ISCO_MAJOR_GROUPS["3"], "sector": UAE_SECTORS["1"]},
        {"title": "Nurses (Associate)", "isco_code": "3221", "category": ISCO_MAJOR_GROUPS["3"], "sector": UAE_SECTORS["2"]},
        {"title": "Sales Representatives", "isco_code": "3322", "category": ISCO_MAJOR_GROUPS["3"], "sector": UAE_SECTORS["5"]},
        # Major Group 4: Clerical Support Workers
        {"title": "General Office Clerks", "isco_code": "4110", "category": ISCO_MAJOR_GROUPS["4"], "sector": UAE_SECTORS["4"]},
        {"title": "Data Entry Clerks", "isco_code": "4132", "category": ISCO_MAJOR_GROUPS["4"], "sector": UAE_SECTORS["4"]},
        {"title": "Customer Information and Receptionists", "isco_code": "4221", "category": ISCO_MAJOR_GROUPS["4"], "sector": UAE_SECTORS["4"]},
        {"title": "Accounting and Bookkeeping Clerks", "isco_code": "4311", "category": ISCO_MAJOR_GROUPS["4"], "sector": UAE_SECTORS["1"]},
        # Major Group 5: Service and Sales Workers
        {"title": "Shop Salespersons", "isco_code": "5223", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        {"title": "Cooks", "isco_code": "5120", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        {"title": "Waiters", "isco_code": "5131", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        {"title": "Housekeeping and Hotel Staff", "isco_code": "5151", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        {"title": "Security Guards", "isco_code": "5414", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        {"title": "Personal Care Workers", "isco_code": "5321", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["2"]},
        {"title": "Call Centre Operators", "isco_code": "5244", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        {"title": "Hairdressers and Beauty Workers", "isco_code": "5141", "category": ISCO_MAJOR_GROUPS["5"], "sector": UAE_SECTORS["5"]},
        # Major Group 7: Craft and Trades Workers
        {"title": "Building Frame Workers and Construction Trades", "isco_code": "7112", "category": ISCO_MAJOR_GROUPS["7"], "sector": UAE_SECTORS["7"]},
        {"title": "Electricians and Electrical Fitters", "isco_code": "7411", "category": ISCO_MAJOR_GROUPS["7"], "sector": UAE_SECTORS["7"]},
        {"title": "Plumbers and Pipe Fitters", "isco_code": "7126", "category": ISCO_MAJOR_GROUPS["7"], "sector": UAE_SECTORS["7"]},
        {"title": "Welders and Flame Cutters", "isco_code": "7212", "category": ISCO_MAJOR_GROUPS["7"], "sector": UAE_SECTORS["7"]},
        {"title": "Vehicle Mechanics", "isco_code": "7231", "category": ISCO_MAJOR_GROUPS["7"], "sector": UAE_SECTORS["8"]},
        # Major Group 8: Plant and Machine Operators
        {"title": "Motor Vehicle Drivers", "isco_code": "8322", "category": ISCO_MAJOR_GROUPS["8"], "sector": UAE_SECTORS["8"]},
        {"title": "Taxi and Ride-Share Drivers", "isco_code": "8322", "category": ISCO_MAJOR_GROUPS["8"], "sector": UAE_SECTORS["8"]},
        {"title": "Crane and Hoist Operators", "isco_code": "8343", "category": ISCO_MAJOR_GROUPS["8"], "sector": UAE_SECTORS["7"]},
        {"title": "Assemblers", "isco_code": "8211", "category": ISCO_MAJOR_GROUPS["8"], "sector": UAE_SECTORS["3"]},
        # Major Group 9: Elementary Occupations
        {"title": "Construction Labourers", "isco_code": "9312", "category": ISCO_MAJOR_GROUPS["9"], "sector": UAE_SECTORS["7"]},
        {"title": "Domestic Workers and Household Helpers", "isco_code": "9111", "category": ISCO_MAJOR_GROUPS["9"], "sector": UAE_SECTORS["9"]},
        {"title": "Cleaners and Housekeepers", "isco_code": "9112", "category": ISCO_MAJOR_GROUPS["9"], "sector": UAE_SECTORS["9"]},
        {"title": "Delivery and Courier Workers", "isco_code": "9334", "category": ISCO_MAJOR_GROUPS["9"], "sector": UAE_SECTORS["8"]},
        {"title": "Food Preparation Assistants", "isco_code": "9411", "category": ISCO_MAJOR_GROUPS["9"], "sector": UAE_SECTORS["5"]},
        {"title": "Agricultural and Fishery Labourers", "isco_code": "9211", "category": ISCO_MAJOR_GROUPS["9"], "sector": UAE_SECTORS["6"]},
    ]

    for occ in occupations:
        occ["slug"] = slugify(occ["title"])
        if not occ.get("url"):
            occ["url"] = f"https://www.mohre.gov.ae/en/services/employment-services.aspx"

    return occupations


def main():
    import os

    if os.path.exists("mohre_index.html"):
        print("Parsing mohre_index.html...")
        with open("mohre_index.html", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        occupations = []
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                code = cells[0].get_text(strip=True)
                if re.match(r'^\d{4}$', code):
                    title = cells[1].get_text(strip=True)
                    occupations.append({
                        "title": title, "isco_code": code,
                        "category": ISCO_MAJOR_GROUPS.get(code[0], "Other"),
                        "sector": UAE_SECTORS.get(code[0], "Other"),
                        "slug": slugify(title),
                        "url": "https://www.mohre.gov.ae/",
                    })
        print(f"Parsed {len(occupations)} occupations")
    else:
        print("Using built-in UAE occupation list (ISCO-08 UAE-weighted).")
        print("For full MOHRE data, save mohre_index.html from: https://www.mohre.gov.ae/")
        occupations = build_default_occupations()

    occupations.sort(key=lambda x: (x["category"], x["title"]))

    from collections import Counter
    cats = Counter(o["category"] for o in occupations)
    print(f"Total: {len(occupations)} occupations")
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")

    with open("occupations.json", "w", encoding="utf-8") as f:
        json.dump(occupations, f, indent=2, ensure_ascii=False)
    print("Saved to occupations.json")


if __name__ == "__main__":
    main()
