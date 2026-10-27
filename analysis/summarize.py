
import statistics


def summarize_measurements(measurements):
    median_value = statistics.median(measurements)

    quartiles = statistics.quantiles(
        measurements,
        n=4,
        method="inclusive"
    )

    q1 = quartiles[0]
    q3 = quartiles[2]
    iqr = q3 - q1

    return median_value, iqr
