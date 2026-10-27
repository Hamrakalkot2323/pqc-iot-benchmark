
from analysis.summarize import summarize_measurements

timings = [8, 12, 9, 100, 11]

median_value, iqr = summarize_measurements(timings)

print("Measurements:", timings)
print("Median:", median_value)
print("IQR:", iqr)


