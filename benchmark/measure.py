
import time


def measure_time(function):
    start = time.perf_counter_ns()
    function()
    end = time.perf_counter_ns()

    return end - start


def benchmark_function(function, warmup_runs=5, recorded_trials=30):
    # Warm-up runs: execute without recording the timings
    for _ in range(warmup_runs):
        function()

    # Recorded runs
    measurements = []

    for _ in range(recorded_trials):
        elapsed_ns = measure_time(function)
        measurements.append(elapsed_ns)

    return measurements

