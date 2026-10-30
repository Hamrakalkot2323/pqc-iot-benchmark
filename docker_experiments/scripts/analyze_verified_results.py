
import csv
import os
import statistics
from collections import defaultdict

RAW_DIR = "results/raw"
ANALYSIS_DIR = "results/analysis"
MANIFEST_FILE = os.path.join(ANALYSIS_DIR, "verified_runs.csv")
OUTPUT_FILE = os.path.join(ANALYSIS_DIR, "verified_summary.csv")

REQUIRED_COLUMNS = {
    "timestamp_utc",
    "profile",
    "algorithm",
    "operation",
    "trial",
    "time_ns",
    "time_ms",
}

SUMMARY_COLUMNS = [
    "profile",
    "algorithm",
    "operation",
    "n",
    "mean_ms",
    "median_ms",
    "stdev_ms",
    "q1_ms",
    "q3_ms",
    "iqr_ms",
]


def read_csv(path):
    with open(path, newline="") as file:
        return list(csv.DictReader(file))


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def main():
    manifest = read_csv(MANIFEST_FILE)
    if not manifest:
        raise ValueError("The verified-run manifest is empty.")

    groups = defaultdict(list)
    files_included = 0

    for entry in manifest:
        filename = entry["timing_file"]
        expected_profile = entry["profile"]
        path = os.path.join(RAW_DIR, filename)

        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"Manifest timing file is missing: {filename}"
            )

        rows = read_csv(path)

        if not rows:
            raise ValueError(f"Timing file is empty: {filename}")

        actual_columns = set(rows[0].keys())
        if not REQUIRED_COLUMNS.issubset(actual_columns):
            raise ValueError(
                f"Required columns missing from {filename}"
            )

        file_measurements = []

        for row in rows:
            if row["profile"].strip() != expected_profile:
                raise ValueError(
                    f"Profile mismatch in {filename}"
                )

            try:
                time_ms = float(row["time_ms"])
                time_ns = float(row["time_ns"])
                trial = int(row["trial"])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid measurement in {filename}"
                )

            if time_ms < 0 or time_ns < 0 or trial < 1:
                raise ValueError(
                    f"Invalid negative time or trial in {filename}"
                )

            file_measurements.append(
                (
                    row["profile"].strip(),
                    row["algorithm"].strip(),
                    row["operation"].strip(),
                    trial,
                    time_ms,
                    time_ns,
                )
            )

        for profile, algorithm, operation, trial, time_ms, time_ns in file_measurements:
            groups[(profile, algorithm, operation)].append(time_ms)

        files_included += 1

    os.makedirs(ANALYSIS_DIR, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()

        for (profile, algorithm, operation), values in sorted(groups.items()):
            q1 = percentile(values, 0.25)
            q3 = percentile(values, 0.75)

            writer.writerow({
                "profile": profile,
                "algorithm": algorithm,
                "operation": operation,
                "n": len(values),
                "mean_ms": f"{statistics.mean(values):.6f}",
                "median_ms": f"{statistics.median(values):.6f}",
                "stdev_ms": f"{statistics.stdev(values):.6f}" if len(values) > 1 else "0.000000",
                "q1_ms": f"{q1:.6f}",
                "q3_ms": f"{q3:.6f}",
                "iqr_ms": f"{q3 - q1:.6f}",
            })

    print(f"Verified timing files included: {files_included}")
    print(f"Summary groups: {len(groups)}")
    print(f"Verified summary saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
