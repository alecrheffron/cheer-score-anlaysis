import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://tv.varsity.com"

SEASON_START = date(
    2025,
    10,
    1,
)

SEASON_END = date(
    2026,
    5,
    31,
)

REQUEST_DELAY = 0.5

OUTPUT_PATH = Path(
    "data/interim/"
    "season_2026_events.csv"
)


def build_month_urls() -> list[str]:
    """
    Build one Varsity results URL for each
    month in the 2025-26 season.
    """

    month_urls = []

    year = SEASON_START.year
    month = SEASON_START.month

    while (
        year < SEASON_END.year
        or (
            year == SEASON_END.year
            and month <= SEASON_END.month
        )
    ):

        month_urls.append(
            (
                f"{BASE_URL}/results"
                f"?date={year:04d}-{month:02d}-01"
            )
        )

        month += 1

        if month == 13:
            month = 1
            year += 1

    return month_urls


def fetch_page(
    url: str,
) -> str:
    """
    Fetch one Varsity results page.
    """

    response = requests.get(
        url,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def clean_text(
    value: str | None,
) -> str | None:
    """
    Normalize whitespace.
    """

    if value is None:
        return None

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value or None


def extract_event_id(
    results_url: str,
) -> str | None:
    """
    Extract Varsity event ID from a results URL.
    """

    match = re.search(
        r"/events/(\d+)",
        results_url,
    )

    if match:
        return match.group(1)

    return None


def find_event_container(
    results_link,
):
    """
    Walk upward from a Results link until
    we find the smallest useful event container.
    """

    current = results_link.parent

    while current is not None:

        text = clean_text(
            current.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            has_date = bool(
                re.search(
                    (
                        r"\b("
                        r"Jan|Feb|Mar|Apr|May|Jun|"
                        r"Jul|Aug|Sep|Oct|Nov|Dec"
                        r")\b"
                    ),
                    text,
                )
            )

            event_links = current.find_all(
                "a",
                href=re.compile(
                    r"/events/\d+"
                ),
            )

            if (
                has_date
                and len(event_links) >= 1
            ):
                return current

        current = current.parent

    return None


def parse_event_from_link(
    results_link,
    source_month: str,
) -> dict | None:
    """
    Parse one event record from a Results link.
    """

    href = results_link.get(
        "href"
    )

    if not href:
        return None

    results_url = urljoin(
        BASE_URL,
        href,
    )

    if "/events/" not in results_url:
        return None

    if "/results" not in results_url:
        return None

    container = find_event_container(
        results_link
    )

    if container is None:
        return None

    container_text = clean_text(
        container.get_text(
            " ",
            strip=True,
        )
    )

    if not container_text:
        return None

    event_links = container.find_all(
        "a",
        href=re.compile(
            r"/events/\d+"
        ),
    )

    event_name = None

    for link in event_links:

        text = clean_text(
            link.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        if text.lower() in {
            "results",
            "replays",
            "videos",
            "schedule",
            "news",
        }:
            continue

        event_name = text
        break

    event_id = extract_event_id(
        results_url
    )

    return {
        "event_id": event_id,
        "event_name_raw": event_name,
        "event_card_text": container_text,
        "results_url": results_url,
        "source_month": source_month,
    }


def discover_events_for_month(
    month_url: str,
) -> list[dict]:
    """
    Discover event Results links from
    one monthly Varsity results page.
    """

    html = fetch_page(
        month_url
    )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    source_month_match = re.search(
        r"date=(\d{4}-\d{2})-\d{2}",
        month_url,
    )

    source_month = (
        source_month_match.group(1)
        if source_month_match
        else ""
    )

    records = []

    results_links = soup.find_all(
        "a",
        href=re.compile(
            r"/events/\d+.*?/results"
        ),
    )

    for results_link in results_links:

        record = parse_event_from_link(
            results_link,
            source_month,
        )

        if record is not None:
            records.append(
                record
            )

    return records


def discover_season_events() -> pd.DataFrame:
    """
    Discover all event results URLs across
    the configured season months.
    """

    month_urls = build_month_urls()

    all_records = []

    for index, month_url in enumerate(
        month_urls,
        start=1,
    ):

        print(
            f"[{index}/{len(month_urls)}] "
            f"{month_url}"
        )

        records = (
            discover_events_for_month(
                month_url
            )
        )

        print(
            f"  Found "
            f"{len(records)} "
            f"event result links"
        )

        all_records.extend(
            records
        )

        time.sleep(
            REQUEST_DELAY
        )

    df = pd.DataFrame(
        all_records
    )

    if df.empty:
        return df

    df = (
        df
        .drop_duplicates(
            subset=[
                "results_url"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return df


def save_season_events(
    df: pd.DataFrame,
) -> None:
    """
    Save discovered season events.
    """

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print(
        f"Saved: "
        f"{OUTPUT_PATH}"
    )


def main() -> None:

    events_df = (
        discover_season_events()
    )

    print()
    print(
        "=" * 80
    )

    print(
        "SEASON EVENT DISCOVERY"
    )

    print(
        "=" * 80
    )

    print(
        f"Unique events: "
        f"{len(events_df)}"
    )

    if not events_df.empty:

        print()
        print(
            events_df[
                [
                    "source_month",
                    "event_id",
                    "event_name_raw",
                    "results_url",
                ]
            ].to_string(
                index=False
            )
        )

        save_season_events(
            events_df
        )


if __name__ == "__main__":
    main()