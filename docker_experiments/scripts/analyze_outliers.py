
import csv
from pathlib import Path
from collections import defaultdict
from statistics import median

PROJECT_DIR = Path(__file__).resolve().parent.parent
MANIFEST = PROJECT_DIR / "results" / "analysis" / "verified_runs.csv"

# Group measurements by profile, algorithm, and operation.
measurements = defaultdict(list)

with MANIFEST.open(newline="") as file:
    runs = csv.DictReader(file)

    for run in runs:
        timing_file = PROJECT_DIR / "results" / "raw" / run["timing_file"]

        with timing_file.open(newline="") as file:
            rows = csv.DictReader(file)

            for row in rows:
                key = (
                    row["profile"],
                    row["algorithm"],
                    row["operation"],
                )

                measurements[key].append({
                    "time_ms": float(row["time_ms"]),
                    "trial": row["trial"],
                    "file": run["timing_file"],
                })


def calculate_quartiles(values):
    """Calculate Q1 and Q3 using the median-of-halves method."""
    ordered = sorted(values)
    middle = len(ordered) // 2

    if len(ordered) < 4:
        return None, None

    lower = ordered[:middle]
    upper = ordered[(middle + 1 if len(ordered) % 2 else middle):]

    return median(lower), median(upper)


print("PQC BENCHMARK — POTENTIAL TIMING ANOMALIES")
print("IQR rule: below Q1 - 1.5*IQR or above Q3 + 1.5*IQR")
print("All measurements are retained; this script only flags them.")
print("=" * 90)

flagged_count = 0

for key, records in sorted(measurements.items()):
    values = [record["time_ms"] for record in records]
    q1, q3 = calculate_quartiles(values)

    if q1 is None or q3 is None:
        continue

    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    for record in records:
        value = record["time_ms"]

        if value < lower_bound or value > upper_bound:
            profile, algorithm, operation = key
            print(
                f"Profile={profile} | "
                f"Algorithm={algorithm} | "
                f"Operation={operation} | "
                f"Trial={record['trial']} | "
                f"Time={value:.6f} ms | "
                f"File={record['file']}"
            )
            flagged_count += 1

print("=" * 90)
print(f"Potential anomalies flagged: {flagged_count}")
print("No raw CSV files were modified.")
