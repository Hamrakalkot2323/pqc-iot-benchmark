
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path("results")
CPU_SETTINGS = [1, 2, 4, 8]
RUNS = ["first", "repeat2"]
OPERATIONS = ["keygen", "sign", "verify"]
ALGORITHMS = ["ML-DSA-44", "ML-DSA-65"]


def main():
    rows = []

    for cpus in CPU_SETTINGS:
        for run in RUNS:
            suffix = "" if run == "first" else "_repeat2"
            path = RESULTS_DIR / f"mldsa_{cpus}cpu{suffix}_summary.csv"

            if not path.exists():
                raise FileNotFoundError(f"Missing results file: {path}")

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

    # Average the two run-level medians for each combination.
    averages = (
        results.groupby(["CPUs", "Algorithm", "Operation"], as_index=False)
        ["Median_ms"]
        .mean()
    )
    averages["Run"] = "mean_of_run_medians"

    combined = pd.concat([results, averages], ignore_index=True)

    output_path = RESULTS_DIR / "mldsa_cpu_comparison_repeated.csv"
    combined.to_csv(output_path, index=False)

    print(combined.sort_values(
        ["CPUs", "Algorithm", "Operation", "Run"]
    ).to_string(index=False))
    print(f"\nRepeated comparison saved to: {output_path}")


if __name__ == "__main__":
    main()

