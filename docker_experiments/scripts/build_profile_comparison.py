import csv
import statistics
from collections import defaultdict
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = PROJECT_DIR / "results" / "analysis"

INPUT = ANALYSIS_DIR / "combined_run_resource_performance.csv"
OUTPUT = ANALYSIS_DIR / "profile_performance_comparison.csv"


def read_csv(path):
    with path.open("r", newline="") as file:
        return list(csv.DictReader(file))


def calculate_statistics(values):
    return {
        "independent_runs": len(values),
        "mean_ms": statistics.mean(values),
        "median_ms": statistics.median(values),
        "stdev_ms": (
            statistics.stdev(values) if len(values) >= 2 else None
        ),
        "min_ms": min(values),
        "max_ms": max(values),
    }


def main():
    rows = read_csv(INPUT)

    if not rows:
        raise ValueError("The combined dataset is empty.")

    # Store run-level medians by profile, algorithm and operation.
    groups = defaultdict(list)

    for row in rows:
        profile = row["profile"]

        for column, value in row.items():
            if not column.endswith("_median_ms") or not value.strip():
                continue

            # Remove the suffix to recover algorithm and operation.
            measurement = column.removesuffix("_median_ms")
            algorithm, operation = measurement.rsplit("_", 1)

            groups[(profile, algorithm, operation)].append(float(value))

    summary = []

    for (profile, algorithm, operation), values in sorted(groups.items()):
        record = {
            "profile": profile,
            "algorithm": algorithm,
            "operation": operation,
        }

        record.update(calculate_statistics(values))
        summary.append(record)

    fields = [
        "profile",
        "algorithm",
        "operation",
        "independent_runs",
        "mean_ms",
        "median_ms",
        "stdev_ms",
        "min_ms",
        "max_ms",
    ]

    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary)

    print(f"Combined run records read: {len(rows)}")
    print(f"Profile-algorithm-operation groups: {len(summary)}")
    print(f"Output saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
