#!/usr/bin/env python3

import csv
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

SUMMARY_CSV = (
    SCRIPT_DIR
    / "FPS_analysis_summary.csv"
)


def number(value):

    try:

        value = float(value)

        if math.isfinite(value):
            return value

    except (TypeError, ValueError):
        pass

    return math.nan


def main():

    if not SUMMARY_CSV.is_file():

        print(
            f"ERROR: Missing {SUMMARY_CSV.name}. "
            "Run 006.collect_FPS_results.py first."
        )

        sys.exit(1)

    with SUMMARY_CSV.open(
        newline="",
    ) as handle:

        rows = list(
            csv.DictReader(handle)
        )

    if not rows:

        print(
            f"ERROR: {SUMMARY_CSV.name} "
            "contains no completed results."
        )

        sys.exit(1)

    rows.sort(
        key=lambda row: number(
            row["cutoff"]
        )
    )

    print()
    print(
        "FPS Similarity Island cutoff experiment"
    )
    print()

    print(
        "Cutoff  Islands  Largest  Mean size  "
        "Singletons  FPS calculations  Time (s)"
    )

    for row in rows:

        calculations = row.get(
            "total_fps_calculations",
            "",
        )

        try:
            calculations = str(
                int(float(calculations))
            )
        except (TypeError, ValueError):
            calculations = "NA"

        print(
            f"{number(row['cutoff']):>6.2f} "
            f"{int(float(row['total_islands'])):>8d} "
            f"{int(float(row['largest_island'])):>8d} "
            f"{number(row['mean_island_size']):>10.2f} "
            f"{int(float(row['singleton_islands'])):>10d} "
            f"{calculations:>16} "
            f"{number(row['elapsed_seconds']):>9.3f}"
        )

    print()
    print("Experimental variables available:")
    print()
    print("  cutoff vs total_islands")
    print("  cutoff vs largest_island")
    print("  cutoff vs mean_island_size")
    print("  cutoff vs median_island_size")
    print("  cutoff vs singleton_islands")
    print("  cutoff vs singleton_fraction")
    print("  cutoff vs total_fps_calculations")
    print(
        "  cutoff vs "
        "average_fps_calculations_per_island"
    )
    print("  cutoff vs elapsed_seconds")
    print("  cutoff vs molecules_per_second")
    print("  cutoff vs virtual_memory_kb")
    print("  cutoff vs physical_memory_kb")
    print()


if __name__ == "__main__":
    main()
