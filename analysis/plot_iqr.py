
import csv
from pathlib import Path

import matplotlib.pyplot as plt

INPUT_FILE = Path("results/summary/pqc_summary.csv")
OUTPUT_FILE = Path("results/iqr_execution_time.png")

# Load the statistical summary generated from the raw measurements
with INPUT_FILE.open("r", newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

operation_labels = {
    "keygen": "Key Generation",
    "encaps": "Encapsulation",
    "decaps": "Decapsulation",
    "sign": "Signing",
    "verify": "Verification",
}

families = [
    (
        ["ML-KEM-512", "ML-KEM-768"],
        ["keygen", "encaps", "decaps"],
        "ML-KEM: Timing Variability",
    ),
    (
        ["ML-DSA-44", "ML-DSA-65"],
        ["keygen", "sign", "verify"],
        "ML-DSA: Timing Variability",
    ),
]

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, (algorithms, operations, title) in zip(axes, families):
    x_positions = list(range(len(operations)))
    bar_width = 0.35

    for index, algorithm in enumerate(algorithms):
        algorithm_rows = {
            row["Operation"]: row
            for row in rows
            if row["Algorithm"] == algorithm
        }

        iqr_ms = [
            float(algorithm_rows[operation]["IQR_ns"]) / 1_000_000
            for operation in operations
        ]

        offsets = [
            position + (index - 0.5) * bar_width
            for position in x_positions
        ]

        ax.bar(
            offsets,
            iqr_ms,
            width=bar_width,
            label=algorithm,
        )

    ax.set_title(title)
    ax.set_ylabel("Interquartile range (ms)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [operation_labels[operation] for operation in operations],
        rotation=20,
        ha="right",
    )
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.legend()

fig.suptitle("Post-Quantum Cryptography: Variability in Execution Times")
fig.tight_layout()

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")

print(f"Graph saved to: {OUTPUT_FILE.resolve()}")

plt.show()
