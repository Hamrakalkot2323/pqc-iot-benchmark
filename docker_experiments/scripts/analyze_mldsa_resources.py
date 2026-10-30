import csv
import statistics
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "results" / "raw"
ANALYSIS_DIR = PROJECT_DIR / "results" / "analysis"

MANIFEST = ANALYSIS_DIR / "verified_runs.csv"

RESOURCE_FIELDS = [
    "memory_limit_bytes",
    "peak_memory_bytes",
    "cpu_usage_usec",
    "cpu_nr_periods",
    "cpu_nr_throttled",
    "cpu_throttled_usec",
]


def read_csv(path):
    with path.open("r", newline="") as file:
        return list(csv.DictReader(file))


def to_number(value):
    if value is None or value.strip() in ("", "max"):
        return None

    try:
        number = float(value)
        return number if number >= 0 else None
    except ValueError:
        return None


def calculate_statistics(values):
    if not values:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "stdev": None,
            "min": None,
            "max": None,
        }

    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.stdev(values) if len(values) >= 2 else None,
        "min": min(values),
        "max": max(values),
    }


def main():
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows = read_csv(MANIFEST)

    mldsa_runs = [
        row for row in manifest_rows
        if row["benchmark"] == "mldsa"
        and row["status"] == "success"
        and row["exit_code"] == "0"
    ]

    run_records = []

    for run in mldsa_runs:
        resource_path = RAW_DIR / run["resource_file"]

        if not resource_path.exists():
            print(f"Missing resource file: {resource_path.name}")
            continue

        resource_rows = read_csv(resource_path)

        if len(resource_rows) != 1:
            print(f"Unexpected resource row count: {resource_path.name}")
            continue

        resource = resource_rows[0]

        record = {
            "run_id": run["run_id"],
            "profile": run["profile"],
            "timing_file": run["timing_file"],
            "resource_file": run["resource_file"],
        }

        for field in RESOURCE_FIELDS:
            record[field] = to_number(resource.get(field))

        run_records.append(record)

    # Save individual run measurements.
    detail_fields = [
        "run_id",
        "profile",
        "timing_file",
        "resource_file",
        *RESOURCE_FIELDS,
    ]

    detail_path = ANALYSIS_DIR / "mldsa_resource_runs.csv"

    with detail_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=detail_fields)
        writer.writeheader()
        writer.writerows(run_records)

    # Calculate profile-level statistics.
    summary_records = []

    for profile in ["C0", "C1", "C2", "C3"]:
        profile_runs = [
            record for record in run_records
            if record["profile"] == profile
        ]

        if not profile_runs:
            continue

        summary = {
            "profile": profile,
            "independent_runs": len(profile_runs),
        }

        for field in RESOURCE_FIELDS:
            values = [
                record[field]
                for record in profile_runs
                if record[field] is not None
            ]

            stats = calculate_statistics(values)

            for stat_name, stat_value in stats.items():
                summary[f"{field}_{stat_name}"] = stat_value

        summary_records.append(summary)

    summary_path = ANALYSIS_DIR / "mldsa_resource_summary.csv"

    summary_fields = (
        list(summary_records[0].keys()) if summary_records else []
    )

    with summary_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(summary_records)

    print(f"Verified ML-DSA runs found: {len(mldsa_runs)}")
    print(f"Resource records processed: {len(run_records)}")
    print(f"Individual measurements saved: {detail_path}")
    print(f"Profile comparison saved: {summary_path}")


if __name__ == "__main__":
    main()
