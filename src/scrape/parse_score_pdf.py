import re

import pdfplumber


COLUMN_NAMES = [
    "team_name_raw",
    "stunt",
    "stunt_dod",
    "stunt_max",
    "pyr",
    "toss",
    "st",
    "st_dod",
    "rt",
    "rt_dod",
    "rt_max",
    "jump",
    "rc",
    "formations_transitions",
    "dance",
    "show",
]


def clean_cell(value: str | None) -> str:
    """Clean whitespace while preserving score values."""
    if value is None:
        return ""

    return " ".join(value.split())


def detect_round(page) -> str | None:
    """
    Detect a competition round explicitly printed on a PDF page.

    Returns None when the page is a continuation page that does not
    repeat the Prelims/Finals heading.
    """
    text = page.extract_text() or ""

    if re.search(r"\bPrelims\b", text, re.IGNORECASE):
        return "Prelims"

    if re.search(r"\bFinals\b", text, re.IGNORECASE):
        return "Finals"

    return None


def split_score_pair(
    value: str,
) -> tuple[float | None, float | None]:
    """Split a paired Varsity score into difficulty and execution."""
    if not value:
        return None, None

    parts = value.split("|")

    difficulty = None
    execution = None

    if len(parts) >= 1:
        first = parts[0].strip()

        try:
            difficulty = float(first)
        except ValueError:
            difficulty = None

    if len(parts) >= 2:
        second = parts[1].strip()

        try:
            execution = float(second)
        except ValueError:
            execution = None

    return difficulty, execution


def get_single_score(value: str) -> float | None:
    """Extract the first numeric value from a single-score field."""
    if not value:
        return None

    first = value.split("|")[0].strip()

    try:
        return float(first)
    except ValueError:
        return None

def normalize_table_row(
    row: list[str | None],
) -> list[str | None]:
    """
    Normalize pdfplumber table rows to the standard
    16-column Varsity scoring schema.

    Some pages are extracted with an empty padding
    column on both the left and right sides, producing
    18 columns instead of 16.
    """
    if (
        len(row) == 18
        and not clean_cell(row[0])
        and not clean_cell(row[-1])
    ):
        return row[1:-1]

    return row

def valid_team_row(
    cleaned_row: list[str],
) -> bool:
    """
    Reject headers, footers, blank rows, and malformed table fragments.
    """
    if len(cleaned_row) != len(COLUMN_NAMES):
        return False

    team_name = cleaned_row[0].strip()

    if not team_name:
        return False

    invalid_names = {
        "team name",
        "nca",
    }

    if team_name.lower() in invalid_names:
        return False

    # A real team row should have a parseable Stunt difficulty score.
    stunt_difficulty, _ = split_score_pair(
        cleaned_row[1]
    )

    if stunt_difficulty is None:
        return False

    return True

def merge_split_team_records(
    records: list[dict],
) -> list[dict]:
    """
    Repair score rows that pdfplumber splits across PDF pages.

    In these broken rows:
    - the first fragment contains the team-name prefix,
      difficulty scores, and single-value fields.
    - the second fragment contains the team-name suffix,
      with execution scores shifted into the difficulty fields.
    """
    merged = []
    i = 0

    execution_fields = [
        (
            "stunt_execution",
            "stunt_difficulty",
        ),
        (
            "pyramid_execution",
            "pyramid_difficulty",
        ),
        (
            "toss_execution",
            "toss_difficulty",
        ),
        (
            "standing_tumbling_execution",
            "standing_tumbling_difficulty",
        ),
        (
            "running_tumbling_execution",
            "running_tumbling_difficulty",
        ),
        (
            "jump_execution",
            "jump_difficulty",
        ),
        (
            "dance_execution",
            "dance_difficulty",
        ),
    ]

    single_value_fields = [
        "stunt_dod",
        "stunt_max",
        "standing_tumbling_dod",
        "running_tumbling_dod",
        "running_tumbling_max",
        "rc",
        "formations_transitions",
        "show",
    ]

    while i < len(records):

        current = records[i]

        if i + 1 < len(records):

            next_record = records[i + 1]

            same_round = (
                current["round"]
                == next_record["round"]
            )

            current_missing_execution = all(
                current[field] is None
                for field, _ in execution_fields
            )

            next_missing_execution = all(
                next_record[field] is None
                for field, _ in execution_fields
            )

            next_missing_single_values = all(
                next_record[field] is None
                for field in single_value_fields
            )

            if (
                same_round
                and current_missing_execution
                and next_missing_execution
                and next_missing_single_values
            ):
                repaired = current.copy()

                repaired["team_name_raw"] = (
                    f"{current['team_name_raw'].strip()} "
                    f"{next_record['team_name_raw'].strip()}"
                )

                for (
                    execution_field,
                    shifted_field,
                ) in execution_fields:

                    repaired[execution_field] = (
                        next_record[shifted_field]
                    )

                merged.append(repaired)

                i += 2
                continue

        merged.append(current)

        i += 1

    return merged

def parse_score_pdf(pdf_path: str) -> list[dict]:
    """Extract structured scoring records from a Varsity PDF."""
    records = []

    current_round = None

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            detected_round = detect_round(page)

            # If this page explicitly identifies a round,
            # update our current state.
            if detected_round is not None:
                current_round = detected_round

            tables = page.extract_tables()

            for table in tables:

                if not table:
                    continue

                for row in table:

                    row = normalize_table_row(row)

                    if len(row) != len(COLUMN_NAMES):
                        continue

                    cleaned_row = [
                        clean_cell(value)
                        for value in row
                    ]

                    if not valid_team_row(
                        cleaned_row
                    ):
                        continue

                    raw = dict(
                        zip(
                            COLUMN_NAMES,
                            cleaned_row,
                        )
                    )

                    stunt_difficulty, stunt_execution = (
                        split_score_pair(
                            raw["stunt"]
                        )
                    )

                    pyr_difficulty, pyr_execution = (
                        split_score_pair(
                            raw["pyr"]
                        )
                    )

                    toss_difficulty, toss_execution = (
                        split_score_pair(
                            raw["toss"]
                        )
                    )

                    (
                        standing_tumbling_difficulty,
                        standing_tumbling_execution,
                    ) = split_score_pair(
                        raw["st"]
                    )

                    (
                        running_tumbling_difficulty,
                        running_tumbling_execution,
                    ) = split_score_pair(
                        raw["rt"]
                    )

                    jump_difficulty, jump_execution = (
                        split_score_pair(
                            raw["jump"]
                        )
                    )

                    dance_difficulty, dance_execution = (
                        split_score_pair(
                            raw["dance"]
                        )
                    )

                    record = {
                        "round": (
                            current_round
                            if current_round
                            else "Unknown"
                        ),
                        "team_name_raw": raw[
                            "team_name_raw"
                        ],

                        "stunt_difficulty":
                            stunt_difficulty,
                        "stunt_execution":
                            stunt_execution,
                        "stunt_dod":
                            get_single_score(
                                raw["stunt_dod"]
                            ),
                        "stunt_max":
                            get_single_score(
                                raw["stunt_max"]
                            ),

                        "pyramid_difficulty":
                            pyr_difficulty,
                        "pyramid_execution":
                            pyr_execution,

                        "toss_difficulty":
                            toss_difficulty,
                        "toss_execution":
                            toss_execution,

                        "standing_tumbling_difficulty":
                            standing_tumbling_difficulty,
                        "standing_tumbling_execution":
                            standing_tumbling_execution,
                        "standing_tumbling_dod":
                            get_single_score(
                                raw["st_dod"]
                            ),

                        "running_tumbling_difficulty":
                            running_tumbling_difficulty,
                        "running_tumbling_execution":
                            running_tumbling_execution,
                        "running_tumbling_dod":
                            get_single_score(
                                raw["rt_dod"]
                            ),
                        "running_tumbling_max":
                            get_single_score(
                                raw["rt_max"]
                            ),

                        "jump_difficulty":
                            jump_difficulty,
                        "jump_execution":
                            jump_execution,

                        "rc":
                            get_single_score(
                                raw["rc"]
                            ),

                        "formations_transitions":
                            get_single_score(
                                raw[
                                    "formations_transitions"
                                ]
                            ),

                        "dance_difficulty":
                            dance_difficulty,
                        "dance_execution":
                            dance_execution,

                        "show":
                            get_single_score(
                                raw["show"]
                            ),
                    }

                    records.append(record)

    return merge_split_team_records(
        records
    )


if __name__ == "__main__":

    test_pdfs = [
        (
            "data/raw/score_breakdowns/"
            "l3_junior_d2_small_a.pdf"
        ),
        (
            "data/raw/score_breakdowns/"
            "l3_junior_d2_small_b.pdf"
        ),
        (
            "data/raw/score_breakdowns/"
            "l3_senior_small.pdf"
        ),
    ]

    split_names = {
        "Quest Athletics",
        "Generals",
        "Southern Athletics",
        "Punches",
        "GymTyme Illinois",
        "Gossip",
    }

    for pdf_path in test_pdfs:

        print()
        print("=" * 80)
        print(pdf_path)
        print("=" * 80)

        records = parse_score_pdf(
            pdf_path
        )

        for record in records:

            if record["team_name_raw"] in split_names:
                print()
                print(record)