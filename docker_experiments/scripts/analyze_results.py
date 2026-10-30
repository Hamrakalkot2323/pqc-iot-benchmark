import csv
import glob
import os
import statistics
from collections import defaultdict

RAW_DIR = "results/raw"
OUTPUT_DIR = "results/analysis"

REQUIRED_COLUMNS = {
    "timestamp_utc", "profile", "algorithm",
    "operation", "trial", "time_ns", "time_ms"
}
VALID_PROFILES = {"C0", "C1", "C2", "C3"}

os.makedirs(OUTPUT_DIR, exist_ok=True)

groups = defaultdict(list)
file_count = 0
excluded_files = []

for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.csv"))):
    name = os.path.basename(path)

    # Only timing files; ignore status and resource logs.
    if not name.startswith(("kem_", "mldsa_", "classical_")):
        continue

    with open(path, newline="") as f:
        reader = csv.DictReader(f)

        if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
            excluded_files.append((name, "unexpected columns"))
            continue

        rows = list(reader)

    if not rows:
        excluded_files.append((name, "empty file"))
        continue

    profiles = {row["profile"].strip() for row in rows}

    # Never guess the profile of older/unknown files.
    if len(profiles) != 1 or not profiles.issubset(VALID_PROFILES):
        excluded_files.append((name, f"unknown/inconsistent profile: {profiles}"))
        continue

    file_count += 1

    for row in rows:
        try:
            value = float(row["time_ms"])
            trial = int(row["trial"])
            if value <= 0 or trial < 1:
                raise ValueError("non-positive time or invalid trial")
        except (ValueError, TypeError):
            excluded_files.append((name, "invalid measurement"))
            break

        key = (
            row["profile"].strip(),
            row["algorithm"].strip(),
            row["operation"].strip(),
        )
        groups[key].append(value)

summary_path = os.path.join(OUTPUT_DIR, "summary.csv")

with open(summary_path, "w", newline="") as f:
    fields = [
        "profile", "algorithm", "operation", "measurements",
        "median_ms", "mean_ms", "stdev_ms", "q1_ms", "q3_ms", "iqr_ms"
    ]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for (profile, algorithm, operation), values in sorted(groups.items()):
        values.sort()
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        writer.writerow({
            "profile": profile,
            "algorithm": algorithm,
            "operation": operation,
            "measurements": len(values),
            "median_ms": f"{statistics.median(values):.6f}",
            "mean_ms": f"{statistics.mean(values):.6f}",
            "stdev_ms": f"{statistics.stdev(values):.6f}" if len(values) > 1 else "",
            "q1_ms": f"{q1:.6f}",
            "q3_ms": f"{q3:.6f}",
            "iqr_ms": f"{q3 - q1:.6f}",
        })

print(f"Timing files included: {file_count}")
print(f"Summary groups: {len(groups)}")
print(f"Summary saved to: {summary_path}")
print(f"Files excluded: {len(excluded_files)}")

for name, reason in excluded_files:
    print(f"  EXCLUDED: {name} — {reason}")
