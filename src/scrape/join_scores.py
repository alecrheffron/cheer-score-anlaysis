from fetch_event import (
    EVENT_URL,
    build_view_all_url,
    fetch_event_page,
    find_result_rows,
)

from parse_score_pdf import parse_score_pdf


DIVISION = "L3 Youth - Flex - Small"
PDF_PATH = "data/raw/l3_youth_flex_small.pdf"


def normalize_name(value: str) -> str:
    """Normalize names for matching between HTML results and PDF rows."""
    return " ".join(
        value.lower()
        .replace("&", "and")
        .split()
    )


def build_result_lookup(results: list[dict], round_name: str) -> dict:
    """Build lookup keyed by normalized program + team name."""
    lookup = {}

    for result in results:
        full_name = (
            f"{result['program_name']} "
            f"{result['team_name']}"
        )

        key = normalize_name(full_name)

        lookup[key] = {
            **result,
            "round": round_name,
        }

    return lookup


if __name__ == "__main__":
    all_results = {}

    for round_name in ["Prelims", "Finals"]:

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

        for key, result in round_lookup.items():
            all_results[
                (round_name, key)
            ] = result

    score_records = parse_score_pdf(
        PDF_PATH
    )

    matched = 0
    unmatched = []

    for score in score_records:

        key = normalize_name(
            score["team_name_raw"]
        )

        match = all_results.get(
            (
                score["round"],
                key,
            )
        )

        if match is None:
            unmatched.append(
                (
                    score["round"],
                    score["team_name_raw"],
                )
            )
            continue

        matched += 1

        print()
        print(
            f"{score['round']} | "
            f"Rank {match['rank']} | "
            f"{score['team_name_raw']} | "
            f"DED {match['deductions']} | "
            f"Stunt D {score['stunt_difficulty']} | "
            f"Stunt E {score['stunt_execution']}"
        )

    print("\n" + "=" * 80)
    print(f"PDF records: {len(score_records)}")
    print(f"Matched:     {matched}")
    print(f"Unmatched:   {len(unmatched)}")

    if unmatched:
        print("\nUNMATCHED RECORDS")

        for record in unmatched:
            print(record)