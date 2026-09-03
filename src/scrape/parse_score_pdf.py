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


def detect_round(page) -> str:
    """Detect the competition round from the PDF page text."""
    text = page.extract_text() or ""

    if re.search(r"\bPrelims\b", text, re.IGNORECASE):
        return "Prelims"

    if re.search(r"\bFinals\b", text, re.IGNORECASE):
        return "Finals"

    return "Unknown"


def split_score_pair(value: str) -> tuple[float | None, float | None]:
    """
    Split a paired Varsity score into difficulty and execution.

    Example:
        '4.50 | 3.70'
        -> (4.50, 3.70)
    """
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
    """
    Extract the first numeric value from a single-score field.

    Example:
        '0.80 | --'
        -> 0.80
    """
    if not value:
        return None

    first = value.split("|")[0].strip()

    try:
        return float(first)
    except ValueError:
        return None


def parse_score_pdf(pdf_path: str) -> list[dict]:
    """Extract structured scoring records from a Varsity PDF."""
    records = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            round_name = detect_round(page)

            tables = page.extract_tables()

            for table in tables:

                # Skip the header row.
                for row in table[1:]:

                    if len(row) != len(COLUMN_NAMES):
                        continue

                    cleaned_row = [
                        clean_cell(value)
                        for value in row
                    ]

                    raw = dict(
                        zip(
                            COLUMN_NAMES,
                            cleaned_row,
                        )
                    )

                    stunt_difficulty, stunt_execution = (
                        split_score_pair(raw["stunt"])
                    )

                    pyr_difficulty, pyr_execution = (
                        split_score_pair(raw["pyr"])
                    )

                    toss_difficulty, toss_execution = (
                        split_score_pair(raw["toss"])
                    )

                    standing_tumbling_difficulty, standing_tumbling_execution = (
                        split_score_pair(raw["st"])
                    )

                    running_tumbling_difficulty, running_tumbling_execution = (
                        split_score_pair(raw["rt"])
                    )

                    jump_difficulty, jump_execution = (
                        split_score_pair(raw["jump"])
                    )

                    dance_difficulty, dance_execution = (
                        split_score_pair(raw["dance"])
                    )

                    record = {
                        "round": round_name,
                        "team_name_raw": raw["team_name_raw"],

                        "stunt_difficulty": stunt_difficulty,
                        "stunt_execution": stunt_execution,
                        "stunt_dod": get_single_score(
                            raw["stunt_dod"]
                        ),
                        "stunt_max": get_single_score(
                            raw["stunt_max"]
                        ),

                        "pyramid_difficulty": pyr_difficulty,
                        "pyramid_execution": pyr_execution,

                        "toss_difficulty": toss_difficulty,
                        "toss_execution": toss_execution,

                        "standing_tumbling_difficulty":
                            standing_tumbling_difficulty,
                        "standing_tumbling_execution":
                            standing_tumbling_execution,
                        "standing_tumbling_dod": get_single_score(
                            raw["st_dod"]
                        ),

                        "running_tumbling_difficulty":
                            running_tumbling_difficulty,
                        "running_tumbling_execution":
                            running_tumbling_execution,
                        "running_tumbling_dod": get_single_score(
                            raw["rt_dod"]
                        ),
                        "running_tumbling_max": get_single_score(
                            raw["rt_max"]
                        ),

                        "jump_difficulty": jump_difficulty,
                        "jump_execution": jump_execution,

                        "rc": get_single_score(
                            raw["rc"]
                        ),
                        "formations_transitions": get_single_score(
                            raw["formations_transitions"]
                        ),

                        "dance_difficulty": dance_difficulty,
                        "dance_execution": dance_execution,

                        "show": get_single_score(
                            raw["show"]
                        ),
                    }

                    records.append(record)

    return records


if __name__ == "__main__":
    records = parse_score_pdf(
        "data/raw/l3_youth_flex_small.pdf"
    )

    print(f"Found {len(records)} score records")

    for record in records:
        print()
        print(
            f"{record['round']} | "
            f"{record['team_name_raw']} | "
            f"Stunt D: {record['stunt_difficulty']} | "
            f"Stunt E: {record['stunt_execution']} | "
            f"PYR D: {record['pyramid_difficulty']} | "
            f"PYR E: {record['pyramid_execution']} | "
            f"ST D: {record['standing_tumbling_difficulty']} | "
            f"ST E: {record['standing_tumbling_execution']} | "
            f"RT D: {record['running_tumbling_difficulty']} | "
            f"RT E: {record['running_tumbling_execution']}"
        )