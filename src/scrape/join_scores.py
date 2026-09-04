import re


def normalize_name(
    value: str,
) -> str:
    """
    Normalize program/team names for matching.
    """

    value = value.lower()

    value = value.replace(
        "&",
        "and",
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


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