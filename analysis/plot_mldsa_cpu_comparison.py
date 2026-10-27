
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = Path("results/mldsa_cpu_comparison_repeated.csv")
OUTPUT_FILE = Path("results/mldsa_cpu_comparison_repeated.png")

df = pd.read_csv(INPUT_FILE)

# Keep only the averages of the two run-level medians.
df = df[df["Run"] == "mean_of_run_medians"]

operations = [
    ("keygen", "Key Generation"),
    ("sign", "Signing"),
    ("verify", "Verification"),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, (operation, title) in zip(axes, operations):
    operation_data = df[df["Operation"] == operation]

    for algorithm in ["ML-DSA-44", "ML-DSA-65"]:
        algorithm_data = operation_data[
            operation_data["Algorithm"] == algorithm
        ].sort_values("CPUs")

        ax.plot(
            algorithm_data["CPUs"],
            algorithm_data["Median_ms"],
            marker="o",
            label=algorithm,
        )

    ax.set_title(title)
    ax.set_xlabel("CPU affinity (logical CPUs)")
    ax.set_ylabel("Mean of run medians (ms)")
    ax.set_xticks([1, 2, 4, 8])
    ax.grid(True, alpha=0.3)
    ax.legend()

fig.suptitle("ML-DSA Performance: Repeated CPU-Affinity Runs")
fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.show()

print(f"Repeated comparison graph saved to: {OUTPUT_FILE}")

