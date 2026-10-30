import csv
import statistics
from pathlib import Path

input_path = Path("results/analysis/mldsa_run_consistency.csv")
output_path = Path("results/analysis/mldsa_consistency_summary.csv")

groups = {}

with input_path.open("r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        key = (
            row["profile"],
            row["algorithm"],
            row["operation"],
        )

        groups.setdefault(key, []).append(float(row["median_ms"]))

results = []

for (profile, algorithm, operation), values in sorted(groups.items()):
    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0
    cv = (stdev / mean * 100) if mean != 0 else 0

    results.append({
        "profile": profile,
        "algorithm": algorithm,
        "operation": operation,
        "independent_runs": len(values),
        "mean_run_median_ms": round(mean, 6),
        "stdev_ms": round(stdev, 6),
        "cv_percent": round(cv, 2),
        "min_run_median_ms": round(min(values), 6),
        "max_run_median_ms": round(max(values), 6),
    })

with output_path.open("w", newline="") as file:
    fieldnames = [
        "profile",
        "algorithm",
        "operation",
        "independent_runs",
        "mean_run_median_ms",
        "stdev_ms",
        "cv_percent",
        "min_run_median_ms",
        "max_run_median_ms",
    ]

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"Groups analysed: {len(results)}")
print(f"Saved summary to: {output_path}")
