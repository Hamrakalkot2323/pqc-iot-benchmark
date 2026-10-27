
import csv
import os
import statistics
import time

import oqs
import psutil

ALGORITHMS = ["ML-KEM-512", "ML-KEM-768"]
ITERATIONS = 100
WARMUP_ITERATIONS = 5

RAW_OUTPUT_PATH = "results/raw/kem_raw_results.csv"
RAW_FIELDNAMES = ["Algorithm", "Operation", "Trial", "Time_ns"]


def configure_cpu_affinity():
    """Restrict this process to the requested number of logical CPUs."""
    requested_cpus = int(os.getenv("BENCHMARK_CPUS", "8"))

    process = psutil.Process()
    available_cpus = process.cpu_affinity()

    if requested_cpus not in (1, 2, 4, 8):
        raise ValueError(
            "BENCHMARK_CPUS must be 1, 2, 4, or 8."
        )

    if requested_cpus > len(available_cpus):
        raise ValueError(
            f"Requested {requested_cpus} CPUs, "
            f"but only {len(available_cpus)} are available."
        )

    selected_cpus = available_cpus[:requested_cpus]
    process.cpu_affinity(selected_cpus)

    print(f"Available logical CPUs: {len(available_cpus)}")
    print(f"Selected logical CPUs: {process.cpu_affinity()}")


def benchmark_kem(algorithm, iterations=ITERATIONS):
    keygen_times = []
    encaps_times = []
    decaps_times = []
    raw_results = []

    for i in range(iterations + WARMUP_ITERATIONS):
        with oqs.KeyEncapsulation(algorithm) as kem:
            # Measure key generation
            start = time.perf_counter_ns()
            public_key = kem.generate_keypair()
            keygen_ns = time.perf_counter_ns() - start

            # Measure encapsulation
            start = time.perf_counter_ns()
            ciphertext, shared_secret = kem.encap_secret(public_key)
            encaps_ns = time.perf_counter_ns() - start

            # Measure decapsulation
            start = time.perf_counter_ns()
            recovered_secret = kem.decap_secret(ciphertext)
            decaps_ns = time.perf_counter_ns() - start

            if shared_secret != recovered_secret:
                raise RuntimeError(
                    f"Shared-secret mismatch for {algorithm}"
                )

        # Exclude warm-up measurements from the results
        if i >= WARMUP_ITERATIONS:
            trial = i - WARMUP_ITERATIONS + 1

            keygen_times.append(keygen_ns / 1_000_000)
            encaps_times.append(encaps_ns / 1_000_000)
            decaps_times.append(decaps_ns / 1_000_000)

            raw_results.extend([
                {
                    "Algorithm": algorithm,
                    "Operation": "keygen",
                    "Trial": trial,
                    "Time_ns": keygen_ns,
                },
                {
                    "Algorithm": algorithm,
                    "Operation": "encaps",
                    "Trial": trial,
                    "Time_ns": encaps_ns,
                },
                {
                    "Algorithm": algorithm,
                    "Operation": "decaps",
                    "Trial": trial,
                    "Time_ns": decaps_ns,
                },
            ])

    os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)

    file_exists = (
        os.path.exists(RAW_OUTPUT_PATH)
        and os.path.getsize(RAW_OUTPUT_PATH) > 0
    )

    with open(RAW_OUTPUT_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        writer.writerows(raw_results)

    return {
        "algorithm": algorithm,
        "iterations": iterations,
        "keygen_median_ms": statistics.median(keygen_times),
        "encaps_median_ms": statistics.median(encaps_times),
        "decaps_median_ms": statistics.median(decaps_times),
        "public_key_bytes": len(public_key),
        "ciphertext_bytes": len(ciphertext),
    }


def main():
    configure_cpu_affinity()

    # Start a fresh raw-results file for each complete run
    os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)

    with open(RAW_OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDNAMES)
        writer.writeheader()

    results = []

    for algorithm in ALGORITHMS:
        print(f"\nBenchmarking {algorithm}...")
        results.append(benchmark_kem(algorithm))

    os.makedirs("results", exist_ok=True)
    output_path = os.path.join("results", "kem_benchmark.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    for result in results:
        print(f"\n{result['algorithm']}")
        print(f"  Key generation median: {result['keygen_median_ms']:.6f} ms")
        print(f"  Encapsulation median:  {result['encaps_median_ms']:.6f} ms")
        print(f"  Decapsulation median:  {result['decaps_median_ms']:.6f} ms")
        print(f"  Public key size:       {result['public_key_bytes']} bytes")
        print(f"  Ciphertext size:       {result['ciphertext_bytes']} bytes")

    print(f"\nSummary CSV saved to: {output_path}")
    print(f"Raw timings saved to: {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
