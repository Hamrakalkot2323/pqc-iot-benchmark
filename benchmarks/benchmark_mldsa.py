
import csv
import os
import statistics
import time
from pathlib import Path

import oqs
import psutil

ALGORITHMS = ["ML-DSA-44", "ML-DSA-65"]
ITERATIONS = 100
WARMUP_ITERATIONS = 5

RAW_OUTPUT = Path("results/raw/mldsa_raw_results.csv")
SUMMARY_OUTPUT = Path("results/mldsa_benchmark.csv")


def configure_cpu_affinity():
    requested_cpus = int(os.getenv("BENCHMARK_CPUS", "8"))

    process = psutil.Process()
    available_cpus = process.cpu_affinity()

    if requested_cpus not in (1, 2, 4, 8):
        raise ValueError("BENCHMARK_CPUS must be 1, 2, 4, or 8.")

    if requested_cpus > len(available_cpus):
        raise ValueError(
            f"Requested {requested_cpus} CPUs, "
            f"but only {len(available_cpus)} are available."
        )

    selected_cpus = available_cpus[:requested_cpus]
    process.cpu_affinity(selected_cpus)

    print(f"CPU affinity: {selected_cpus}")


def benchmark_algorithm(algorithm):
    operations = {
        "keygen": [],
        "sign": [],
        "verify": [],
    }

    # Warm-up operations are excluded from recorded measurements.
    for _ in range(WARMUP_ITERATIONS):
        with oqs.Signature(algorithm) as signer:
            public_key = signer.generate_keypair()
            message = b"PQC benchmark warm-up message"
            signature = signer.sign(message)

        with oqs.Signature(algorithm) as verifier:
            if not verifier.verify(message, signature, public_key):
                raise RuntimeError(f"{algorithm}: warm-up verification failed")

    for trial in range(1, ITERATIONS + 1):
        message = f"PQC benchmark message {trial}".encode("utf-8")

        # Key generation
        with oqs.Signature(algorithm) as signer:
            start = time.perf_counter_ns()
            public_key = signer.generate_keypair()
            keygen_time = time.perf_counter_ns() - start

            # Signing
            start = time.perf_counter_ns()
            signature = signer.sign(message)
            sign_time = time.perf_counter_ns() - start

        # Verification
        with oqs.Signature(algorithm) as verifier:
            start = time.perf_counter_ns()
            valid = verifier.verify(message, signature, public_key)
            verify_time = time.perf_counter_ns() - start

        if not valid:
            raise RuntimeError(
                f"{algorithm}: signature verification failed on trial {trial}"
            )

        operations["keygen"].append(keygen_time)
        operations["sign"].append(sign_time)
        operations["verify"].append(verify_time)

    return operations


def main():
    configure_cpu_affinity()

    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    raw_rows = []
    summary_rows = []

    for algorithm in ALGORITHMS:
        print(f"\nBenchmarking {algorithm}...")

        results = benchmark_algorithm(algorithm)

        for operation, measurements in results.items():
            for trial, elapsed_ns in enumerate(measurements, start=1):
                raw_rows.append({
                    "Algorithm": algorithm,
                    "Operation": operation,
                    "Trial": trial,
                    "Time_ns": elapsed_ns,
                })

            median_ms = statistics.median(measurements) / 1_000_000

            summary_rows.append({
                "algorithm": algorithm,
                f"{operation}_median_ms": median_ms,
            })

            print(f"{operation}: median = {median_ms:.6f} ms")

    with RAW_OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Algorithm", "Operation", "Trial", "Time_ns"],
        )
        writer.writeheader()
        writer.writerows(raw_rows)

    with SUMMARY_OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "algorithm",
                "keygen_median_ms",
                "sign_median_ms",
                "verify_median_ms",
            ],
        )
        writer.writeheader()

        for row in summary_rows:
            writer.writerow({
                "algorithm": row["algorithm"],
                "keygen_median_ms": row.get("keygen_median_ms", ""),
                "sign_median_ms": row.get("sign_median_ms", ""),
                "verify_median_ms": row.get("verify_median_ms", ""),
            })

    print(f"\nRaw measurements saved to: {RAW_OUTPUT}")
    print(f"Summary saved to: {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
