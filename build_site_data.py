"""
Build compact JSON for the website merging CSV stats with AI exposure scores.
UAE version: outputs pay in AED, ISCO-08 codes, MOHRE/FCSC employment data.

Usage: uv run python build_site_data.py
"""

import csv
import json
import os
from collections import Counter


def main():
    with open("scores.json", encoding="utf-8") as f:
        scores_list = json.load(f)
    scores = {s["slug"]: s for s in scores_list}

    with open("occupations.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    data = []
    for row in rows:
        slug = row["slug"]
        score = scores.get(slug, {})

        entry = {
            "slug": slug,
            "title": row.get("title", ""),
            "isco_code": row.get("isco_code", ""),
            "sector": row.get("sector", ""),
            "pay_aed": row.get("median_pay_annual_aed", ""),
            "emiratisation_rate": row.get("emiratisation_rate", ""),
            "ai_impact": score.get("ai_impact", ""),
            "automation_risk": score.get("automation_risk", ""),
            "augmentation_potential": score.get("augmentation_potential", ""),
            "timeline": score.get("timeline", ""),
            "reasoning": score.get("reasoning", ""),
        }
        data.append(entry)

    # Summary stats
    ai_impacts = [d["ai_impact"] for d in data if d["ai_impact"]]
    impact_counts = Counter(ai_impacts)

    site_data = {
        "occupations": data,
        "stats": {
            "total": len(data),
            "by_ai_impact": dict(impact_counts),
        },
    }

    os.makedirs("site", exist_ok=True)
    out_path = os.path.join("site", "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(site_data, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(data)} occupations to {out_path}")
    print("AI impact breakdown:")
    for label, count in sorted(impact_counts.items()):
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
