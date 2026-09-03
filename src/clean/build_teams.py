from pathlib import Path
import re

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def make_team_id(
    program_name: str,
    team_name: str,
) -> str:
    """
    Create a stable team ID from program and team name.
    """

    combined_name = (
        f"{program_name}_{team_name}"
    )

    team_id = re.sub(
        r"[^a-z0-9]+",
        "_",
        combined_name.lower(),
    ).strip("_")

    return team_id


def build_teams_table(
    merged_records: list[dict],
) -> pd.DataFrame:
    """
    Build one row per unique program/team combination.
    """

    teams = {}

    for record in merged_records:

        program_name = record["program_name"]
        team_name = record["team_name"]

        team_id = make_team_id(
            program_name,
            team_name,
        )

        teams[team_id] = {
            "team_id": team_id,
            "program_name": program_name,
            "team_name": team_name,
        }

    return pd.DataFrame(
        teams.values()
    )


def save_teams_table(
    df: pd.DataFrame,
    competition_id: str,
) -> Path:
    """
    Save one competition's team dimension table.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DIR
        / f"{competition_id}_teams.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return output_path