
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = Path("results/mldsa_variability_analysis.csv")
OUTPUT_FILE = Path("results/mldsa_variability_comparison.png")

df = pd.read_csv(INPUT_FILE)

# Keep CPU settings in a consistent order.
cpu_settings = [1, 2, 4, 8]
algorithms = ["ML-DSA-44", "ML-DSA-65"]
operations = [
    ("keygen", "Key Generation"),
    ("sign", "Signing"),
    ("verify", "Verification"),
]

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

for ax, (operation, title) in zip(axes, operations):
    subset = df[df["Operation"] == operation]

    for algorithm in algorithms:
        algo_data = subset[
            subset["Algorithm"] == algorithm
        ].sort_values("CPUs")

        ax.plot(
            algo_data["CPUs"],
            algo_data["Difference_percent_of_first"],
            marker="o",
            label=algorithm,
        )

    ax.set_title(title)
    ax.set_xlabel("CPU affinity (logical CPUs)")
    ax.set_ylabel("Run-to-run difference (%)")
    ax.set_xticks(cpu_settings)
    ax.grid(True, alpha=0.3)
    ax.legend()

fig.suptitle("ML-DSA Run-to-Run Timing Differences")
fig.tight_layout()

fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
plt.show()

print(f"Variability graph saved to: {OUTPUT_FILE}")
