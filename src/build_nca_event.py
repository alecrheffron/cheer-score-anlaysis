from clean.build_event_tables import (
    build_divisions_table,
    build_performances_table,
    save_divisions_table,
    save_performances_table,
)

from clean.build_competition import (
    build_competition_table,
    save_competition_table,
)

from scrape.scrape_level3_event import (
    scrape_level3_event,
)


COMPETITION_ID = (
    "nca_all_star_nationals_2026"
)

COMPETITION_NAME = (
    "2026 NCA All-Star National Championship"
)

SEASON = 2026

START_DATE = "2026-02-27"
END_DATE = "2026-03-01"

CITY = "Dallas"
STATE = "TX"

EVENT_TIER = "National"
EVENT_SIZE = "Very Large"
JUDGING_POOL_TYPE = "National/Mixed"
LOCATION_REGION = "Southwest"


def main() -> None:

    merged_records, unmatched_records = (
        scrape_level3_event()
    )

    if unmatched_records:
        raise RuntimeError(
            "Cannot build processed table: "
            "unmatched records remain."
        )

    performances = (
        build_performances_table(
            merged_records,
            COMPETITION_ID,
        )
    )

    output_path = (
        save_performances_table(
            performances,
            COMPETITION_ID,
        )
    )

    divisions = build_divisions_table(
        merged_records
    )

    divisions_output_path = (
        save_divisions_table(
            divisions,
            COMPETITION_ID,
        )
    )

    competition = build_competition_table(
        competition_id=COMPETITION_ID,
        competition_name=COMPETITION_NAME,
        season=SEASON,
        start_date=START_DATE,
        end_date=END_DATE,
        city=CITY,
        state=STATE,
        event_tier=EVENT_TIER,
        event_size=EVENT_SIZE,
        judging_pool_type=JUDGING_POOL_TYPE,
        location_region=LOCATION_REGION,
    )

    competition_output_path = (
        save_competition_table(
            competition,
            COMPETITION_ID,
        )
    )

    print()
    print("=" * 80)
    print("PERFORMANCES TABLE")
    print("=" * 80)

    print(
        f"Rows:    {len(performances)}"
    )

    print(
        f"Columns: {len(performances.columns)}"
    )

    print(
        f"Saved:   {output_path}"
    )

    print()

    print(
        performances.head()
    )

    print()
    print("=" * 80)
    print("DIVISIONS TABLE")
    print("=" * 80)

    print(
        f"Rows:  {len(divisions)}"
    )

    print(
        f"Saved: {divisions_output_path}"
    )

    print()

    print(
        divisions
    )

    print()
    print("=" * 80)
    print("COMPETITION TABLE")
    print("=" * 80)

    print(
        f"Rows:  {len(competition)}"
    )

    print(
        f"Saved: {competition_output_path}"
    )

    print()

    print(
        competition
    )


if __name__ == "__main__":
    main()