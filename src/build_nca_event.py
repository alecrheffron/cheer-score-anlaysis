from clean.build_event_tables import (
    build_divisions_table,
    build_performances_table,
    save_divisions_table,
    save_performances_table,
)

from scrape.scrape_level3_event import (
    scrape_level3_event,
)


COMPETITION_ID = (
    "nca_all_star_nationals_2026"
)


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


if __name__ == "__main__":
    main()