
import csv
import os
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path
import time

import oqs


PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "results" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PROFILE = os.environ.get("PQC_PROFILE", "UNKNOWN")

OUTPUT_FILE = OUTPUT_DIR / f"kem_{TIMESTAMP}.csv"

ALGORITHMS = ["ML-KEM-512", "ML-KEM-768"]
WARMUP_TRIALS = 5
RECORDED_TRIALS = 30


def benchmark_algorithm(algorithm):
    measurements = {
        "keygen": [],
        "encapsulation": [],
        "decapsulation": [],
    }

    print(f"\nBenchmarking {algorithm}...")

    with oqs.KeyEncapsulation(algorithm) as kem:
        # Warmup trials
        for _ in range(WARMUP_TRIALS):
            public_key = kem.generate_keypair()
            ciphertext, shared_secret = kem.encap_secret(public_key)
            recovered_secret = kem.decap_secret(ciphertext)

            if shared_secret != recovered_secret:
                raise RuntimeError(
                    f"{algorithm}: shared-secret mismatch during warmup"
                )

    for trial in range(1, RECORDED_TRIALS + 1):
        # Key generation
        with oqs.KeyEncapsulation(algorithm) as kem:
            start = time.perf_counter_ns()
            public_key = kem.generate_keypair()
            keygen_ns = time.perf_counter_ns() - start

        # Encapsulation
        with oqs.KeyEncapsulation(algorithm) as kem:
            public_key = kem.generate_keypair()

            start = time.perf_counter_ns()
            ciphertext, shared_secret = kem.encap_secret(public_key)
            encapsulation_ns = time.perf_counter_ns() - start

            # Decapsulation
            start = time.perf_counter_ns()
            recovered_secret = kem.decap_secret(ciphertext)
            decapsulation_ns = time.perf_counter_ns() - start

        if shared_secret != recovered_secret:
            raise RuntimeError(
                f"{algorithm}: shared-secret mismatch in trial {trial}"
            )

        measurements["keygen"].append(keygen_ns)
        measurements["encapsulation"].append(encapsulation_ns)
        measurements["decapsulation"].append(decapsulation_ns)

        if trial % 10 == 0:
            print(f"  Completed {trial}/{RECORDED_TRIALS} trials")

    return measurements


def main():
    print("Post-Quantum Cryptography: ML-KEM Benchmark")
    print(f"liboqs version: {oqs.oqs_version()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Experiment profile: {PROFILE}")
    print(f"Warmups per algorithm: {WARMUP_TRIALS}")
    print(f"Recorded trials per algorithm: {RECORDED_TRIALS}")

    rows = []

    for algorithm in ALGORITHMS:
        measurements = benchmark_algorithm(algorithm)

        for operation, values in measurements.items():
            for trial, elapsed_ns in enumerate(values, start=1):
                rows.append({
                    "timestamp_utc": TIMESTAMP,
                    "profile": PROFILE,
                    "algorithm": algorithm,
                    "operation": operation,
                    "trial": trial,
                    "time_ns": elapsed_ns,
                    "time_ms": elapsed_ns / 1_000_000,
                })

            median_ms = statistics.median(values) / 1_000_000
            print(f"  {operation} median: {median_ms:.6f} ms")

    with OUTPUT_FILE.open("w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "timestamp_utc",
                "profile",
                "algorithm",
                "operation",
                "trial",
                "time_ns",
                "time_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} measurements to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

