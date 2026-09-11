from pathlib import Path

import pandas as pd

from scrape.scrape_level3_event import (
    scrape_level_event,
)

from clean.build_event_tables import (
    build_performances_table,
    build_divisions_table,
)

from clean.build_teams import (
    build_teams_table,
)


def get_level_paths(
    level: str,
) -> tuple[Path, Path, Path]:
    """
    Build level-specific input, output,
    and status paths.

    Level 3 keeps its existing paths so the
    validated collection does not need to
    be migrated or re-scraped.
    """

    level_slug = level.replace(
        ".",
        "_",
    )

    input_path = Path(
        "data/interim/"
        f"season_2026_level{level_slug}_events.csv"
    )

    if level == "3":
        output_dir = Path(
            "data/processed/"
            "season_2026_events"
        )

        status_path = Path(
            "data/interim/"
            "season_2026_scrape_status.csv"
        )

    else:
        output_dir = Path(
            "data/processed/"
            "season_2026_events/"
            f"level_{level_slug}"
        )

        status_path = Path(
            "data/interim/"
            f"season_2026_level{level_slug}_"
            "scrape_status.csv"
        )

    return (
        input_path,
        output_dir,
        status_path,
    )


def make_competition_id(
    event_id: str,
    event_name: str,
) -> str:
    """
    Build a stable competition ID
    from the Varsity event ID.
    """

    return str(event_id)


def event_is_complete(
    competition_id: str,
    output_dir: Path,
) -> bool:
    """
    Return True when the event's main
    processed outputs already exist.
    """

    performances_path = (
        output_dir
        / f"{competition_id}_performances.csv"
    )

    divisions_path = (
        output_dir
        / f"{competition_id}_divisions.csv"
    )

    teams_path = (
        output_dir
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
    output_dir: Path,
) -> tuple[int, int, int]:
    """
    Build and save event-level processed tables.
    """

    output_dir.mkdir(
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
        output_dir
        / (
            f"{competition_id}"
            "_performances.csv"
        ),
        index=False,
    )

    divisions.to_csv(
        output_dir
        / (
            f"{competition_id}"
            "_divisions.csv"
        ),
        index=False,
    )

    teams.to_csv(
        output_dir
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


def load_status(
    status_path: Path,
) -> list[dict]:
    """
    Load prior season scraping status.
    """

    if not status_path.exists():
        return []

    status_df = pd.read_csv(
        status_path
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
    status_path: Path,
) -> None:
    """
    Save current season scraping status.
    """

    status_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        rows
    ).to_csv(
        status_path,
        index=False,
    )


def main(
    level: str = "3",
    limit: int | None = None,
) -> None:
    """
    Scrape qualifying events for one
    competitive All Star level.
    """

    (
        input_path,
        output_dir,
        status_path,
    ) = get_level_paths(
        level
    )

    events = pd.read_csv(
        input_path
    )

    if limit is not None:
        events = events.head(
            limit
        )

    status_rows = load_status(
        status_path
    )

    total_events = len(events)

    print(
        "=" * 80
    )

    print(
        f"LEVEL {level} SEASON SCRAPE"
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

        if prior_status is not None:

            prior_state = str(
                prior_status["status"]
            )

            prior_performances = pd.to_numeric(
                prior_status.get(
                    "performances"
                ),
                errors="coerce",
            )

            if (
                prior_state == "SUCCESS"
                and event_is_complete(
                    competition_id,
                    output_dir,
                )
            ):
                print(
                    "SKIP: already complete"
                )
                continue

            if (
                prior_state
                == "NO_SCORE_BREAKDOWNS"
            ):
                print(
                    "SKIP: no score "
                    "breakdowns published"
                )
                continue

            if (
                prior_state
                == "SOURCE_INCOMPLETE"
            ):
                if (
                    pd.notna(
                        prior_performances
                    )
                    and prior_performances > 0
                ):
                    if event_is_complete(
                        competition_id,
                        output_dir,
                    ):
                        print(
                            "SKIP: partial event "
                            "already processed"
                        )
                        continue
                else:
                    print(
                        "SKIP: source incomplete "
                        "with no usable records"
                    )
                    continue

        try:

            (
                merged_records,
                unmatched_records,
                event_qa,
            ) = scrape_level_event(
                event_url=event_url,
                competition_id=competition_id,
                level=level,
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
                    status_rows,
                    status_path,
                )

                continue

            if event_qa[
                "error_division_count"
            ] > 0:
                raise ValueError(
                    f"{event_qa['error_division_count']} "
                    "division(s) had scraper errors"
                )

            source_incomplete = (
                event_qa[
                    "check_division_count"
                ] > 0
                or event_qa[
                    "no_pdf_division_count"
                ] > 0
                or len(unmatched_records) > 0
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

                if unmatched_records:
                    reasons.append(
                        f"{len(unmatched_records)} "
                        "score record(s) could not be "
                        "matched to published results"
                    )

                if event_qa[
                    "no_pdf_division_count"
                ] > 0:
                    reasons.append(
                        f"{event_qa['no_pdf_division_count']} "
                        "division(s) missing score "
                        "breakdown PDFs"
                    )

                if merged_records:
                    (
                        performance_count,
                        division_count,
                        team_count,
                    ) = save_event_tables(
                        competition_id,
                        merged_records,
                        output_dir,
                    )

                    print()
                    print(
                        "EVENT PARTIAL | "
                        f"{performance_count} usable "
                        "performances saved"
                    )

                else:
                    performance_count = 0
                    division_count = 0
                    team_count = 0

                    print()
                    print(
                        "EVENT SKIPPED | "
                        "No usable performances"
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
                            performance_count,
                        "divisions":
                            division_count,
                        "teams":
                            team_count,
                        "error":
                            "; ".join(reasons),
                    }
                )

                save_status(
                    status_rows,
                    status_path,
                )

                continue

            (
                performance_count,
                division_count,
                team_count,
            ) = save_event_tables(
                competition_id,
                merged_records,
                output_dir,
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
            status_rows,
            status_path,
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
        f"{status_path}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--level",
        type=str,
        default="3",
        choices=[
            "1",
            "2",
            "3",
            "4",
            "4.2",
            "5",
            "6",
            "7",
        ],
        help=(
            "Competitive All Star level "
            "to scrape"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Optional maximum number of "
            "qualified events to process"
        ),
    )

    args = parser.parse_args()

    main(
        level=args.level,
        limit=args.limit,
    )