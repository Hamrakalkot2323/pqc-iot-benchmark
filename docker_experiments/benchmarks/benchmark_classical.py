
import csv
import os
import platform
import statistics
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa


# -------------------- Configuration --------------------

WARMUP_TRIALS = 5
RECORDED_TRIALS = 30

PROJECT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_DIR / "results" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PROFILE = os.environ.get("PQC_PROFILE", "UNKNOWN")
OUTPUT_FILE = OUTPUT_DIR / f"classical_{TIMESTAMP}.csv"

MESSAGE = b"Post-quantum cryptography benchmark test message"

RSA_PADDING = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)


# -------------------- Helpers --------------------

def measure_ns(function):
    start = time.perf_counter_ns()
    result = function()
    elapsed = time.perf_counter_ns() - start
    return result, elapsed


def benchmark_rsa():
    algorithm = "RSA-2048"
    print(f"\nBenchmarking {algorithm}...")

    operations = {
        "keygen": [],
        "encryption": [],
        "decryption": [],
    }

    # Warm-up trials
    for _ in range(WARMUP_TRIALS):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        ciphertext = private_key.public_key().encrypt(
            MESSAGE, RSA_PADDING
        )
        plaintext = private_key.decrypt(ciphertext, RSA_PADDING)

        if plaintext != MESSAGE:
            raise RuntimeError("RSA warm-up correctness check failed")

    # Recorded trials
    for trial in range(1, RECORDED_TRIALS + 1):
        private_key, keygen_ns = measure_ns(
            lambda: rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
        )

        ciphertext, encryption_ns = measure_ns(
            lambda: private_key.public_key().encrypt(
                MESSAGE, RSA_PADDING
            )
        )

        plaintext, decryption_ns = measure_ns(
            lambda: private_key.decrypt(ciphertext, RSA_PADDING)
        )

        if plaintext != MESSAGE:
            raise RuntimeError(f"RSA decryption failed in trial {trial}")

        operations["keygen"].append(keygen_ns)
        operations["encryption"].append(encryption_ns)
        operations["decryption"].append(decryption_ns)

        if trial % 10 == 0:
            print(f"  Completed {trial}/{RECORDED_TRIALS} trials")

    return operations


def benchmark_ecdsa():
    algorithm = "ECDSA-P256-SHA256"
    print(f"\nBenchmarking {algorithm}...")

    operations = {
        "keygen": [],
        "sign": [],
        "verify": [],
    }

    # Warm-up trials
    for _ in range(WARMUP_TRIALS):
        private_key = ec.generate_private_key(ec.SECP256R1())
        signature = private_key.sign(
            MESSAGE, ec.ECDSA(hashes.SHA256())
        )
        private_key.public_key().verify(
            signature, MESSAGE, ec.ECDSA(hashes.SHA256())
        )

    # Recorded trials
    for trial in range(1, RECORDED_TRIALS + 1):
        private_key, keygen_ns = measure_ns(
            lambda: ec.generate_private_key(ec.SECP256R1())
        )

        signature, sign_ns = measure_ns(
            lambda: private_key.sign(
                MESSAGE, ec.ECDSA(hashes.SHA256())
            )
        )

        def verify_signature():
            try:
                private_key.public_key().verify(
                    signature, MESSAGE, ec.ECDSA(hashes.SHA256())
                )
                return True
            except InvalidSignature:
                return False

        valid, verify_ns = measure_ns(verify_signature)

        if not valid:
            raise RuntimeError(
                f"ECDSA verification failed in trial {trial}"
            )

        operations["keygen"].append(keygen_ns)
        operations["sign"].append(sign_ns)
        operations["verify"].append(verify_ns)

        if trial % 10 == 0:
            print(f"  Completed {trial}/{RECORDED_TRIALS} trials")

    return operations


# -------------------- Run and save results --------------------

def main():
    print("Classical Cryptography Benchmark")
    print(f"Python version: {platform.python_version()}")
    print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
    print(f"Experiment profile: {PROFILE}")
    print(f"Warm-ups per algorithm: {WARMUP_TRIALS}")
    print(f"Recorded trials per operation: {RECORDED_TRIALS}")

    all_measurements = [
        ("RSA-2048", benchmark_rsa()),
        ("ECDSA-P256-SHA256", benchmark_ecdsa()),
    ]

    rows = []

    for algorithm, measurements in all_measurements:
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
            print(
                f"  {algorithm} {operation} median: "
                f"{median_ms:.6f} ms"
            )

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
