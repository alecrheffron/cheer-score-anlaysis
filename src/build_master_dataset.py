from pathlib import Path

import pandas as pd


BASE_DIR = Path(
    "data/processed/season_2026_events"
)

OUTPUT_PATH = Path(
    "data/processed/"
    "season_2026_all_levels_performances.csv"
)

LEVEL_DIRS = {
    "1": BASE_DIR / "level_1",
    "2": BASE_DIR / "level_2",
    "3": BASE_DIR,
    "4": BASE_DIR / "level_4",
    "4.2": BASE_DIR / "level_4_2",
    "5": BASE_DIR / "level_5",
    "6": BASE_DIR / "level_6",
}


def load_level(
    level: str,
    directory: Path,
) -> pd.DataFrame:
    performance_files = sorted(
        directory.glob("*_performances.csv")
    )

    if not performance_files:
        raise FileNotFoundError(
            f"No performance files found for "
            f"Level {level}: {directory}"
        )

    event_frames = []

    for performance_path in performance_files:
        division_path = performance_path.with_name(
            performance_path.name.replace(
                "_performances.csv",
                "_divisions.csv",
            )
        )

        if not division_path.exists():
            raise FileNotFoundError(
                f"Missing division file for "
                f"{performance_path.name}"
            )

        performances = pd.read_csv(
            performance_path,
            dtype={
                "competition_id": "string",
                "division_id": "string",
                "team_id": "string",
                "round": "string",
            },
        )

        divisions = pd.read_csv(
            division_path,
            dtype={
                "division_id": "string",
            },
        )

        division_cols = [
            "division_id",
            "division_name_raw",
            "age_group",
            "size",
            "is_coed",
            "is_flex",
            "is_d2",
            "division_split",
        ]

        divisions = (
            divisions[division_cols]
            .drop_duplicates()
        )

        duplicate_ids = (
            divisions["division_id"]
            .duplicated(
                keep=False
            )
        )

        if duplicate_ids.any():
            print()
            print(
                "CONFLICTING DIVISION METADATA"
            )
            print(
                divisions.loc[
                    duplicate_ids
                ]
                .sort_values(
                    "division_id"
                )
                .to_string(
                    index=False
                )
            )

            raise ValueError(
                "A division_id maps to multiple "
                "metadata rows within an event: "
                f"{division_path}"
            )

        merged = performances.merge(
            divisions,
            on="division_id",
            how="left",
            validate="many_to_one",
        )

        missing_metadata = (
            merged[
                "division_name_raw"
            ]
            .isna()
            .sum()
        )

        if missing_metadata:
            raise ValueError(
                f"{missing_metadata} performance "
                f"row(s) missing division metadata "
                f"in {performance_path}"
            )

        merged["level"] = level

        event_frames.append(
            merged
        )

    level_df = pd.concat(
        event_frames,
        ignore_index=True,
    )

    return level_df


def add_scoring_context(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = df.copy()

    no_toss = (
        (df["level"] == "1")
        | (
            (df["level"] == "2")
            & (
                df["age_group"]
                == "Mini"
            )
        )
    )

    df["toss_applicable"] = ~no_toss

    df["scorecard_max"] = (
        df["toss_applicable"]
        .map(
            {
                True: 50.0,
                False: 46.0,
            }
        )
    )

    df["scoring_schema"] = (
        df["toss_applicable"]
        .map(
            {
                True: "standard_50",
                False: "no_toss_46",
            }
        )
    )

    return df


def validate_master(
    df: pd.DataFrame,
) -> None:
    key = [
        "competition_id",
        "division_id",
        "team_id",
        "round",
    ]

    duplicate_keys = (
        df.duplicated(
            key
        )
        .sum()
    )

    if duplicate_keys:
        raise ValueError(
            f"{duplicate_keys} duplicate "
            "performance key row(s) found"
        )

    no_toss = (
        ~df["toss_applicable"]
    )

    bad_no_toss = (
        df.loc[
            no_toss,
            [
                "toss_difficulty",
                "toss_execution",
            ],
        ]
        .notna()
        .any(axis=1)
        .sum()
    )

    if bad_no_toss:
        raise ValueError(
            f"{bad_no_toss} no-toss "
            "performance(s) contain toss scores"
        )

    bad_standard_toss = (
        df.loc[
            ~no_toss,
            [
                "toss_difficulty",
                "toss_execution",
            ],
        ]
        .isna()
        .any(axis=1)
        .sum()
    )

    if bad_standard_toss:
        raise ValueError(
            f"{bad_standard_toss} standard-scorecard "
            "performance(s) are missing toss scores"
        )


def main() -> None:
    frames = []

    print()
    print("=" * 72)
    print("BUILDING ALL-LEVEL MASTER DATASET")
    print("=" * 72)

    for level, directory in (
        LEVEL_DIRS.items()
    ):
        df = load_level(
            level,
            directory,
        )

        frames.append(df)

        print(
            f"Level {level:<3} | "
            f"{len(df):>6,} rows | "
            f"{df['competition_id'].nunique():>3} "
            "competitions"
        )

    master = pd.concat(
        frames,
        ignore_index=True,
    )

    master = add_scoring_context(
        master
    )

    validate_master(
        master
    )

    preferred_columns = [
        "competition_id",
        "division_id",
        "team_id",
        "level",
        "division_name_raw",
        "age_group",
        "size",
        "is_coed",
        "is_flex",
        "is_d2",
        "division_split",
        "round",
        "program_name",
        "team_name",
        "rank",
        "raw_score",
        "deductions",
        "performance_score",
        "event_score",
        "toss_applicable",
        "scorecard_max",
        "scoring_schema",
    ]

    remaining_columns = [
        col
        for col in master.columns
        if col not in preferred_columns
    ]

    master = master[
        preferred_columns
        + remaining_columns
    ]

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    master.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("=" * 72)
    print("MASTER DATASET QA")
    print("=" * 72)

    print(
        "Rows:",
        f"{len(master):,}",
    )
    print(
        "Competitions:",
        master[
            "competition_id"
        ].nunique(),
    )
    print(
        "Teams:",
        master[
            "team_id"
        ].nunique(),
    )
    print(
        "Division IDs:",
        master[
            "division_id"
        ].nunique(),
    )

    print()
    print("ROWS BY LEVEL")
    print(
        master[
            "level"
        ]
        .value_counts(
            sort=False
        )
        .reindex(
            LEVEL_DIRS.keys()
        )
    )

    print()
    print("SCORING SCHEMAS")
    print(
        master[
            "scoring_schema"
        ]
        .value_counts()
    )

    print()
    print(
        "Duplicate performance keys:",
        master.duplicated(
            [
                "competition_id",
                "division_id",
                "team_id",
                "round",
            ]
        ).sum(),
    )

    print()
    print(
        "Saved:",
        OUTPUT_PATH,
    )


if __name__ == "__main__":
    main()
