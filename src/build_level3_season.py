import re
from pathlib import Path

import pandas as pd

from scrape.scrape_level3_event import (
    scrape_level3_event,
)

from clean.build_event_tables import (
    build_performances_table,
    build_divisions_table,
)

from clean.build_teams import (
    build_teams_table,
)


INPUT_PATH = Path(
    "data/interim/"
    "season_2026_level3_events.csv"
)

OUTPUT_DIR = Path(
    "data/processed/season_2026_events"
)

STATUS_PATH = Path(
    "data/interim/"
    "season_2026_scrape_status.csv"
)


def make_competition_id(
    event_id: str,
    event_name: str,
) -> str:
    """
    Build a stable competition ID
    from Varsity event ID and name.
    """

    name_slug = (
        event_name
        .lower()
        .strip()
    )

    name_slug = re.sub(
        r"[^a-z0-9]+",
        "_",
        name_slug,
    )

    name_slug = (
        name_slug
        .strip("_")
    )

    return (
        f"{event_id}_"
        f"{name_slug}"
    )


def event_is_complete(
    competition_id: str,
) -> bool:
    """
    Return True when the event's main
    processed outputs already exist.
    """

    performances_path = (
        OUTPUT_DIR
        / f"{competition_id}_performances.csv"
    )

    divisions_path = (
        OUTPUT_DIR
        / f"{competition_id}_divisions.csv"
    )

    teams_path = (
        OUTPUT_DIR
        / f"{competition_id}_teams.csv"
    )

    return (
        performances_path.exists()
        and divisions_path.exists()
        and teams_path.exists()
    )


def save_event_tables(
    competition_id: str,
    merged_records: list[dict],
) -> tuple[int, int, int]:
    """
    Build and save event-level processed tables.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    performances = (
        build_performances_table(
            merged_records,
            competition_id,
        )
    )

    if performances.empty:
        raise ValueError(
            "No merged performance records"
        )

    divisions = (
        build_divisions_table(
            merged_records
        )
    )

    teams = (
        build_teams_table(
            merged_records
        )
    )

    performances.to_csv(
        OUTPUT_DIR
        / (
            f"{competition_id}"
            "_performances.csv"
        ),
        index=False,
    )

    divisions.to_csv(
        OUTPUT_DIR
        / (
            f"{competition_id}"
            "_divisions.csv"
        ),
        index=False,
    )

    teams.to_csv(
        OUTPUT_DIR
        / (
            f"{competition_id}"
            "_teams.csv"
        ),
        index=False,
    )

    return (
        len(performances),
        len(divisions),
        len(teams),
    )


def load_status() -> list[dict]:
    """
    Load prior season scraping status.
    """

    if not STATUS_PATH.exists():
        return []

    status_df = pd.read_csv(
        STATUS_PATH
    )

    return status_df.to_dict(
        orient="records"
    )


def update_status_row(
    rows: list[dict],
    new_row: dict,
) -> None:
    """
    Insert or replace one event status row.
    """

    event_id = str(
        new_row["event_id"]
    )

    rows[:] = [
        row
        for row in rows
        if str(
            row["event_id"]
        ) != event_id
    ]

    rows.append(
        new_row
    )


def save_status(
    rows: list[dict],
) -> None:
    """
    Save current season scraping status.
    """

    STATUS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        rows
    ).to_csv(
        STATUS_PATH,
        index=False,
    )


def main(
    limit: int | None = 50,
) -> None:
    """
    Scrape qualifying Level 3 events.

    Default limit is 50 so the batch
    system can be tested safely before
    launching the full season.
    """

    events = pd.read_csv(
        INPUT_PATH
    )

    if limit is not None:
        events = events.head(
            limit
        )

    status_rows = load_status()

    total_events = len(events)

    print(
        "=" * 80
    )

    print(
        "LEVEL 3 SEASON SCRAPE"
    )

    print(
        "=" * 80
    )

    print(
        f"Events queued: "
        f"{total_events}"
    )

    for index, row in events.iterrows():

        event_id = str(
            row["event_id"]
        )

        event_name = str(
            row["event_name_raw"]
        )

        event_url = row[
            "results_url"
        ]

        competition_id = (
            make_competition_id(
                event_id,
                event_name,
            )
        )

        print()
        print(
            "#" * 80
        )

        print(
            f"[{index + 1}/"
            f"{total_events}] "
            f"{event_name}"
        )

        print(
            f"Competition ID: "
            f"{competition_id}"
        )

        prior_status = next(
            (
                item
                for item in status_rows
                if str(
                    item["event_id"]
                ) == event_id
            ),
            None,
        )

        if (
            prior_status is not None
            and prior_status[
                "status"
            ] == "SUCCESS"
            and event_is_complete(
                competition_id
            )
        ):

            print(
                "SKIP: already complete"
            )

            continue

        try:

            (
                merged_records,
                unmatched_records,
                event_qa,
            ) = scrape_level3_event(
                event_url=event_url,
                competition_id=
                    competition_id,
            )

            if (
                event_qa[
                    "division_count"
                ] > 0
                and event_qa[
                    "no_pdf_division_count"
                ]
                == event_qa[
                    "division_count"
                ]
            ):
                print()
                print(
                    "EVENT SKIPPED | "
                    "No score breakdown PDFs "
                    "published"
                )

                update_status_row(
                    status_rows,
                    {
                        "event_id":
                            event_id,
                        "competition_id":
                            competition_id,
                        "event_name":
                            event_name,
                        "results_url":
                            event_url,
                        "status":
                            "NO_SCORE_BREAKDOWNS",
                        "performances":
                            0,
                        "divisions":
                            event_qa[
                                "division_count"
                            ],
                        "teams":
                            0,
                        "error":
                            None,
                    }
                )

                save_status(
                    status_rows
                )

                continue

            source_incomplete = (
                event_qa[
                    "check_division_count"
                ] > 0
                or event_qa[
                    "no_pdf_division_count"
                ] > 0
            )

            if source_incomplete:

                reasons = []

                if event_qa[
                    "check_division_count"
                ] > 0:
                    reasons.append(
                        f"{event_qa['check_division_count']} "
                        "division(s) failed QA checks"
                    )

                if event_qa[
                    "no_pdf_division_count"
                ] > 0:
                    reasons.append(
                        f"{event_qa['no_pdf_division_count']} "
                        "division(s) missing score "
                        "breakdown PDFs"
                    )

                print()
                print(
                    "EVENT SKIPPED | "
                    "Incomplete source data"
                )

                update_status_row(
                    status_rows,
                    {
                        "event_id":
                            event_id,
                        "competition_id":
                            competition_id,
                        "event_name":
                            event_name,
                        "results_url":
                            event_url,
                        "status":
                            "SOURCE_INCOMPLETE",
                        "performances":
                            0,
                        "divisions":
                            event_qa[
                                "division_count"
                            ],
                        "teams":
                            0,
                        "error":
                            "; ".join(reasons),
                    }
                )

                save_status(
                    status_rows
                )

                continue

            if event_qa[
                "error_division_count"
            ] > 0:
                raise ValueError(
                    f"{event_qa['error_division_count']} "
                    "division(s) had scraper errors"
                )

            if unmatched_records:
                raise ValueError(
                    f"{len(unmatched_records)} "
                    "unmatched records"
                )

            (
                performance_count,
                division_count,
                team_count,
            ) = save_event_tables(
                competition_id,
                merged_records,
            )

            status = "SUCCESS"
            error = None

            print()
            print(
                f"EVENT COMPLETE | "
                f"{performance_count} "
                f"performances"
            )

        except Exception as exc:

            performance_count = None
            division_count = None
            team_count = None

            status = "ERROR"

            error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            print()
            print(
                f"EVENT FAILED | "
                f"{error}"
            )

        update_status_row(
            status_rows,
            {
                "event_id":
                    event_id,
                "competition_id":
                    competition_id,
                "event_name":
                    event_name,
                "results_url":
                    event_url,
                "status":
                    status,
                "performances":
                    performance_count,
                "divisions":
                    division_count,
                "teams":
                    team_count,
                "error":
                    error,
            }
        )

        save_status(
            status_rows
        )

    print()
    print(
        "=" * 80
    )

    print(
        "BATCH COMPLETE"
    )

    print(
        "=" * 80
    )

    status_df = pd.DataFrame(
        status_rows
    )

    if not status_df.empty:

        print(
            status_df[
                "status"
            ].value_counts()
        )

    print(
        f"Status saved: "
        f"{STATUS_PATH}"
    )


if __name__ == "__main__":
    main()