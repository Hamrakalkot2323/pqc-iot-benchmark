
# Cryptographic algorithms to benchmark

KEM_ALGORITHMS = [
    "ML-KEM-512",
    "ML-KEM-768",
]

SIGNATURE_ALGORITHMS = [
    "ML-DSA-44",
    "ML-DSA-65",
]

CLASSICAL_ALGORITHMS = [
    "RSA-2048",
    "ECDSA-P256",
]

# Benchmark settings
WARMUP_RUNS = 5
RECORDED_TRIALS = 30
MESSAGE_SIZE_BYTES = 1024


# Operations we want to measure

KEM_OPERATIONS = [
    "keygen",
    "encapsulation",
    "decapsulation",
]

SIGNATURE_OPERATIONS = [
    "keygen",
    "sign",
    "verify",
]

RSA_OPERATIONS = [
    "keygen",
    "encrypt",
    "decrypt",
]

ECDSA_OPERATIONS = [
    "keygen",
    "sign",
    "verify",
]
