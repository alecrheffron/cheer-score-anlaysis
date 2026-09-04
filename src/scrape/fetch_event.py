import re
import json
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


EVENT_URL = (
    "https://tv.varsity.com/events/"
    "14478838/results"
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


def find_rounds(
    html: str,
) -> list[str]:
    """
    Extract unique competition round names
    from a Varsity event results page.

    Sources checked:
    1. Round dropdown
    2. Score Breakdown titles
    3. Visible heading text
    4. Raw HTML / embedded page data
    """

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    rounds = []
    seen = set()

    round_pattern = re.compile(
        r"\b("
        r"Prelims|"
        r"Finals|"
        r"Semifinals|"
        r"Semi-Finals|"
        r"Round\s+\d+"
        r")\b",
        flags=re.IGNORECASE,
    )

    def add_round(
        value: str,
    ) -> None:
        """
        Normalize and add one round name.
        """

        value = value.strip()

        if value.lower().startswith(
            "round "
        ):
            value = value.title()

        elif value.lower() == "prelims":
            value = "Prelims"

        elif value.lower() == "finals":
            value = "Finals"

        elif value.lower() in (
            "semifinals",
            "semi-finals",
        ):
            value = "Semifinals"

        if value not in seen:
            rounds.append(
                value
            )

            seen.add(
                value
            )

    # --------------------------------------------------
    # 1. Round dropdown
    # --------------------------------------------------

    round_list = soup.find(
        "div",
        id="filter-roundName",
    )

    if round_list is not None:

        for span in round_list.find_all(
            "span",
            class_="dropdown-title",
        ):

            round_name = span.get_text(
                " ",
                strip=True,
            )

            if round_name:
                add_round(
                    round_name
                )

    if rounds:
        return rounds

    # --------------------------------------------------
    # 2. Score Breakdown titles
    # --------------------------------------------------

    breakdowns = find_score_breakdowns(
        html
    )

    for breakdown in breakdowns:

        division_round = breakdown[
            "division_round"
        ]

        match = round_pattern.search(
            division_round
        )

        if match is not None:
            add_round(
                match.group(1)
            )

    if rounds:
        return rounds

    # --------------------------------------------------
    # 3. Visible headings
    # --------------------------------------------------

    for heading in soup.find_all(
        ["h2", "h3", "h4", "h5"],
    ):

        heading_text = heading.get_text(
            " ",
            strip=True,
        )

        match = round_pattern.search(
            heading_text
        )

        if match is not None:
            add_round(
                match.group(1)
            )

    if rounds:
        return rounds

    # --------------------------------------------------
    # 4. Raw HTML / embedded serialized data
    # --------------------------------------------------

    for match in round_pattern.finditer(
        html
    ):

        add_round(
            match.group(1)
        )

    return rounds


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

    if round_name == "Semifinals":
        round_name = "Semi-Finals"

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

    if round_name == "Semifinals":
        round_name = "Semi-Finals"

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

def download_pdf(url: str, filename: str) -> Path:
    """Download a Varsity score breakdown PDF."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    output_path = Path("data/raw") / filename
    output_path.write_bytes(response.content)

    return output_path

if __name__ == "__main__":

    html = fetch_event_page(
        EVENT_URL
    )

    rounds = find_rounds(
        html
    )

    print(
        f"Found {len(rounds)} round(s)"
    )

    for round_name in rounds:

        print(
            f"  {round_name}"
        )