#!/usr/bin/env python3

import csv
import math
import re
import statistics
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

TASK_LIST = SCRIPT_DIR / "FPS_tasks.tsv"

STATUS_CSV = SCRIPT_DIR / "FPS_status.csv"
SUMMARY_CSV = SCRIPT_DIR / "FPS_analysis_summary.csv"
ISLAND_CSV = SCRIPT_DIR / "FPS_island_statistics.csv"


def mean(values):
    return statistics.mean(values) if values else math.nan


def median(values):
    return statistics.median(values) if values else math.nan


def pstdev(values):
    if len(values) > 1:
        return statistics.pstdev(values)

    if len(values) == 1:
        return 0.0

    return math.nan


def read_tasks():

    if not TASK_LIST.is_file():
        raise SystemExit(
            "ERROR: FPS_tasks.tsv not found. "
            "Run 002.make_task_list.sh first."
        )

    with TASK_LIST.open(newline="") as handle:
        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def parse_output(path):

    run = {
        "completed": False,
        "cutoff": math.nan,
        "molecules_to_cluster": 0,
        "molecules_clustered": 0,
        "total_islands": 0,
        "total_fps_calculations": 0,
        "average_fps_calculations_per_island": math.nan,
        "elapsed_seconds": math.nan,
        "molecules_per_second": math.nan,
        "virtual_memory_kb": 0,
        "physical_memory_kb": 0,
        "islands": [],
        "source_file": str(path),
    }

    current = None

    with path.open(
        "r",
        errors="replace",
    ) as handle:

        for raw_line in handle:

            line = raw_line.strip()

            match = re.match(
                r"^Similarity Cutoff:\s*([-+]?\d+(?:\.\d+)?)",
                line,
            )

            if match:
                run["cutoff"] = float(match.group(1))
                continue

            match = re.match(
                r"^Molecules to Cluster:\s*(\d+)",
                line,
            )

            if match:
                run["molecules_to_cluster"] = int(match.group(1))
                continue

            match = re.match(
                r"^FPS ISLAND\s+(\d+)",
                line,
                re.IGNORECASE,
            )

            if match:

                current = {
                    "island_id": int(match.group(1)),
                    "head": "",
                    "size": 0,
                }

                run["islands"].append(current)
                continue

            if current is not None:

                match = re.match(
                    r"^Island Head:\s+(\S+)",
                    line,
                )

                if match:
                    current["head"] = match.group(1)
                    continue

                match = re.match(
                    r"^Island Size:\s+(\d+)",
                    line,
                )

                if match:
                    current["size"] = int(match.group(1))
                    continue

            if line.startswith(
                "Similarity Island clustering complete"
            ):
                run["completed"] = True
                current = None
                continue

            match = re.match(
                r"^Molecules Clustered:\s*(\d+)",
                line,
            )

            if match:
                run["molecules_clustered"] = int(match.group(1))
                continue

            match = re.match(
                r"^Total Islands:\s*(\d+)",
                line,
            )

            if match:
                run["total_islands"] = int(match.group(1))
                continue

            match = re.match(
                r"^Total FPS Calculations:\s*(\d+)",
                line,
                re.IGNORECASE,
            )

            if match:
                run["total_fps_calculations"] = int(
                    match.group(1)
                )
                continue

            match = re.match(
                r"^Average FPS Calculations per Island:\s*"
                r"([-+]?\d+(?:\.\d+)?)",
                line,
                re.IGNORECASE,
            )

            if match:
                run[
                    "average_fps_calculations_per_island"
                ] = float(match.group(1))
                continue

            match = re.match(
                r"^Total elapsed time:\s*"
                r"([-+]?\d+(?:\.\d+)?)\s+seconds",
                line,
            )

            if match:
                run["elapsed_seconds"] = float(
                    match.group(1)
                )
                continue

            match = re.match(
                r"^Number of molecules per second:\s*"
                r"([-+]?\d+(?:\.\d+)?)",
                line,
            )

            if match:
                run["molecules_per_second"] = float(
                    match.group(1)
                )
                continue

            match = re.match(
                r"^Virtual memory used for this process:\s*"
                r"(\d+)\s+kilobytes",
                line,
            )

            if match:
                run["virtual_memory_kb"] = int(
                    match.group(1)
                )
                continue

            match = re.match(
                r"^Physical memory used for this process:\s*"
                r"(\d+)\s+kilobytes",
                line,
            )

            if match:
                run["physical_memory_kb"] = int(
                    match.group(1)
                )
                continue

    sizes = [
        island["size"]
        for island in run["islands"]
        if island["size"] > 0
    ]

    run["parsed_islands"] = len(sizes)

    run["largest_island"] = (
        max(sizes)
        if sizes
        else 0
    )

    run["smallest_island"] = (
        min(sizes)
        if sizes
        else 0
    )

    run["mean_island_size"] = mean(sizes)
    run["median_island_size"] = median(sizes)
    run["std_island_size"] = pstdev(sizes)

    run["singleton_islands"] = sum(
        size == 1
        for size in sizes
    )

    if sizes:
        run["singleton_fraction"] = (
            run["singleton_islands"]
            / len(sizes)
        )
    else:
        run["singleton_fraction"] = math.nan

    if run["molecules_clustered"] > 0:
        run["largest_island_fraction"] = (
            run["largest_island"]
            / run["molecules_clustered"]
        )
    else:
        run["largest_island_fraction"] = math.nan

    return run


def write_csv(path, fields, rows):

    with path.open(
        "w",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)


def main():

    tasks = read_tasks()

    status_rows = []
    successful_runs = []

    for task in tasks:

        case_name = task["case_name"]

        output_file = SCRIPT_DIR / f"{case_name}.out"
        summary_file = (
            SCRIPT_DIR
            / f"{case_name}_summary.out"
        )

        success_file = (
            SCRIPT_DIR
            / f".{case_name}.success"
        )

        failed_file = (
            SCRIPT_DIR
            / f".{case_name}.failed"
        )

        run = (
            parse_output(output_file)
            if output_file.is_file()
            else None
        )

        if (
            success_file.is_file()
            and run is not None
            and run["completed"]
            and summary_file.is_file()
            and summary_file.stat().st_size > 0
        ):
            status = "SUCCESS"

        elif failed_file.is_file():
            status = "FAILED"

        elif output_file.is_file():
            status = "INCOMPLETE"

        else:
            status = "MISSING"

        status_rows.append(
            {
                "task_id": task["task_id"],
                "cutoff": task["cutoff"],
                "case_name": case_name,
                "status": status,
                "total_islands": (
                    run["total_islands"]
                    if run
                    else ""
                ),
                "elapsed_seconds": (
                    run["elapsed_seconds"]
                    if run
                    else ""
                ),
                "output_file": str(output_file),
            }
        )

        if status == "SUCCESS":

            run["case_name"] = case_name
            successful_runs.append(run)

    write_csv(
        STATUS_CSV,
        [
            "task_id",
            "cutoff",
            "case_name",
            "status",
            "total_islands",
            "elapsed_seconds",
            "output_file",
        ],
        status_rows,
    )

    successful_runs.sort(
        key=lambda run: run["cutoff"]
    )

    summary_fields = [
        "cutoff",
        "molecules_to_cluster",
        "molecules_clustered",
        "total_islands",
        "parsed_islands",
        "largest_island",
        "smallest_island",
        "mean_island_size",
        "median_island_size",
        "std_island_size",
        "singleton_islands",
        "singleton_fraction",
        "largest_island_fraction",
        "total_fps_calculations",
        "average_fps_calculations_per_island",
        "elapsed_seconds",
        "molecules_per_second",
        "virtual_memory_kb",
        "physical_memory_kb",
        "case_name",
        "source_file",
    ]

    write_csv(
        SUMMARY_CSV,
        summary_fields,
        [
            {
                field: run.get(field, "")
                for field in summary_fields
            }
            for run in successful_runs
        ],
    )

    island_rows = []

    for run in successful_runs:

        for island in run["islands"]:

            island_rows.append(
                {
                    "cutoff": run["cutoff"],
                    "island_id": island["island_id"],
                    "island_head": island["head"],
                    "island_size": island["size"],
                }
            )

    write_csv(
        ISLAND_CSV,
        [
            "cutoff",
            "island_id",
            "island_head",
            "island_size",
        ],
        island_rows,
    )

    success = sum(
        row["status"] == "SUCCESS"
        for row in status_rows
    )

    failed = sum(
        row["status"] == "FAILED"
        for row in status_rows
    )

    incomplete = sum(
        row["status"] == "INCOMPLETE"
        for row in status_rows
    )

    missing = sum(
        row["status"] == "MISSING"
        for row in status_rows
    )

    print()
    print("FPS Similarity Island experiment")
    print()
    print(f"Total tasks: {len(status_rows)}")
    print(f"Successful:  {success}")
    print(f"Failed:      {failed}")
    print(f"Incomplete:  {incomplete}")
    print(f"Missing:     {missing}")
    print()

    if successful_runs:

        print(
            "Cutoff  Islands  Largest  Mean size  "
            "Singletons  Time (s)"
        )

        for run in successful_runs:

            print(
                f"{run['cutoff']:>6.2f} "
                f"{run['total_islands']:>8d} "
                f"{run['largest_island']:>8d} "
                f"{run['mean_island_size']:>10.2f} "
                f"{run['singleton_islands']:>10d} "
                f"{run['elapsed_seconds']:>9.3f}"
            )

    print()
    print("CSV files:")
    print(f"  {STATUS_CSV.name}")
    print(f"  {SUMMARY_CSV.name}")
    print(f"  {ISLAND_CSV.name}")
    print()


if __name__ == "__main__":
    main()
