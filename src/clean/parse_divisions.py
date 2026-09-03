import re

def parse_division_name(
    division: str,
) -> dict:
    """
    Parse a Varsity division name into standardized fields.

    Example:
        L3 Senior - D2 - Small - A
    """

    parts = [
        part.strip()
        for part in division.split("-")
    ]

    first_part = parts[0]

    level = int(
        first_part.split()[0]
        .replace("L", "")
    )

    age_group = (
        "Youth"
        if "Youth" in first_part
        else "Junior"
        if "Junior" in first_part
        else "Senior"
        if "Senior" in first_part
        else None
    )

    is_coed = "Coed" in division
    is_flex = "Flex" in division
    is_d2 = "D2" in division

    size = None

    for value in [
        "Small",
        "Medium",
        "Large",
    ]:
        if value in parts:
            size = value
            break

    division_split = None

    for value in [
        "A",
        "B",
        "C",
        "D",
    ]:
        if value in parts:
            division_split = value
            break

    division_id = re.sub(
        r"[^a-z0-9]+",
        "_",
        division.lower(),
    ).strip("_")

    return {
        "division_id": division_id,
        "division_name_raw": division,
        "level": level,
        "age_group": age_group,
        "size": size,
        "is_coed": is_coed,
        "is_flex": is_flex,
        "is_d2": is_d2,
        "division_split": division_split,
    }

if __name__ == "__main__":

    test_divisions = [
        "L3 Youth - D2",
        "L3 Youth - Flex - D2",
        "L3 Youth - Flex - Small",
        "L3 Youth - Small",
        "L3 Youth - Flex - Medium",
        "L3 Youth - Medium",
        "L3 Junior - Flex - D2 - A",
        "L3 Junior - Flex - D2 - B",
        "L3 Junior - D2 - Small - A",
        "L3 Junior - D2 - Small - B",
        "L3 Junior - Flex - Small",
        "L3 Junior - Small",
        "L3 Junior - D2 - Medium",
        "L3 Junior - Flex - Medium",
        "L3 Junior - Medium",
        "L3 Senior Coed",
        "L3 Senior - D2 - Small - A",
        "L3 Senior - D2 - Small - B",
        "L3 Senior - Small",
        "L3 Senior Coed - D2 - Small",
        "L3 Senior - D2 - Medium",
        "L3 Senior - Medium",
        "L3 Senior Coed - D2 - Medium",
    ]

    for division in test_divisions:
        print(
            parse_division_name(
                division
            )
        )