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
)

from scrape.join_scores import (
    build_result_lookup,
    join_score_records,
)

from scrape.parse_score_pdf import (
    parse_score_pdf,
)


REQUEST_DELAY = 0.5

PDF_DIR = Path("data/raw/score_breakdowns")


def make_filename(
    competition_id: str,
    division: str,
) -> str:
    """
    Convert competition and division names into
    a safe PDF filename.
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
) -> list[str]:
    """
    Discover standard Level 3 divisions
    from one event page.
    """

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
        if (
            division.startswith("L3 ")
            and not division.startswith(
                excluded_groups
            )
        )
    ]


def get_score_pdf(
    event_url: str,
    competition_id: str,
    division: str,
) -> Path | None:
    """
    Find and download the score breakdown PDF
    for one division.
    """

    division_url = build_division_url(
        event_url,
        division,
        "Finals",
    )

    html = fetch_event_page(
        division_url
    )

    breakdowns = find_score_breakdowns(
        html
    )

    if not breakdowns:
        return None

    PDF_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = make_filename(
        competition_id,
        division,
    )

    output_path = (
        PDF_DIR
        / filename
    )

    if output_path.exists():
        return output_path

    downloaded_path = download_pdf(
        breakdowns[0]["pdf_url"],
        f"score_breakdowns/{filename}",
    )

    return downloaded_path


def get_division_results(
    event_url: str,
    division: str,
) -> dict:
    """
    Fetch complete View All results
    for Prelims and Finals.
    """

    result_lookup = {}

    round_counts = {}

    for round_name in [
        "Prelims",
        "Finals",
    ]:

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
]:
    """
    Download, parse, and join all standard
    Level 3 divisions for one competition.
    """

    divisions = get_level3_divisions(
        event_url
    )

    print(
        f"Found {len(divisions)} "
        f"Level 3 divisions"
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
            pdf_path = get_score_pdf(
                event_url,
                competition_id,
                division,
            )

            if pdf_path is None:

                print(
                    "  ERROR: "
                    "No score breakdown PDF found"
                )

                division_summaries.append(
                    {
                        "division": division,
                        "status": "NO PDF",
                        "prelims": 0,
                        "finals": 0,
                        "pdf_records": 0,
                        "merged": 0,
                        "unmatched": 0,
                    }
                )

                continue

            time.sleep(
                REQUEST_DELAY
            )

            score_records = parse_score_pdf(
                str(pdf_path)
            )

            results_data = get_division_results(
                event_url,
                division,
            )

            merged_records, unmatched = (
                join_score_records(
                    score_records,
                    results_data["lookup"],
                    division,
                )
            )

            prelim_count = (
                results_data[
                    "round_counts"
                ]["Prelims"]
            )

            final_count = (
                results_data[
                    "round_counts"
                ]["Finals"]
            )

            print(
                f"  Prelims results: "
                f"{prelim_count}"
            )

            print(
                f"  Finals results:   "
                f"{final_count}"
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

            expected_records = (
                prelim_count
                + final_count
            )

            is_problem = (
                len(score_records) != expected_records
                or len(merged_records) != expected_records
                or len(unmatched) != 0
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
                    "prelims": prelim_count,
                    "finals": final_count,
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
                        "division": division,
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
                    "prelims": 0,
                    "finals": 0,
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

    total_prelims = sum(
        row["prelims"]
        for row in division_summaries
    )

    total_finals = sum(
        row["finals"]
        for row in division_summaries
    )

    total_pdf_records = sum(
        row["pdf_records"]
        for row in division_summaries
    )

    print(
        f"Divisions:          "
        f"{len(divisions)}"
    )

    print(
        f"Prelim results:     "
        f"{total_prelims}"
    )

    print(
        f"Final results:      "
        f"{total_finals}"
    )

    print(
        f"View All total:     "
        f"{total_prelims + total_finals}"
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
        for row in division_summaries
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
                f"PDF {row['pdf_records']} | "
                f"Merged {row['merged']} | "
                f"Unmatched {row['unmatched']}"
            )

    if all_unmatched_records:

        print()
        print(
            "UNMATCHED TEAMS"
        )

        for record in all_unmatched_records:

            print(
                f"  {record['division']} | "
                f"{record['round']} | "
                f"{record['team_name_raw']}"
            )

    return (
        all_merged_records,
        all_unmatched_records,
    )