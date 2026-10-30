
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path


# -------------------- Configuration --------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "results" / "raw"
PROCESSED_DIR = PROJECT_DIR / "results" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_FILE = PROCESSED_DIR / "benchmark_summary.csv"


def percentile(sorted_values, fraction):
    """Calculate a percentile using linear interpolation."""
    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return sorted_values[lower]

    weight = position - lower
    return (
        sorted_values[lower] * (1 - weight)
        + sorted_values[upper] * weight
    )


def load_measurements():
    measurements = defaultdict(list)
    files = sorted(RAW_DIR.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DIR}"
        )

    for file_path in files:
        with file_path.open("r", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            required_columns = {
                "algorithm",
                "operation",
                "trial",
                "time_ns",
                "time_ms",
            }

            if not required_columns.issubset(
                reader.fieldnames or []
            ):
                print(f"Skipping unrecognized CSV: {file_path.name}")
                continue

            has_profile_column = (
                "profile" in (reader.fieldnames or [])
            )

            file_samples = 0

            for row in reader:
                algorithm = row["algorithm"]
                operation = row["operation"]

                # Old pilot files without profile metadata remain
                # separate from the configured C0-C3 experiments.
                profile = (
                    row.get("profile", "").strip()
                    if has_profile_column else ""
                )
                if not profile:
                    profile = "UNKNOWN"

                time_ms = float(row["time_ms"])

                if not math.isfinite(time_ms) or time_ms < 0:
                    raise ValueError(
                        f"Invalid timing in {file_path.name}"
                    )

                measurements[
                    (profile, algorithm, operation)
                ].append(time_ms)

                file_samples += 1

        if file_samples:
            print(
                f"Loaded: {file_path.name} "
                f"({file_samples} measurements)"
            )
        else:
            print(f"No measurements found in: {file_path.name}")

    return measurements


def calculate_summary(measurements):
    summary_rows = []

    for (profile, algorithm, operation), values in sorted(
        measurements.items()
    ):
        ordered = sorted(values)

        q1 = percentile(ordered, 0.25)
        q3 = percentile(ordered, 0.75)

        summary_rows.append({
            "profile": profile,
            "algorithm": algorithm,
            "operation": operation,
            "sample_count": len(ordered),
            "median_ms": statistics.median(ordered),
            "mean_ms": statistics.mean(ordered),
            "std_dev_ms": (
                statistics.stdev(ordered)
                if len(ordered) > 1 else 0.0
            ),
            "min_ms": ordered[0],
            "q1_ms": q1,
            "q3_ms": q3,
            "max_ms": ordered[-1],
            "iqr_ms": q3 - q1,
        })

    return summary_rows


def save_summary(summary_rows):
    fieldnames = [
        "profile",
        "algorithm",
        "operation",
        "sample_count",
        "median_ms",
        "mean_ms",
        "std_dev_ms",
        "min_ms",
        "q1_ms",
        "q3_ms",
        "max_ms",
        "iqr_ms",
    ]

    with SUMMARY_FILE.open("w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(summary_rows)


def main():
    print("PQC Benchmark Results Analysis")
    print("=" * 60)

    measurements = load_measurements()

    if not measurements:
        raise RuntimeError("No valid measurements were loaded.")

    summary_rows = calculate_summary(measurements)
    save_summary(summary_rows)

    for row in summary_rows:
        print(
            f"\nProfile: {row['profile']}"
            f"\n{row['algorithm']} | {row['operation']}"
            f"\n  Samples: {row['sample_count']}"
            f"\n  Median:  {row['median_ms']:.6f} ms"
            f"\n  Mean:    {row['mean_ms']:.6f} ms"
            f"\n  Std dev: {row['std_dev_ms']:.6f} ms"
            f"\n  IQR:     {row['iqr_ms']:.6f} ms"
            f"\n  Min-Max: {row['min_ms']:.6f} - "
            f"{row['max_ms']:.6f} ms"
        )

    print("\n" + "=" * 60)
    print(f"Summary saved to: {SUMMARY_FILE}")
    print(f"Profile-algorithm-operation groups: {len(summary_rows)}")


if __name__ == "__main__":
    main()
