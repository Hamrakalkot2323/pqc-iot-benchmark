
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path("results")
CPU_SETTINGS = [1, 2, 4, 8]
ALGORITHMS = ["ML-DSA-44", "ML-DSA-65"]
OPERATIONS = ["keygen", "sign", "verify"]


def main():
    rows = []

    for cpus in CPU_SETTINGS:
        for run in ["first", "repeat2"]:
            suffix = "" if run == "first" else "_repeat2"
            path = RESULTS_DIR / f"mldsa_{cpus}cpu{suffix}_summary.csv"

            if not path.exists():
                raise FileNotFoundError(f"Missing file: {path}")

            df = pd.read_csv(path)

            for algorithm in ALGORITHMS:
                algorithm_rows = df[df["algorithm"] == algorithm]

                for operation in OPERATIONS:
                    column = f"{operation}_median_ms"
                    values = algorithm_rows[column].dropna()

                    if values.empty:
                        raise ValueError(
                            f"Missing {column} for {algorithm} in {path}"
                        )

                    rows.append({
                        "CPUs": cpus,
                        "Run": run,
                        "Algorithm": algorithm,
                        "Operation": operation,
                        "Median_ms": float(values.iloc[0]),
                    })

    results = pd.DataFrame(rows)

    # Average of the two run-level medians.
    averages = (
        results.groupby(["CPUs", "Algorithm", "Operation"])["Median_ms"]
        .mean()
        .rename("Mean_of_run_medians_ms")
    )

    # Absolute difference and relative variation between the two runs.
    wide = results.pivot(
        index=["CPUs", "Algorithm", "Operation"],
        columns="Run",
        values="Median_ms",
    ).reset_index()

    wide["Absolute_difference_ms"] = (
        wide["repeat2"] - wide["first"]
    ).abs()

    wide["Difference_percent_of_first"] = (
        wide["Absolute_difference_ms"] / wide["first"] * 100
    )

    # Average the run-level medians for each CPU/algorithm/operation.
    wide = wide.merge(
        averages.reset_index(),
        on=["CPUs", "Algorithm", "Operation"],
    )

    output_path = RESULTS_DIR / "mldsa_variability_analysis.csv"
    wide.to_csv(output_path, index=False)

    print("\nML-DSA run-to-run variability")
    print(wide.round(6).to_string(index=False))
    print(f"\nAnalysis saved to: {output_path}")


if __name__ == "__main__":
    main()
