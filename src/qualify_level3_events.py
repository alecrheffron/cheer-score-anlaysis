import time
from pathlib import Path

import pandas as pd

from scrape.fetch_event import (
    fetch_event_page,
    find_divisions,
)
from scrape.scrape_level3_event import (
    get_level3_divisions,
)


INPUT_PATH = Path(
    "data/interim/season_2026_events.csv"
)

OUTPUT_PATH = Path(
    "data/interim/season_2026_level3_events.csv"
)

REQUEST_DELAY = 0.5
MAX_ATTEMPTS = 3


def get_qualified_divisions(
    event_url: str,
) -> tuple[list[str], int]:
    """
    Fetch an event page with retries and return
    its standard Level 3 divisions.

    Repeated fetches protect season qualification
    from transient or incomplete Varsity responses.
    """

    observations = []

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1,
    ):
        html = fetch_event_page(
            event_url
        )

        all_divisions = find_divisions(
            html
        )

        level3_divisions = (
            get_level3_divisions(
                event_url,
                html=html,
            )
        )

        observation = (
            tuple(all_divisions),
            tuple(level3_divisions),
        )

        observations.append(
            observation
        )

        # A populated division list is usable
        # immediately. Empty lists are retried
        # because Varsity can occasionally return
        # incomplete results-page content.
        if all_divisions:
            return (
                level3_divisions,
                len(all_divisions),
            )

        if attempt < MAX_ATTEMPTS:
            time.sleep(
                REQUEST_DELAY
            )

    # Three successful HTTP responses containing
    # no divisions are treated as a genuine
    # no-results/no-division page.
    if (
        observations
        and all(
            observation == observations[0]
            for observation in observations
        )
    ):
        return [], 0

    raise RuntimeError(
        "Inconsistent division discovery "
        "across qualification attempts"
    )


def qualify_level3_events() -> pd.DataFrame:
    """
    Check discovered season events and keep only
    events containing standard Level 3 divisions.
    """

    events = pd.read_csv(
        INPUT_PATH,
        dtype={"event_id": str},
    )

    print(
        f"Loaded {len(events)} discovered events"
    )
    print("=" * 80)

    qualified_events = []
    error_events = []

    for index, row in events.iterrows():

        event_url = row["results_url"]

        print(
            f"[{index + 1}/{len(events)}] "
            f"{row['event_id']}",
            end="",
            flush=True,
        )

        try:

            (
                divisions,
                all_division_count,
            ) = get_qualified_divisions(
                event_url
            )

            if divisions:

                qualified_row = row.to_dict()

                qualified_row[
                    "level3_division_count"
                ] = len(divisions)

                qualified_row[
                    "level3_divisions"
                ] = " | ".join(divisions)

                qualified_events.append(
                    qualified_row
                )

                print(
                    f"  KEEP — "
                    f"{len(divisions)} L3 divisions"
                )

            else:

                print(
                    "  skip — no standard L3 "
                    f"({all_division_count} "
                    "total divisions)"
                )

        except Exception as exc:

            print(
                f"  ERROR — "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            error_events.append(
                {
                    "event_id":
                        row["event_id"],
                    "results_url":
                        event_url,
                    "error_type":
                        type(exc).__name__,
                    "error_message":
                        str(exc),
                }
            )

        time.sleep(
            REQUEST_DELAY
        )

    qualified_df = pd.DataFrame(
        qualified_events
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    qualified_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("=" * 80)
    print("LEVEL 3 SEASON QUALIFICATION")
    print("=" * 80)

    print(
        f"Events checked:      "
        f"{len(events)}"
    )

    print(
        f"Level 3 events:      "
        f"{len(qualified_df)}"
    )

    print(
        f"Events skipped:      "
        f"{len(events) - len(qualified_df) - len(error_events)}"
    )

    print(
        f"Errors:              "
        f"{len(error_events)}"
    )

    if not qualified_df.empty:

        print(
            f"Total L3 divisions:  "
            f"{qualified_df['level3_division_count'].sum()}"
        )

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )

    error_path = Path(
        "data/interim/"
        "season_2026_level3_qualification_errors.csv"
    )

    if error_events:

        pd.DataFrame(
            error_events
        ).to_csv(
            error_path,
            index=False,
        )

        print(
            f"Errors saved: {error_path}"
        )

    elif error_path.exists():

        error_path.unlink()

    return qualified_df


if __name__ == "__main__":

    qualify_level3_events()