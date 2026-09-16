from pathlib import Path

import pandas as pd


PROCESSED_DIR = Path("data/processed")


def build_competition_table(
    competition_id: str,
    competition_name: str,
    season: int,
    start_date: str,
    end_date: str,
    city: str,
    state: str,
    event_tier: str,
    event_size: str,
    judging_pool_type: str,
    location_region: str,
) -> pd.DataFrame:
    """
    Build one competition dimension record.
    """

    competition = {
        "competition_id": competition_id,
        "competition_name": competition_name,
        "season": season,
        "start_date": start_date,
        "end_date": end_date,
        "city": city,
        "state": state,
        "event_tier": event_tier,
        "event_size": event_size,
        "judging_pool_type": judging_pool_type,
        "location_region": location_region,
    }

    return pd.DataFrame(
        [competition]
    )


def save_competition_table(
    df: pd.DataFrame,
    competition_id: str,
) -> Path:
    """
    Save one competition dimension table.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DIR
        / f"{competition_id}_competition.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return output_path