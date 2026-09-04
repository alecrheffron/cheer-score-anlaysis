import re
import time
from pathlib import Path

from scrape.fetch_event import (
    build_division_url,
    build_view_all_url,
    download_pdf,
    fetch_event_page,
    find_divisions,
    find_result_rows,
    find_score_breakdowns,
    find_rounds,
)

from scrape.join_scores import (
    build_result_lookup,
    join_score_records,
)

from scrape.parse_score_pdf import (
    parse_score_pdf,
)


REQUEST_DELAY = 0.5

PDF_DIR = Path(
    "data/raw/score_breakdowns"
)


def make_filename(
    competition_id: str,
    division: str,
) -> str:
    """
    Convert competition and division names
    into a safe PDF filename.
    """

    combined_name = (
        f"{competition_id}_{division}"
    )

    filename = combined_name.lower()

    filename = re.sub(
        r"[^a-z0-9]+",
        "_",
        filename,
    )

    filename = filename.strip("_")

    return f"{filename}.pdf"


def get_level3_divisions(
    event_url: str,
    html: str | None = None,
) -> list[str]:
    """
    Discover standard Level 3 divisions
    from one event page.

    If event HTML is supplied, reuse it so the
    event page does not need to be fetched twice.
    """

    if html is None:
        html = fetch_event_page(
            event_url
        )

    divisions = find_divisions(
        html
    )

    excluded_groups = (
        "L3 - U16",
        "L3 - U18",
    )

    return [
        division
        for division in divisions
        if division.startswith(
            (
                "L3 Youth",
                "L3 Junior",
                "L3 Senior",
            )
        )
    ]


def get_score_pdf(
    event_url: str,
    competition_id: str,
    division: str,
    rounds: list[str],
) -> list[Path]:
    """
    Find and download all unique score breakdown
    PDFs available for one division.
    """

    pdf_urls = []

    for round_name in rounds:

        division_url = build_division_url(
            event_url,
            division,
            round_name,
        )

        html = fetch_event_page(
            division_url
        )

        breakdowns = find_score_breakdowns(
            html
        )

        if not breakdowns:
            continue

        pdf_url = breakdowns[0]["pdf_url"]

        if pdf_url not in pdf_urls:
            pdf_urls.append(
                pdf_url
            )

        time.sleep(
            REQUEST_DELAY
        )

    if not pdf_urls:
        return []

    PDF_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf_paths = []

    for index, pdf_url in enumerate(
        pdf_urls,
        start=1,
    ):

        if len(pdf_urls) == 1:

            filename = make_filename(
                competition_id,
                division,
            )

        else:

            filename = make_filename(
                competition_id,
                f"{division}_part_{index}",
            )

        output_path = (
            PDF_DIR
            / filename
        )

        if output_path.exists():

            pdf_paths.append(
                output_path
            )

            continue

        downloaded_path = download_pdf(
            pdf_url,
            f"score_breakdowns/{filename}",
        )

        pdf_paths.append(
            downloaded_path
        )

        time.sleep(
            REQUEST_DELAY
        )

    return pdf_paths


def get_division_results(
    event_url: str,
    division: str,
    rounds: list[str],
) -> dict:
    """
    Fetch complete View All results
    for the supplied competition rounds.
    """

    result_lookup = {}
    round_counts = {}

    for round_name in rounds:

        url = build_view_all_url(
            event_url,
            division,
            round_name,
        )

        html = fetch_event_page(
            url
        )

        results = find_result_rows(
            html
        )

        round_counts[
            round_name
        ] = len(results)

        lookup = build_result_lookup(
            results,
            round_name,
        )

        result_lookup.update(
            lookup
        )

        time.sleep(
            REQUEST_DELAY
        )

    return {
        "lookup": result_lookup,
        "round_counts": round_counts,
    }


def scrape_level3_event(
    event_url: str,
    competition_id: str,
) -> tuple[
    list[dict],
    list[dict],
    dict,
]:
    """
    Download, parse, and join all
    standard Level 3 divisions
    for one competition.
    """

    html = fetch_event_page(
        event_url
    )

    rounds = find_rounds(
        html
    )

    if not rounds:
        raise ValueError(
            f"No competition rounds found for "
            f"{competition_id}"
        )

    divisions = get_level3_divisions(
        event_url,
        html=html,
    )

    print(
        f"Found {len(divisions)} "
        f"Level 3 divisions"
    )

    print(
        f"Rounds found: "
        f"{', '.join(rounds)}"
    )

    print(
        "=" * 80
    )

    all_merged_records = []
    all_unmatched_records = []
    division_summaries = []

    for index, division in enumerate(
        divisions,
        start=1,
    ):

        print()
        print(
            f"[{index}/{len(divisions)}] "
            f"{division}"
        )

        try:

            pdf_paths = get_score_pdf(
                event_url,
                competition_id,
                division,
                rounds,
            )

            if not pdf_paths:

                print(
                    "  ERROR: "
                    "No score breakdown PDF found"
                )

                division_summaries.append(
                    {
                        "division": division,
                        "status": "NO PDF",
                        "round_counts": {
                            round_name: 0
                            for round_name
                            in rounds
                        },
                        "pdf_records": 0,
                        "merged": 0,
                        "unmatched": 0,
                    }
                )

                continue

            score_records = []

            for pdf_path in pdf_paths:

                parsed_records = (
                    parse_score_pdf(
                        str(pdf_path)
                    )
                )

                score_records.extend(
                    parsed_records
                )

            results_data = (
                get_division_results(
                    event_url,
                    division,
                    rounds,
                )
            )

            merged_records, unmatched = (
                join_score_records(
                    score_records,
                    results_data[
                        "lookup"
                    ],
                    division,
                )
            )

            round_counts = (
                results_data[
                    "round_counts"
                ]
            )

            expected_records = sum(
                round_counts.values()
            )

            for round_name in rounds:

                print(
                    f"  {round_name} results: "
                    f"{round_counts[round_name]}"
                )

            print(
                f"  PDF records:      "
                f"{len(score_records)}"
            )

            print(
                f"  Merged:           "
                f"{len(merged_records)}"
            )

            print(
                f"  Unmatched:        "
                f"{len(unmatched)}"
            )

            is_problem = (
                len(score_records)
                != expected_records
                or len(merged_records)
                != expected_records
                or len(unmatched)
                != 0
            )

            status = (
                "CHECK"
                if is_problem
                else "OK"
            )

            division_summaries.append(
                {
                    "division": division,
                    "status": status,
                    "round_counts":
                        round_counts,
                    "pdf_records": len(
                        score_records
                    ),
                    "merged": len(
                        merged_records
                    ),
                    "unmatched": len(
                        unmatched
                    ),
                }
            )

            all_merged_records.extend(
                merged_records
            )

            for record in unmatched:

                all_unmatched_records.append(
                    {
                        "division":
                            division,
                        **record,
                    }
                )

        except Exception as exc:

            print(
                f"  ERROR: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            division_summaries.append(
                {
                    "division": division,
                    "status": "ERROR",
                    "round_counts": {
                        round_name: 0
                        for round_name
                        in rounds
                    },
                    "pdf_records": 0,
                    "merged": 0,
                    "unmatched": 0,
                }
            )

        time.sleep(
            REQUEST_DELAY
        )

    print()
    print(
        "=" * 80
    )

    print(
        "LEVEL 3 EVENT QA"
    )

    print(
        "=" * 80
    )

    total_round_counts = {
        round_name: sum(
            row[
                "round_counts"
            ].get(
                round_name,
                0,
            )
            for row
            in division_summaries
        )
        for round_name
        in rounds
    }

    total_view_all = sum(
        total_round_counts.values()
    )

    total_pdf_records = sum(
        row["pdf_records"]
        for row
        in division_summaries
    )

    print(
        f"Divisions:          "
        f"{len(divisions)}"
    )

    for round_name in rounds:

        print(
            f"{round_name} results: "
            f"{total_round_counts[round_name]}"
        )

    print(
        f"View All total:     "
        f"{total_view_all}"
    )

    print(
        f"PDF records:        "
        f"{total_pdf_records}"
    )

    print(
        f"Merged records:     "
        f"{len(all_merged_records)}"
    )

    print(
        f"Unmatched records:  "
        f"{len(all_unmatched_records)}"
    )

    problem_divisions = [
        row
        for row
        in division_summaries
        if row["status"] != "OK"
    ]

    print(
        f"Problem divisions:  "
        f"{len(problem_divisions)}"
    )

    if problem_divisions:

        print()
        print(
            "DIVISIONS TO CHECK"
        )

        for row in problem_divisions:

            print(
                f"  {row['status']} | "
                f"{row['division']} | "
                f"PDF "
                f"{row['pdf_records']} | "
                f"Merged "
                f"{row['merged']} | "
                f"Unmatched "
                f"{row['unmatched']}"
            )

    if all_unmatched_records:

        print()
        print(
            "UNMATCHED TEAMS"
        )

        for record in (
            all_unmatched_records
        ):

            print(
                f"  "
                f"{record['division']} | "
                f"{record['round']} | "
                f"{record['team_name_raw']}"
            )

    event_qa = {
        "division_count": len(divisions),
        "problem_division_count": len(
            problem_divisions
        ),
        "no_pdf_division_count": sum(
            row["status"] == "NO PDF"
            for row in division_summaries
        ),
        "error_division_count": sum(
            row["status"] == "ERROR"
            for row in division_summaries
        ),
        "check_division_count": sum(
            row["status"] == "CHECK"
            for row in division_summaries
        ),
        "pdf_records": total_pdf_records,
        "merged_records": len(
            all_merged_records
        ),
        "unmatched_records": len(
            all_unmatched_records
        ),
    }

    return (
        all_merged_records,
        all_unmatched_records,
        event_qa,
    )