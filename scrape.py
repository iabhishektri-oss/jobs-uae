"""
Scrape MOHRE / FCSC UAE occupation detail pages (raw HTML).

Saves raw HTML to html/<slug>.html as the source of truth.
Run make_csv.py afterwards to parse the HTML into occupations.csv.

Data sources:
  - MOHRE (Ministry of Human Resources & Emiratisation): https://www.mohre.gov.ae/
  - FCSC (Federal Competitiveness and Statistics Centre): https://www.fcsc.gov.ae/
  - ISCO-08 UAE adaptation: https://www.ilo.org/public/english/bureau/stat/isco/isco08/

Usage:
    uv run python scrape.py                   # scrape all occupations
    uv run python scrape.py --start 0 --end 5 # scrape first 5
    uv run python scrape.py --start 10 --end 20 # scrape indices 10-19
    uv run python scrape.py --force           # re-scrape ignoring cache

Caching: skips any occupation where html/<slug>.html already exists.
"""

import argparse
import json
import os
import time
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Main scraper
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Scrape MOHRE/FCSC UAE occupation pages")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end",   type=int, default=None, help="End index (exclusive)")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if cached")
    args = parser.parse_args()

    # Load occupation list from parse_occupations.py output
    from parse_occupations import get_occupations
    occupations = get_occupations()

    subset = occupations[args.start : args.end]
    print(f"Scraping {len(subset)} of {len(occupations)} UAE occupations "
          f"(indices {args.start}..{args.end or len(occupations)-1})")

    os.makedirs("html", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="en-AE",
            extra_http_headers={
                "Accept-Language": "ar,en;q=0.9,en-AE;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        page = context.new_page()

        for i, occ in enumerate(subset):
            slug = occ["slug"]
            out_path = os.path.join("html", f"{slug}.html")

            if not args.force and os.path.exists(out_path):
                print(f"  [{i+1}/{len(subset)}] SKIP (cached): {slug}")
                continue

            url = occ.get("url", f"https://www.mohre.gov.ae/en/careers/{slug}")
            print(f"  [{i+1}/{len(subset)}] Fetching: {url}")

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                html = page.content()
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"    Saved {len(html):,} bytes -> {out_path}")
            except Exception as e:
                print(f"    ERROR: {e}")
                # Save error placeholder so we can retry with --force
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(f"<!-- ERROR: {e} -->")

            # Polite delay to avoid rate-limiting
            time.sleep(1.5)

        browser.close()

    print("Done.")


if __name__ == "__main__":
    main()
