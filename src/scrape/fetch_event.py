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

def find_result_rows(html: str) -> list[dict]:
    """Extract team result rows from a filtered Varsity results page."""
    soup = BeautifulSoup(html, "lxml")

    results = []

    for row in soup.select("table.results-varsity tbody tr"):
        cells = row.find_all("td")

        if len(cells) < 7:
            continue

        rank = cells[0].get_text(" ", strip=True)

        program_cell = cells[2]

        program_tag = program_cell.select_one("div.text")
        team_tag = program_cell.select_one("div.sub-text")

        program_name = (
            program_tag.get_text(" ", strip=True)
            if program_tag
            else ""
        )

        team_name = (
            team_tag.get_text(" ", strip=True)
            if team_tag
            else ""
        )

        raw_score = cells[3].get_text(" ", strip=True)
        deductions = cells[4].get_text(" ", strip=True)
        performance_score = cells[5].get_text(" ", strip=True)
        event_score = cells[6].get_text(" ", strip=True)

        results.append(
            {
                "rank": rank,
                "program_name": program_name,
                "team_name": team_name,
                "raw_score": raw_score,
                "deductions": deductions,
                "performance_score": performance_score,
                "event_score": event_score,
            }
        )

    return results

def build_view_all_url(
    base_url: str,
    division: str,
    round_name: str = "Finals",
) -> str:
    """Build a Varsity View All results URL for one division and round."""
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

    return f"{base_url}/view-all?{query}"

if __name__ == "__main__":
    test_division = "L3 Youth - Flex - Small"

    rounds = [
        "Prelims",
        "Finals",
    ]

    for round_name in rounds:
        view_all_url = build_view_all_url(
            EVENT_URL,
            test_division,
            round_name,
        )

        view_all_html = fetch_event_page(
            view_all_url
        )

        results = find_result_rows(
            view_all_html
        )

        print("\n" + "=" * 80)
        print(f"{test_division} | {round_name}")
        print("=" * 80)
        print(f"Found {len(results)} team result rows")

        for result in results:
            print(
                f"{result['rank']} | "
                f"{result['program_name']} | "
                f"{result['team_name']} | "
                f"RS {result['raw_score']} | "
                f"DED {result['deductions']} | "
                f"PS {result['performance_score']} | "
                f"ES {result['event_score']}"
            )