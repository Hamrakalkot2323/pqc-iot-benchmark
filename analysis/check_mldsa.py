
import oqs

print("Available ML-DSA algorithms:\n")

for algorithm in oqs.get_enabled_sig_mechanisms():
    if algorithm.startswith("ML-DSA"):
        print(algorithm)
