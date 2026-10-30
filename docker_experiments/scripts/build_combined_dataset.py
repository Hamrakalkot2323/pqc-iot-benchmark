import csv
import statistics
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "results" / "raw"
ANALYSIS_DIR = PROJECT_DIR / "results" / "analysis"

MANIFEST = ANALYSIS_DIR / "verified_runs.csv"
OUTPUT = ANALYSIS_DIR / "combined_run_resource_performance.csv"

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


def main():
    manifest_rows = read_csv(MANIFEST)

    verified_runs = [
        row for row in manifest_rows
        if row["status"] == "success"
        and row["exit_code"] == "0"
    ]

    combined_records = []

    for run in verified_runs:
        timing_path = RAW_DIR / run["timing_file"]
        resource_path = RAW_DIR / run["resource_file"]

        if not timing_path.is_file():
            raise FileNotFoundError(
                f"Missing timing file: {run['timing_file']}"
            )

        if not resource_path.is_file():
            raise FileNotFoundError(
                f"Missing resource file: {run['resource_file']}"
            )

        timing_rows = read_csv(timing_path)
        resource_rows = read_csv(resource_path)

        if not timing_rows:
            raise ValueError(f"Empty timing file: {timing_path.name}")

        if len(resource_rows) != 1:
            raise ValueError(
                f"Expected one resource row in {resource_path.name}"
            )

        # Check that the timing data belongs to this run and profile.
        for row in timing_rows:
            if row["profile"] != run["profile"]:
                raise ValueError(
                    f"Profile mismatch in {timing_path.name}"
                )

        resource = resource_rows[0]

        if resource["profile"] != run["profile"]:
            raise ValueError(
                f"Resource profile mismatch in {resource_path.name}"
            )

        if resource["exit_code"] != "0":
            raise ValueError(
                f"Resource exit code mismatch in {resource_path.name}"
            )

        record = {
            "run_id": run["run_id"],
            "profile": run["profile"],
            "benchmark": run["benchmark"],
            "timing_file": run["timing_file"],
            "resource_file": run["resource_file"],
        }

        # Calculate one median for every algorithm-operation pair.
        groups = {}

        for row in timing_rows:
            algorithm = row["algorithm"]
            operation = row["operation"]

            try:
                time_ms = float(row["time_ms"])
                time_ns = float(row["time_ns"])
                trial = int(row["trial"])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Invalid measurement in {timing_path.name}"
                )

            if time_ms < 0 or time_ns < 0 or trial < 1:
                raise ValueError(
                    f"Invalid measurement in {timing_path.name}"
                )

            if abs(time_ms - time_ns / 1_000_000) > 0.000000001:
                raise ValueError(
                    f"Timing unit mismatch in {timing_path.name}"
                )

            key = (algorithm, operation)
            groups.setdefault(key, []).append(time_ms)

        for (algorithm, operation), values in groups.items():
            if len(values) != 30:
                raise ValueError(
                    f"Expected 30 trials for {algorithm} {operation} "
                    f"in {timing_path.name}; found {len(values)}"
                )

            column = f"{algorithm}_{operation}_median_ms"
            record[column] = statistics.median(values)

        # Attach the container-level resource measurements.
        for field in RESOURCE_FIELDS:
            record[field] = to_number(resource.get(field))

        combined_records.append(record)

    if len(combined_records) != len(verified_runs):
        raise ValueError("Some verified runs were not processed.")

    # Build a consistent set of columns across all runs.
    timing_columns = sorted({
        key
        for record in combined_records
        for key in record
        if key.endswith("_median_ms")
    })

    base_columns = [
        "run_id",
        "profile",
        "benchmark",
        "timing_file",
        "resource_file",
    ]

    fieldnames = base_columns + timing_columns + RESOURCE_FIELDS

    # Save the combined dataset.
    with OUTPUT.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_records)

    print(f"Verified runs processed: {len(verified_runs)}")
    print(f"Combined records created: {len(combined_records)}")
    print(f"Timing columns created: {len(timing_columns)}")
    print(f"Output saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
