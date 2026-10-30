import csv
import statistics
from pathlib import Path

manifest_path = Path("results/analysis/verified_runs.csv")
raw_dir = Path("results/raw")
output_path = Path("results/analysis/mldsa_run_consistency.csv")

results = []

with manifest_path.open("r", newline="") as file:
    manifest = csv.DictReader(file)

    for run in manifest:
        timing_file = run["timing_file"]

        if not timing_file.startswith("mldsa_"):
            continue

        file_path = raw_dir / timing_file

        measurements = {}

        with file_path.open("r", newline="") as raw_file:
            reader = csv.DictReader(raw_file)

            for row in reader:
                key = (row["algorithm"], row["operation"])
                measurements.setdefault(key, []).append(
                    float(row["time_ms"])
                )

        for (algorithm, operation), times in measurements.items():
            if len(times) != 30:
                print(
                    f"WARNING: {timing_file} — "
                    f"{algorithm} {operation}: "
                    f"expected 30 trials, found {len(times)}"
                )
                continue

            results.append({
                "profile": run["profile"],
                "run_id": run["run_id"],
                "timing_file": timing_file,
                "algorithm": algorithm,
                "operation": operation,
                "trials": len(times),
                "median_ms": statistics.median(times),
            })

results.sort(
    key=lambda row: (
        row["profile"],
        row["algorithm"],
        row["operation"],
        row["run_id"],
    )
)

with output_path.open("w", newline="") as file:
    fieldnames = [
        "profile",
        "run_id",
        "timing_file",
        "algorithm",
        "operation",
        "trials",
        "median_ms",
    ]

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"Verified ML-DSA runs analysed: {len(set(r['run_id'] for r in results))}")
print(f"Run-level observations: {len(results)}")
print(f"Saved results to: {output_path}")
