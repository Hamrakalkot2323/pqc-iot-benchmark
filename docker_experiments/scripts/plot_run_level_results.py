import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "results/analysis/run_level_summary.csv"
OUTPUT_DIR = BASE_DIR / "results/analysis/figures"

PROFILES = ["C0", "C1", "C2", "C3"]


def read_summary():
    with INPUT_FILE.open(newline="") as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 72:
        raise ValueError(f"Expected 72 rows, found {len(rows)}")

    required = {
        "profile",
        "algorithm",
        "operation",
        "median_of_run_medians_ms",
        "min_run_median_ms",
        "max_run_median_ms",
    }

    if not required.issubset(rows[0]):
        raise ValueError(f"Missing columns: {required - set(rows[0])}")

    return rows


def get_values(group):
    profiles = [p for p in PROFILES if p in group]

    medians = [float(group[p]["median_of_run_medians_ms"])
               for p in profiles]
    lows = [float(group[p]["min_run_median_ms"])
            for p in profiles]
    highs = [float(group[p]["max_run_median_ms"])
             for p in profiles]

    for p, median, low, high in zip(profiles, medians, lows, highs):
        if not all(math.isfinite(v) for v in (median, low, high)):
            raise ValueError(f"Non-finite timing for profile {p}")

        if low > median or median > high:
            raise ValueError(
                f"Median outside range for {p}: "
                f"min={low}, median={median}, max={high}"
            )

        if low <= 0 or median <= 0 or high <= 0:
            raise ValueError(
                f"Non-positive timing for logarithmic plot at {p}"
            )

    lower = [max(0.0, median - low)
             for median, low in zip(medians, lows)]
    upper = [max(0.0, high - median)
             for median, high in zip(highs, medians)]

    return profiles, medians, lower, upper


def plot_errorbars(ax, profiles, medians, lower, upper, **kwargs):
    # Matplotlib expects a 2-by-N array for asymmetric error bars.
    errors = [lower, upper]

    if any(value < 0 for side in errors for value in side):
        raise ValueError("Negative error-bar length detected")

    if len(profiles) != len(medians):
        raise ValueError("Profile and median counts differ")

    if len(lower) != len(medians) or len(upper) != len(medians):
        raise ValueError("Error-bar and median counts differ")

    ax.errorbar(
        profiles,
        medians,
        yerr=errors,
        **kwargs,
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_summary()

    groups = {}
    for row in rows:
        key = (row["algorithm"], row["operation"])
        groups.setdefault(key, []).append(row)

    # 1. Individual algorithm-operation graphs.
    for (algorithm, operation), group_rows in sorted(groups.items()):
        group = {row["profile"]: row for row in group_rows}

        profiles, medians, lower, upper = get_values(group)

        fig, ax = plt.subplots(figsize=(8, 5))
        plot_errorbars(
            ax, profiles, medians, lower, upper,
            fmt="o", capsize=5,
        )

        ax.set_title(f"{algorithm}: {operation}")
        ax.set_xlabel("Resource profile")
        ax.set_ylabel("Median of run medians (ms)")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()

        filename = f"{algorithm}_{operation}.png"
        fig.savefig(OUTPUT_DIR / filename, dpi=200)
        plt.close(fig)

    # 2. Comparison graphs: one graph per operation.
    operations = sorted({row["operation"] for row in rows})

    for operation in operations:
        fig, ax = plt.subplots(figsize=(10, 6))

        algorithms = sorted({
            row["algorithm"]
            for row in rows
            if row["operation"] == operation
        })

        for algorithm in algorithms:
            group = {
                row["profile"]: row
                for row in rows
                if row["algorithm"] == algorithm
                and row["operation"] == operation
            }

            try:
                profiles, medians, lower, upper = get_values(group)

                plot_errorbars(
                    ax, profiles, medians, lower, upper,
                    marker="o",
                    capsize=4,
                    label=algorithm,
                )
            except (ValueError, TypeError) as error:
                raise ValueError(
                    f"Failed plotting algorithm={algorithm}, "
                    f"operation={operation}: {error}"
                ) from error

        ax.set_title(f"Algorithm Comparison: {operation}")
        ax.set_xlabel("Resource profile")
        ax.set_ylabel("Median of run medians (ms)")
        ax.set_yscale("log")
        ax.grid(axis="y", which="both", alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()

        fig.savefig(
            OUTPUT_DIR / f"comparison_{operation}.png",
            dpi=200,
        )
        plt.close(fig)

    # 3. Compact overview of all 72 summary rows.
    fig, ax = plt.subplots(figsize=(14, 7))

    labels = []
    values = []

    for (algorithm, operation), group_rows in sorted(groups.items()):
        group = {row["profile"]: row for row in group_rows}

        for profile in PROFILES:
            if profile not in group:
                continue

            row = group[profile]
            labels.append(f"{algorithm}\n{operation}\n{profile}")
            values.append(float(row["median_of_run_medians_ms"]))

    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Overview contains invalid logarithmic values")

    x_values = list(range(len(labels)))
    ax.scatter(x_values, values, s=12)

    ax.set_yscale("log")
    ax.set_title("Benchmark Overview Across Resource Profiles")
    ax.set_xlabel("Algorithm, operation, and profile")
    ax.set_ylabel("Median of run medians (ms, logarithmic scale)")
    ax.set_xticks(x_values)
    ax.set_xticklabels(labels, rotation=90, fontsize=5)
    ax.grid(axis="y", which="both", alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "benchmark_overview.png", dpi=200)
    plt.close(fig)

    print("Summary rows validated:", len(rows))
    print("Individual graphs:", len(groups))
    print("Operation comparison graphs:", len(operations))
    print("Overview graph: benchmark_overview.png")
    print("Saved figures to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
