
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

INPUT_PATH = Path("results/kem_cpu_comparison.csv")
OUTPUT_PATH = Path("results/kem_cpu_comparison.png")

df = pd.read_csv(INPUT_PATH)

# Average repeated measurements for each CPU setting and algorithm.
metrics = {
    "keygen_median_ms": "Key Generation",
    "encaps_median_ms": "Encapsulation",
    "decaps_median_ms": "Decapsulation",
}

averaged = (
    df.groupby(["CPU_Setting", "algorithm"], as_index=False)[
        list(metrics.keys())
    ]
    .mean()
)

# Ensure CPU settings are displayed in numerical order.
averaged["CPU_Setting"] = averaged["CPU_Setting"].astype(int)
averaged = averaged.sort_values("CPU_Setting")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for ax, (column, title) in zip(axes, metrics.items()):
    for algorithm in ["ML-KEM-512", "ML-KEM-768"]:
        subset = averaged[averaged["algorithm"] == algorithm]

        ax.plot(
            subset["CPU_Setting"],
            subset[column],
            marker="o",
            label=algorithm,
        )

    ax.set_title(title)
    ax.set_xlabel("Available logical CPUs")
    ax.set_ylabel("Average of run medians (ms)")
    ax.set_xticks(sorted(averaged["CPU_Setting"].unique()))
    ax.legend()
    ax.grid(True, alpha=0.3)

fig.suptitle(
    "ML-KEM Performance Under Different CPU Affinity Settings",
    fontsize=14,
)

plt.tight_layout()

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")

print(f"Graph saved to: {OUTPUT_PATH}")
print("\nAveraged results:")
print(averaged.to_string(index=False))

plt.show()
