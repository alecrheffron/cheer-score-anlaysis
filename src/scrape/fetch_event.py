import json
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


EVENT_URL = (
    "https://tv.varsity.com/events/"
    "14478911-2026-nca-all-star-national-championship/results"
)


def fetch_event_page(url: str) -> str:
    """Download the HTML for a Varsity TV competition results page."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.text


def save_html(html: str, filename: str) -> None:
    """Save raw event HTML for inspection."""
    output_path = Path("data/raw") / filename
    output_path.write_text(html, encoding="utf-8")


def find_divisions(html: str) -> list[str]:
    """Extract unique cheer division names from Varsity's division dropdown."""
    soup = BeautifulSoup(html, "lxml")

    divisions = []
    seen = set()

    level_prefixes = (
        "L1 ",
        "L2 ",
        "L3 ",
        "L4 ",
        "L4.2 ",
        "L5 ",
        "L6 ",
        "L7 ",
    )

    for span in soup.find_all("span", class_="dropdown-title"):
        title = span.get_text(" ", strip=True)

        if title.startswith(level_prefixes) and title not in seen:
            divisions.append(title)
            seen.add(title)

    return divisions


def find_score_breakdowns(html: str) -> list[dict]:
    """Extract division/round names and unique Score Breakdown URLs."""
    soup = BeautifulSoup(html, "lxml")

    breakdowns = []
    seen = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"]

        if "FileDownload" not in href or href in seen:
            continue

        seen.add(href)

        parent = tag.parent

        if parent is None or parent.parent is None:
            continue

        section = parent.parent
        section_text = section.get_text(" ", strip=True)

        section_text = (
            section_text
            .replace("Score Breakdowns", "")
            .replace("View All", "")
            .strip()
        )

        breakdowns.append(
            {
                "division_round": section_text,
                "pdf_url": href,
            }
        )

    return breakdowns


def build_division_url(
    base_url: str,
    division: str,
    round_name: str = "Finals",
) -> str:
    """Build a Varsity results URL filtered to one division and round."""
    facets = {
        "class": "Cheer",
        "division": division,
        "roundName": round_name,
    }

    query = urlencode(
        {
            "facets": json.dumps(
                facets,
                separators=(",", ":"),
            )
        }
    )

    return f"{base_url}?{query}"


if __name__ == "__main__":
    html = fetch_event_page(EVENT_URL)

    save_html(
        html,
        "nca_2026_results.html",
    )

    divisions = find_divisions(html)

    level_3_divisions = [
        division
        for division in divisions
        if division.startswith("L3 ")
    ]

    print(f"Downloaded {len(html):,} characters")
    print(f"Found {len(divisions)} total divisions")
    print(f"Found {len(level_3_divisions)} Level 3 divisions")

    test_division = "L3 Junior - D2 - Small - A"

    division_url = build_division_url(
        EVENT_URL,
        test_division,
    )

    division_html = fetch_event_page(division_url)
    division_breakdowns = find_score_breakdowns(division_html)

    print(f"\nTesting: {test_division}")
    print(f"Found {len(division_breakdowns)} score breakdown(s)")

    for breakdown in division_breakdowns:
        print(breakdown["division_round"])
        print(breakdown["pdf_url"])