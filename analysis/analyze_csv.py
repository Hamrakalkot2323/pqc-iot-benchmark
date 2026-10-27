
import csv
import statistics


def load_timings(csv_path):
    timings = []

    with open(csv_path, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            timings.append(int(row["Time_ns"]))

    return timings


def analyze_timings(timings):
    median_value = statistics.median(timings)

    quartiles = statistics.quantiles(
        timings,
        n=4,
        method="inclusive",
    )

    iqr = quartiles[2] - quartiles[0]

    return median_value, iqr


if __name__ == "__main__":
    timings = load_timings("results/raw/test_results.csv")

    median_value, iqr = analyze_timings(timings)

    print("Number of measurements:", len(timings))
    print("Median (ns):", median_value)
    print("IQR (ns):", iqr)
