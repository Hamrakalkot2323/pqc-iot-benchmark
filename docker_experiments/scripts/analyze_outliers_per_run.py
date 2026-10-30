
import csv
from pathlib import Path
from collections import defaultdict
from statistics import median

PROJECT_DIR = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_DIR / "results" / "analysis" / "verified_runs.csv"

# Store measurements separately for each timing file,
# algorithm, and operation.
measurements = defaultdict(list)

with MANIFEST.open(newline="") as manifest_file:
    runs = csv.DictReader(manifest_file)

    for run in runs:
        timing_file = PROJECT_DIR / "results" / "raw" / run["timing_file"]

        with timing_file.open(newline="") as timing_handle:
            rows = csv.DictReader(timing_handle)

            for row in rows:
                key = (
                    run["timing_file"],
                    row["algorithm"],
                    row["operation"],
                )

                measurements[key].append({
                    "time_ms": float(row["time_ms"]),
                    "trial": row["trial"],
                })


def calculate_quartiles(values):
    """Calculate Q1 and Q3 using the median-of-halves method."""
    ordered = sorted(values)

    if len(ordered) < 4:
        return None, None

    middle = len(ordered) // 2
    lower = ordered[:middle]

    if len(ordered) % 2 == 0:
        upper = ordered[middle:]
    else:
        upper = ordered[middle + 1:]

    return median(lower), median(upper)


print("PQC BENCHMARK — PER-RUN ANOMALY SCREENING")
print("Rule: values outside Q1 - 1.5*IQR or Q3 + 1.5*IQR")
print("Measurements are flagged for review, never automatically removed.")
print("=" * 100)

flagged_count = 0
groups_checked = 0

for key, records in sorted(measurements.items()):
    values = [record["time_ms"] for record in records]
    q1, q3 = calculate_quartiles(values)

    if q1 is None:
        continue

    groups_checked += 1
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    for record in records:
        value = record["time_ms"]

        if value < lower_bound or value > upper_bound:
            filename, algorithm, operation = key

            print(
                f"File={filename} | "
                f"Algorithm={algorithm} | "
                f"Operation={operation} | "
                f"Trial={record['trial']} | "
                f"Time={value:.6f} ms"
            )

            flagged_count += 1

print("=" * 100)
print(f"Groups checked: {groups_checked}")
print(f"Potential anomalies flagged: {flagged_count}")
print("Raw benchmark files were not modified.")
