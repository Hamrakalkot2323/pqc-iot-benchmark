
import psutil
import os

process = psutil.Process(os.getpid())

print("Original CPU affinity:", process.cpu_affinity())
print("Available logical CPUs:", psutil.cpu_count())

# Temporarily restrict this test process to one logical CPU.
original_affinity = process.cpu_affinity()

try:
    process.cpu_affinity([original_affinity[0]])
    print("Restricted CPU affinity:", process.cpu_affinity())
finally:
    # Restore the original affinity before the script exits.
    process.cpu_affinity(original_affinity)
    print("Restored CPU affinity:", process.cpu_affinity())
