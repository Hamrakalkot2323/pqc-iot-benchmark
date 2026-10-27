
import csv
import time

from benchmark.measure import benchmark_function


def example_operation():
    time.sleep(0.01)


measurements = benchmark_function(
    example_operation,
    warmup_runs=5,
    recorded_trials=30,
)

with open("results/raw/test_results.csv", "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow(["Algorithm", "Operation", "Trial", "Time_ns"])

    for trial_number, elapsed_ns in enumerate(measurements, start=1):
        writer.writerow([
            "TEST",
            "example_operation",
            trial_number,
            elapsed_ns,
        ])

print("Recorded measurements:", len(measurements))
print("CSV saved successfully!")
