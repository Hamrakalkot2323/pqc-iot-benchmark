
import csv
import statistics
from pathlib import Path

INPUT_FILES = [
    Path("results/raw/kem_raw_results.csv"),
    Path("results/raw/dsa_raw_results.csv"),
]

OUTPUT_PATH = Path("results/summary/pqc_summary.csv")


def load_results(csv_paths):
    rows = []

    for csv_path in csv_paths:
        if not csv_path.exists():
            raise FileNotFoundError(
                f"Raw results file not found: {csv_path}"
            )

        with csv_path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            required_columns = {
                "Algorithm",
                "Operation",
                "Trial",
                "Time_ns",
            }

            if not required_columns.issubset(reader.fieldnames or []):
                raise ValueError(
                    f"Unexpected CSV columns in {csv_path}"
                )

            for row in reader:
                row["Time_ns"] = int(row["Time_ns"])
                rows.append(row)

    return rows


def calculate_summary(rows):
    groups = {}

    for row in rows:
        key = (row["Algorithm"], row["Operation"])
        groups.setdefault(key, []).append(row["Time_ns"])

    summaries = []

    for (algorithm, operation), timings in sorted(groups.items()):
        quartiles = statistics.quantiles(
            timings,
            n=4,
            method="inclusive",
        )

        summaries.append({
            "Algorithm": algorithm,
            "Operation": operation,
            "Trials": len(timings),
            "Median_ns": statistics.median(timings),
            "IQR_ns": quartiles[2] - quartiles[0],
        })

    return summaries


def save_summary(summaries, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Algorithm",
        "Operation",
        "Trials",
        "Median_ns",
        "IQR_ns",
    ]

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    print(f"Summary saved to: {output_path}")


def main():
    rows = load_results(INPUT_FILES)
    summaries = calculate_summary(rows)
    save_summary(summaries, OUTPUT_PATH)

    print(f"\nTotal raw measurements: {len(rows)}")
    print("\nSummary results:")

    for summary in summaries:
        print(summary)


if __name__ == "__main__":
    main()
