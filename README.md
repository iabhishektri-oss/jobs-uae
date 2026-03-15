# AI Exposure of the UAE Job Market

Analyzing how susceptible every occupation in the UAE economy is to AI and automation, using data from the UAE Ministry of Human Resources and Emiratisation (MOHRE) and Federal Competitiveness and Statistics Centre (FCSC).

![AI Exposure Treemap](jobs.png)

## What's here

The UAE has a unique labour market with over 88% expatriate workforce across diverse sectors including oil & gas, finance, construction, tourism, and a fast-growing tech sector. We compile occupation data from official UAE government sources, score each occupation's AI exposure, and build an interactive treemap visualization.

## Data Sources (UAE)

- [ISCO-08 UAE Adaptation](https://www.mohre.gov.ae/) - UAE uses the International Standard Classification of Occupations (ISCO-08) adapted for the UAE context, published by MOHRE
- [UAE FCSC Labour Force Survey](https://www.fcsc.gov.ae/) - Federal Competitiveness and Statistics Centre annual labour force data
- [UAE Vision 2031 / Occupational Demand Forecasts](https://www.uaevision2031.ae/) - Forward-looking employment projections
- [KHDA / Abu Dhabi DOE](https://www.khda.gov.ae/) - Skills and qualification standards for UAE occupations
- [CBUAE Wage Protection System Data](https://www.centralbank.ae/) - Wage data by occupation sector

## Data pipeline

1. Scrape (scrape.py) - Downloads raw HTML from MOHRE, FCSC and related UAE government sources into html/
2. Parse (parse_detail.py, process.py) - Converts HTML into clean Markdown in pages/
3. Tabulate (make_csv.py) - Extracts pay in AED, education, job count, growth outlook, ISCO code into occupations.csv
4. Score (score.py) - Sends each occupation to an LLM with a UAE-calibrated scoring rubric. Results in scores.json
5. Build site data (build_site_data.py) - Merges CSV and scores into site/data.json
6. Website (site/index.html) - Interactive treemap: area = employment, colour = AI exposure

## Key files

| File | Description |
|------|-------------|
| occupations.json | Master list with title, URL, ISCO code, category, slug |
| occupations.csv | Stats: pay (AED), education, job count, Emiratisation rate |
| scores.json | AI exposure scores (0-10) with rationales |
| html/ | Raw HTML from MOHRE/FCSC (source of truth) |
| pages/ | Clean Markdown per occupation |
| site/ | Static treemap website |

## AI exposure scoring

Each occupation is scored 0-10 for AI Exposure in the UAE context. The UAE has a unique labour market profile:

- The UAE is aggressively pursuing AI adoption as part of UAE AI Strategy 2031 and has one of the highest AI investment rates per capita globally
- Dubai and Abu Dhabi are regional fintech, logistics, and tech hubs with very high AI adoption rates
- The large construction and hospitality sectors (dominated by migrant labour) have low AI exposure for manual work
- The Emiratisation policy (Nafis programme) incentivises hiring UAE nationals in white-collar roles increasingly targeted by AI
- The oil and gas sector is investing heavily in AI for operations, raising exposure for technical and managerial roles
- A significant proportion of the workforce is in retail, hospitality, and domestic services with moderate AI exposure

Calibration examples (UAE):

| Score | Meaning | Examples |
|-------|---------|---------|
| 0-1 | Minimal | Construction labourers, domestic workers, agricultural workers |
| 2-3 | Low | Electricians, plumbers, chefs, security guards |
| 4-5 | Moderate | Nurses, retail managers, hotel staff supervisors, teachers |
| 6-7 | High | Engineers, bank managers, accountants, HR professionals |
| 8-9 | Very high | Software developers, financial analysts, legal professionals, data scientists |
| 10 | Maximum | Data entry clerks, call centre agents, document processing clerks |

## Visualization

The main visualization is an interactive treemap where:
- Area of each rectangle is proportional to employment (number of jobs)
- Colour indicates AI exposure on a green (safe) to red (exposed) scale
- Layout groups occupations by ISCO major group / UAE sector
- Hover shows detailed tooltip with pay (AED), jobs, Emiratisation rate, education, exposure score

## Setup

uv sync
uv run playwright install chromium

Requires OPENROUTER_API_KEY in .env

## Usage

uv run python scrape.py
uv run python process.py
uv run python make_csv.py
uv run python score.py
uv run python build_site_data.py
cd site && python -m http.server 8000

## Differences from the US version

| Aspect | US (karpathy/jobs) | UAE (this repo) |
|--------|-------------------|----------------|
| Data source | BLS OOH | MOHRE + FCSC + ISCO-08 UAE |
| Occupation codes | BLS SOC | ISCO-08 (UN standard) |
| Pay data | USD annual | AED annual / monthly |
| Workforce context | ~165M US workers | ~5M UAE workforce (88% expats) |
| Projections | BLS 10-year | UAE Vision 2031 forecasts |
| Scraping target | bls.gov/ooh | mohre.gov.ae / fcsc.gov.ae |
