from pathlib import Path

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

if __name__ == "__main__":
    html = fetch_event_page(EVENT_URL)

    save_html(
        html,
        "nca_2026_results.html",
    )

    breakdowns = find_score_breakdowns(html)

    print(f"Downloaded {len(html):,} characters")
    print(f"Found {len(breakdowns)} unique score breakdowns")

    for breakdown in breakdowns:
        print()
        print(breakdown["division_round"])
        print(breakdown["pdf_url"])