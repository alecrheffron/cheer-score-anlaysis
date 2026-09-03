from pathlib import Path

import pandas as pd

from clean.parse_divisions import parse_division_name

from clean.build_teams import make_team_id

PROCESSED_DIR = Path("data/processed")


PERFORMANCE_COLUMNS = [
    "competition_id",
    "division_id",
    "team_id",
    "round",
    "program_name",
    "team_name",
    "rank",
    "raw_score",
    "deductions",
    "performance_score",
    "event_score",
    "stunt_difficulty",
    "stunt_execution",
    "stunt_dod",
    "stunt_max",
    "pyramid_difficulty",
    "pyramid_execution",
    "toss_difficulty",
    "toss_execution",
    "standing_tumbling_difficulty",
    "standing_tumbling_execution",
    "standing_tumbling_dod",
    "running_tumbling_difficulty",
    "running_tumbling_execution",
    "running_tumbling_dod",
    "running_tumbling_max",
    "jump_difficulty",
    "jump_execution",
    "rc",
    "formations_transitions",
    "dance_difficulty",
    "dance_execution",
    "show",
]


def build_performances_table(
    merged_records: list[dict],
    competition_id: str,
) -> pd.DataFrame:
    """
    Convert validated merged score records into
    the performances fact table.
    """

    df = pd.DataFrame(
        merged_records
    )

    df.insert(
        0,
        "competition_id",
        competition_id,
    )

    df["division_id"] = df["division"].apply(
        lambda value: parse_division_name(
            value
        )["division_id"]
    )

    df["team_id"] = df.apply(
        lambda row: make_team_id(
            row["program_name"],
            row["team_name"],
        ),
        axis=1,
    )

    numeric_columns = [
        "rank",
        "raw_score",
        "deductions",
        "performance_score",
        "event_score",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df[
        PERFORMANCE_COLUMNS
    ]

    return df


def build_divisions_table(
    merged_records: list[dict],
) -> pd.DataFrame:
    """
    Build one row per unique division from
    validated merged score records.
    """

    unique_divisions = list(
        dict.fromkeys(
            record["division"]
            for record in merged_records
        )
    )

    parsed_divisions = [
        parse_division_name(division)
        for division in unique_divisions
    ]

    divisions = pd.DataFrame(
        parsed_divisions
    )

    return divisions


def save_performances_table(
    df: pd.DataFrame,
    competition_id: str,
) -> Path:
    """
    Save one competition's performances to processed data.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DIR
        / f"{competition_id}_performances.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return output_path


def save_divisions_table(
    df: pd.DataFrame,
    competition_id: str,
) -> Path:
    """
    Save one competition's division dimension table.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DIR
        / f"{competition_id}_divisions.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return output_path