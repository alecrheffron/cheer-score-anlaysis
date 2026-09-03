from scrape.fetch_event import (
    EVENT_URL,
    build_view_all_url,
    fetch_event_page,
    find_result_rows,
)

from scrape.parse_score_pdf import parse_score_pdf


DIVISION = "L3 Youth - Flex - Small"
PDF_PATH = "data/raw/l3_youth_flex_small.pdf"


def normalize_name(value: str) -> str:
    """Normalize names for matching between HTML results and PDF rows."""
    return " ".join(
        value.lower()
        .replace("&", "and")
        .split()
    )


def build_result_lookup(
    results: list[dict],
    round_name: str,
) -> dict:
    """Build result lookup keyed by round and normalized team identity."""
    lookup = {}

    for result in results:
        full_name = (
            f"{result['program_name']} "
            f"{result['team_name']}"
        )

        key = (
            round_name,
            normalize_name(full_name),
        )

        lookup[key] = result

    return lookup


def join_score_records(
    score_records: list[dict],
    result_lookup: dict,
    division: str,
) -> tuple[list[dict], list[dict]]:
    """Join PDF scoring records to View All competition results."""
    merged_records = []
    unmatched_records = []

    for score in score_records:

        key = (
            score["round"],
            normalize_name(
                score["team_name_raw"]
            ),
        )

        result = result_lookup.get(key)

        if result is None:
            unmatched_records.append(score)
            continue

        merged_record = {
            "division": division,
            "round": score["round"],

            "program_name": result["program_name"],
            "team_name": result["team_name"],

            "rank": result["rank"],
            "raw_score": result["raw_score"],
            "deductions": result["deductions"],
            "performance_score": result["performance_score"],
            "event_score": result["event_score"],

            **{
                key: value
                for key, value in score.items()
                if key not in {
                    "round",
                    "team_name_raw",
                }
            },
        }

        merged_records.append(
            merged_record
        )

    return merged_records, unmatched_records


if __name__ == "__main__":

    result_lookup = {}

    for round_name in [
        "Prelims",
        "Finals",
    ]:

        view_all_url = build_view_all_url(
            EVENT_URL,
            DIVISION,
            round_name,
        )

        html = fetch_event_page(
            view_all_url
        )

        results = find_result_rows(
            html
        )

        round_lookup = build_result_lookup(
            results,
            round_name,
        )

        result_lookup.update(
            round_lookup
        )

    score_records = parse_score_pdf(
        PDF_PATH
    )

    merged_records, unmatched = (
        join_score_records(
            score_records,
            result_lookup,
            DIVISION,
        )
    )

    for record in merged_records:
        print()
        print(
            f"{record['round']} | "
            f"Rank {record['rank']} | "
            f"{record['program_name']} / "
            f"{record['team_name']} | "
            f"RS {record['raw_score']} | "
            f"DED {record['deductions']} | "
            f"PS {record['performance_score']} | "
            f"Stunt D {record['stunt_difficulty']} | "
            f"Stunt E {record['stunt_execution']}"
        )

    print("\n" + "=" * 80)
    print(
        f"Merged records: {len(merged_records)}"
    )
    print(
        f"Unmatched:      {len(unmatched)}"
    )