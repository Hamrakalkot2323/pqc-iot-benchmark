
import csv
from pathlib import Path

RESULTS_DIR = Path("results")

SUMMARY_FILES = {
    2: RESULTS_DIR / "kem_2cpu_summary.csv",
    4: RESULTS_DIR / "kem_4cpu_summary.csv",
    4.1: RESULTS_DIR / "kem_4cpu_repeat2_summary.csv",
    8: RESULTS_DIR / "kem_8cpu_summary.csv",
    8.1: RESULTS_DIR / "kem_8cpu_repeat2_summary.csv",
}

OUTPUT_PATH = RESULTS_DIR / "kem_cpu_comparison.csv"


def main():
    combined_rows = []

    for cpu_setting, file_path in SUMMARY_FILES.items():
        if not file_path.exists():
            print(f"Skipping missing file: {file_path}")
            continue

        with file_path.open(
            "r", newline="", encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                row["CPU_Setting"] = (
                    str(cpu_setting).replace(".1", "")
                )
                row["Run"] = (
                    "repeat2" if ".1" in str(cpu_setting) else "first"
                )
                combined_rows.append(row)

    if not combined_rows:
        raise RuntimeError("No summary data was found.")

    fieldnames = [
        "CPU_Setting",
        "Run",
        *[
            key for key in combined_rows[0]
            if key not in ("CPU_Setting", "Run")
        ],
    ]

    with OUTPUT_PATH.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)

    print(f"Combined {len(combined_rows)} summary rows.")
    print(f"Saved comparison dataset to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
