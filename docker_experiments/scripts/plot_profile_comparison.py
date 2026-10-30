import csv
from pathlib import Path

import matplotlib.pyplot as plt


PROJECT_DIR = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = PROJECT_DIR / "results" / "analysis"

INPUT = ANALYSIS_DIR / "profile_performance_comparison.csv"
OUTPUT_DIR = ANALYSIS_DIR / "profile_comparison_figures"

PROFILES = ["C0", "C1", "C2", "C3"]


def read_summary():
    with INPUT.open("r", newline="") as file:
        return list(csv.DictReader(file))


def main():
    rows = read_summary()

    if not rows:
        raise ValueError("The profile comparison dataset is empty.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Find every algorithm-operation combination.
    combinations = sorted({
        (row["algorithm"], row["operation"])
        for row in rows
    })

    graphs_created = 0

    for algorithm, operation in combinations:

        means = []
        deviations = []

        for profile in PROFILES:
            matching = [
                row for row in rows
                if row["profile"] == profile
                and row["algorithm"] == algorithm
                and row["operation"] == operation
            ]

            if len(matching) != 1:
                raise ValueError(
                    f"Expected one record for {profile}, "
                    f"{algorithm}, {operation}; found {len(matching)}."
                )

            record = matching[0]

            mean = float(record["mean_ms"])
            stdev = float(record["stdev_ms"])

            if mean <= 0 or stdev < 0:
                raise ValueError(
                    f"Invalid statistics for {algorithm} {operation}."
                )

            means.append(mean)
            deviations.append(stdev)

        # Create one graph for this algorithm and operation.
        plt.figure(figsize=(8, 5))

        plt.errorbar(
            PROFILES,
            means,
            yerr=deviations,
            marker="o",
            markersize=7,
            capsize=5,
            linewidth=1.8
        )

        plt.yscale("log")
        plt.xlabel("Resource Profile")
        plt.ylabel("Execution Time (ms)")
        plt.title(f"{algorithm} - {operation}")
        plt.grid(True, which="both", linestyle="--", alpha=0.5)

        plt.tight_layout()

        filename = f"{algorithm}_{operation}.png"
        plt.savefig(OUTPUT_DIR / filename, dpi=300)
        plt.close()

        graphs_created += 1

    print(f"Algorithm-operation combinations: {len(combinations)}")
    print(f"Graphs created: {graphs_created}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
