"""
Score each UAE occupation's AI exposure using an LLM via OpenRouter.

Reads Markdown descriptions from pages/, sends each to an LLM with a
scoring rubric calibrated for the UAE job market. Results cached in scores.json.

Usage:
  uv run python score.py
  uv run python score.py --model google/gemini-3-flash-preview
  uv run python score.py --start 0 --end 10
"""

import argparse
import json
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "google/gemini-3-flash-preview"
OUTPUT_FILE = "scores.json"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are an expert analyst evaluating how exposed different occupations in the United Arab Emirates (UAE) are to AI and automation. You will be given a description of a UAE occupation from official sources (MOHRE, FCSC, or ISCO-08).

Rate the occupation's overall AI Exposure on a scale from 0 to 10.

AI Exposure measures: how much will AI reshape this occupation in the UAE over the next 5-10 years? Consider both direct automation and indirect effects.

UAE-specific context to consider:
- The UAE is one of the world's most aggressive AI adopters: the UAE AI Strategy 2031 targets making UAE a global AI leader, and the government mandates AI in many sectors
- Dubai and Abu Dhabi are regional hubs for fintech, logistics, and tech with very high rates of AI adoption already underway
- Over 88% of the UAE workforce is expatriate: economic disruption from AI affects visa status and residency, creating unique incentives for rapid automation
- The Nafis (Emiratisation) programme incentivises replacing expatriates with UAE nationals in white-collar roles - AI may accelerate this transition
- Oil and gas (ADNOC) is investing heavily in AI-driven operations, raising technical role exposure significantly
- The construction sector (large and labour-intensive) has low near-term AI exposure for manual work, though logistics and project management face disruption
- Hospitality and tourism (a major UAE sector) face moderate automation pressure in service roles but high pressure in back-office functions

A key signal is whether the job's work product is fundamentally digital. Jobs entirely on computers face high exposure (7+). Jobs requiring physical presence in unpredictable environments are more resilient.

Use these anchors calibrated for the UAE:
- 0-1: Minimal. Entirely physical, manual, or outdoor work. Examples: construction labourers, domestic workers, gardeners.
- 2-3: Low. Skilled manual trades or direct care roles. Examples: electricians, plumbers, chefs, security guards, nurses' aides.
- 4-5: Moderate. Mix of physical and knowledge work. Examples: nurses, hotel supervisors, teachers, police officers.
- 6-7: High. Predominantly knowledge/professional work. Examples: engineers, bank managers, accountants, HR professionals, lawyers.
- 8-9: Very high. Mostly computer-based, all core tasks digital. Examples: software developers, financial analysts, legal associates, data scientists.
- 10: Maximum. Routine digital processing only. Examples: data entry clerks, call centre agents, document processing clerks.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "exposure": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors, referencing UAE-specific context where relevant>"
}"""


def score_occupation(client, text, model):
    response = client.post(
        API_URL,
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content[:-3]
    return json.loads(content.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    with open("occupations.json", encoding="utf-8") as f:
        occupations = json.load(f)

    subset = occupations[args.start:args.end]

    scores = {}
    if os.path.exists(OUTPUT_FILE) and not args.force:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for entry in json.load(f):
                scores[entry["slug"]] = entry

    print(f"Scoring {len(subset)} UAE occupations with {args.model}")
    print(f"Already cached: {len(scores)}")

    errors = []
    client = httpx.Client()

    for i, occ in enumerate(subset):
        slug = occ["slug"]
        if slug in scores:
            continue

        md_path = f"pages/{slug}.md"
        if not os.path.exists(md_path):
            text = f"# {occ['title']}\n\nISCO Category: {occ.get('category', 'Unknown')}\nISCO Code: {occ.get('isco_code', 'Unknown')}\n\nUAE occupation from MOHRE/ISCO-08 classification."
            print(f"  [{i+1}] {occ['title']} (metadata only)...", end=" ", flush=True)
        else:
            with open(md_path, encoding="utf-8") as f:
                text = f.read()
            print(f"  [{i+1}/{len(subset)}] {occ['title']}...", end=" ", flush=True)

        try:
            result = score_occupation(client, text, args.model)
            scores[slug] = {"slug": slug, "title": occ["title"],
                            "isco_code": occ.get("isco_code", ""), **result}
            print(f"exposure={result['exposure']}")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(slug)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(scores.values()), f, indent=2, ensure_ascii=False)

        if i < len(subset) - 1:
            time.sleep(args.delay)

    client.close()
    print(f"\nDone. Scored {len(scores)} occupations, {len(errors)} errors.")

    vals = [s for s in scores.values() if "exposure" in s]
    if vals:
        avg = sum(s["exposure"] for s in vals) / len(vals)
        print(f"Average UAE AI exposure: {avg:.1f}/10")


if __name__ == "__main__":
    main()
