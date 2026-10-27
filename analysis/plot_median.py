
import csv
from pathlib import Path

import matplotlib.pyplot as plt

INPUT_FILE = Path("results/summary/pqc_summary.csv")
OUTPUT_FILE = Path("results/median_execution_time.png")

# Load the actual statistical summary
with INPUT_FILE.open("r", newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

algorithms = sorted({row["Algorithm"] for row in rows})
operations = ["keygen", "encaps", "decaps", "sign", "verify"]

operation_labels = {
    "keygen": "Key Generation",
    "encaps": "Encapsulation",
    "decaps": "Decapsulation",
    "sign": "Signing",
    "verify": "Verification",
}

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for ax, family, title in zip(
    axes,
    [
        ["ML-KEM-512", "ML-KEM-768"],
        ["ML-DSA-44", "ML-DSA-65"],
    ],
    ["ML-KEM: Key Establishment", "ML-DSA: Digital Signatures"],
):
    family_rows = [row for row in rows if row["Algorithm"] in family]

    for algorithm in family:
        selected = [
            row for row in family_rows if row["Algorithm"] == algorithm
        ]
        selected.sort(key=lambda row: operations.index(row["Operation"]))

        labels = [
            operation_labels[row["Operation"]] for row in selected
        ]
        medians_ms = [
            float(row["Median_ns"]) / 1_000_000 for row in selected
        ]

        ax.plot(labels, medians_ms, marker="o", linewidth=2, label=algorithm)

    ax.set_title(title)
    ax.set_ylabel("Median execution time (ms)")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend()

fig.suptitle("Post-Quantum Cryptography: Median Execution Times")
fig.tight_layout()

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
print(f"Graph saved to: {OUTPUT_FILE.resolve()}")

plt.show()
