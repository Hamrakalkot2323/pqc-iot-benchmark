
import csv
import os
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import oqs


# -------------------- Configuration --------------------

ALGORITHMS = ["ML-DSA-44", "ML-DSA-65"]
WARMUP_TRIALS = 5
RECORDED_TRIALS = 30

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "results" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PROFILE = os.environ.get("PQC_PROFILE", "UNKNOWN")
OUTPUT_FILE = OUTPUT_DIR / f"mldsa_{TIMESTAMP}.csv"

MESSAGE = b"Post-quantum cryptography benchmark test message"


# -------------------- Benchmark functions --------------------

def benchmark_algorithm(algorithm):
    print(f"\nBenchmarking {algorithm}...")

    operations = {
        "keygen": [],
        "sign": [],
        "verify": [],
    }

    # Warm-up operations are excluded from recorded measurements.
    for _ in range(WARMUP_TRIALS):
        with oqs.Signature(algorithm) as signer:
            public_key = signer.generate_keypair()
            signature = signer.sign(MESSAGE)

            if not signer.verify(MESSAGE, signature, public_key):
                raise RuntimeError(
                    f"Signature verification failed during warm-up: {algorithm}"
                )

    # Collect recorded measurements.
    for trial in range(1, RECORDED_TRIALS + 1):
        with oqs.Signature(algorithm) as signer:
            start = time.perf_counter_ns()
            public_key = signer.generate_keypair()
            keygen_ns = time.perf_counter_ns() - start

            start = time.perf_counter_ns()
            signature = signer.sign(MESSAGE)
            sign_ns = time.perf_counter_ns() - start

            start = time.perf_counter_ns()
            valid = signer.verify(MESSAGE, signature, public_key)
            verify_ns = time.perf_counter_ns() - start

            if not valid:
                raise RuntimeError(
                    f"Signature verification failed for {algorithm}, trial {trial}"
                )

            operations["keygen"].append(keygen_ns)
            operations["sign"].append(sign_ns)
            operations["verify"].append(verify_ns)

        if trial % 10 == 0:
            print(f"  Completed {trial}/{RECORDED_TRIALS} trials")

    return operations


# -------------------- Run and save results --------------------

def main():
    print("Post-Quantum Cryptography: ML-DSA Benchmark")
    print(f"liboqs version: {oqs.oqs_version()}")
    print(f"Python version: {platform.python_version()}")
    print(f"Experiment profile: {PROFILE}")
    print(f"Warm-ups per algorithm: {WARMUP_TRIALS}")
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
