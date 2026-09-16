def validate_event_tables(
    performances,
    divisions,
    competition,
    teams,
) -> None:
    """
    Validate relationships between event tables.

    Raises ValueError if any relational integrity
    check fails.
    """

    errors = []

    # --------------------------------------------------
    # Competition foreign key check
    # --------------------------------------------------

    valid_competition_ids = set(
        competition["competition_id"]
    )

    invalid_competition_ids = set(
        performances["competition_id"]
    ) - valid_competition_ids

    if invalid_competition_ids:
        errors.append(
            "Performances contain invalid "
            f"competition IDs: "
            f"{invalid_competition_ids}"
        )

    # --------------------------------------------------
    # Division foreign key check
    # --------------------------------------------------

    valid_division_ids = set(
        divisions["division_id"]
    )

    invalid_division_ids = set(
        performances["division_id"]
    ) - valid_division_ids

    if invalid_division_ids:
        errors.append(
            "Performances contain invalid "
            f"division IDs: "
            f"{invalid_division_ids}"
        )

    # --------------------------------------------------
    # Team foreign key check
    # --------------------------------------------------

    valid_team_ids = set(
        teams["team_id"]
    )

    invalid_team_ids = set(
        performances["team_id"]
    ) - valid_team_ids

    if invalid_team_ids:
        errors.append(
            "Performances contain invalid "
            f"team IDs: "
            f"{invalid_team_ids}"
        )

    # --------------------------------------------------
    # Dimension primary-key uniqueness
    # --------------------------------------------------

    if competition["competition_id"].duplicated().any():
        errors.append(
            "Duplicate competition IDs found."
        )

    if divisions["division_id"].duplicated().any():
        errors.append(
            "Duplicate division IDs found."
        )

    if teams["team_id"].duplicated().any():
        errors.append(
            "Duplicate team IDs found."
        )

    # --------------------------------------------------
    # Performance uniqueness
    # --------------------------------------------------

    performance_key = [
        "competition_id",
        "division_id",
        "team_id",
        "round",
    ]

    duplicate_performances = (
        performances.duplicated(
            subset=performance_key,
            keep=False,
        )
    )

    if duplicate_performances.any():
        duplicate_rows = performances.loc[
            duplicate_performances,
            performance_key,
        ]

        errors.append(
            "Duplicate performance records found:\n"
            f"{duplicate_rows}"
        )

    # --------------------------------------------------
    # Null key checks
    # --------------------------------------------------

    key_columns = [
        "competition_id",
        "division_id",
        "team_id",
        "round",
    ]

    null_keys = (
        performances[key_columns]
        .isna()
        .sum()
    )

    if null_keys.any():
        errors.append(
            "Null performance keys found:\n"
            f"{null_keys[null_keys > 0]}"
        )

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    if errors:
        raise ValueError(
            "\n\n".join(errors)
        )