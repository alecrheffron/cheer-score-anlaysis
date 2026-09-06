import re

from difflib import SequenceMatcher


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

        score_round = score["round"]
        score_name = normalize_name(
            score["team_name_raw"]
        )

        key = (
            score_round,
            score_name,
        )

        result = result_lookup.get(key)

        if result is None:
            candidates = []

            for candidate_key, candidate_result in result_lookup.items():
                candidate_round, candidate_name = candidate_key

                if candidate_round != score_round:
                    continue

                similarity = SequenceMatcher(
                    None,
                    score_name,
                    candidate_name,
                ).ratio()

                candidates.append(
                    (
                        similarity,
                        candidate_name,
                        candidate_result,
                    )
                )

            candidates.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            if candidates:
                best_score, best_name, best_result = candidates[0]

                second_score = (
                    candidates[1][0]
                    if len(candidates) > 1
                    else 0.0
                )

                if (
                    best_score >= 0.96
                    and best_score - second_score >= 0.03
                ):
                    print(
                        "  Fuzzy name match: "
                        f"{score_name!r} -> "
                        f"{best_name!r} "
                        f"({best_score:.3f})"
                    )

                    result = best_result

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