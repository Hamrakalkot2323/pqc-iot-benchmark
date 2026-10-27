
import csv
import os
import statistics
import time

import oqs

ALGORITHMS = ["ML-DSA-44", "ML-DSA-65"]
ITERATIONS = 100
WARMUP_ITERATIONS = 5
MESSAGE = b"Test message for PQC benchmark"

RAW_OUTPUT_PATH = "results/raw/dsa_raw_results.csv"
RAW_FIELDNAMES = ["Algorithm", "Operation", "Trial", "Time_ns"]


def benchmark_dsa(algorithm, iterations=ITERATIONS):
    keygen_times = []
    sign_times = []
    verify_times = []
    raw_results = []

    public_key = None
    signature = None

    for i in range(iterations + WARMUP_ITERATIONS):
        with oqs.Signature(algorithm) as signer:
            # Measure key generation
            start = time.perf_counter_ns()
            public_key = signer.generate_keypair()
            keygen_ns = time.perf_counter_ns() - start

            # Measure signing
            start = time.perf_counter_ns()
            signature = signer.sign(MESSAGE)
            sign_ns = time.perf_counter_ns() - start

        # Use a separate verifier so verification is measured independently
        with oqs.Signature(algorithm) as verifier:
            start = time.perf_counter_ns()
            valid = verifier.verify(MESSAGE, signature, public_key)
            verify_ns = time.perf_counter_ns() - start

        if not valid:
            raise RuntimeError(
                f"Signature verification failed for {algorithm}"
            )

        # A modified message must not verify successfully
        with oqs.Signature(algorithm) as verifier:
            if verifier.verify(MESSAGE + b"!", signature, public_key):
                raise RuntimeError(
                    f"Tampered message accepted for {algorithm}"
                )

        # Exclude warm-up measurements
        if i >= WARMUP_ITERATIONS:
            trial = i - WARMUP_ITERATIONS + 1

            keygen_times.append(keygen_ns / 1_000_000)
            sign_times.append(sign_ns / 1_000_000)
            verify_times.append(verify_ns / 1_000_000)

            raw_results.extend([
                {
                    "Algorithm": algorithm,
                    "Operation": "keygen",
                    "Trial": trial,
                    "Time_ns": keygen_ns,
                },
                {
                    "Algorithm": algorithm,
                    "Operation": "sign",
                    "Trial": trial,
                    "Time_ns": sign_ns,
                },
                {
                    "Algorithm": algorithm,
                    "Operation": "verify",
                    "Trial": trial,
                    "Time_ns": verify_ns,
                },
            ])

    return {
        "algorithm": algorithm,
        "iterations": iterations,
        "keygen_median_ms": statistics.median(keygen_times),
        "sign_median_ms": statistics.median(sign_times),
        "verify_median_ms": statistics.median(verify_times),
        "public_key_bytes": len(public_key),
        "signature_bytes": len(signature),
        "raw_results": raw_results,
    }


def main():
    os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)

    # Start a fresh raw-results file for this complete run
    with open(RAW_OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDNAMES)
        writer.writeheader()

    results = []

    for algorithm in ALGORITHMS:
        print(f"Benchmarking {algorithm}...")
        results.append(benchmark_dsa(algorithm))

    # Save the summary results
    os.makedirs("results", exist_ok=True)
    output_path = os.path.join("results", "dsa_benchmark.csv")

    summary_results = [
        {key: value for key, value in result.items() if key != "raw_results"}
        for result in results
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=summary_results[0].keys(),
        )
        writer.writeheader()
        writer.writerows(summary_results)

    # Save all individual measurements
    with open(RAW_OUTPUT_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDNAMES)

        for result in results:
            writer.writerows(result["raw_results"])

    # Display summary results
    for result in summary_results:
        print(f"\n{result['algorithm']}")
        print(f"  Key generation median: {result['keygen_median_ms']:.6f} ms")
        print(f"  Signing median:        {result['sign_median_ms']:.6f} ms")
        print(f"  Verification median:   {result['verify_median_ms']:.6f} ms")
        print(f"  Public key size:       {result['public_key_bytes']} bytes")
        print(f"  Signature size:        {result['signature_bytes']} bytes")

    print(f"\nSummary CSV saved to: {output_path}")
    print(f"Raw timings saved to: {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    main()

