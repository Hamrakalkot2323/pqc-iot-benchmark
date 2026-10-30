
import csv
import glob
import os
import re
from datetime import datetime

RAW_DIR = "results/raw"
OUTPUT_FILE = "results/analysis/verified_runs.csv"

FIELDS = [
    "timing_file",
    "run_id",
    "profile",
    "benchmark",
    "status",
    "exit_code",
    "resource_file",
    "timestamp_delta_seconds",
]

FAMILIES = {"kem", "mldsa", "classical"}
PROFILES = {"C0", "C1", "C2", "C3"}


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def timestamp_from_name(name):
    match = re.search(r"_(\d{8}T\d{6})Z\.csv$", name)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y%m%dT%H%M%S")


def main():
    verified = {}
    rejected = []

    for timing_path in sorted(glob.glob(os.path.join(RAW_DIR, "*.csv"))):
        timing_name = os.path.basename(timing_path)

        if not timing_name.startswith(("kem_", "mldsa_", "classical_")):
            continue

        family = timing_name.split("_", 1)[0]
        timing_time = timestamp_from_name(timing_name)

        if timing_time is None:
            continue

        try:
            timing_rows = read_csv(timing_path)
            if not timing_rows:
                rejected.append((timing_name, "empty timing file"))
                continue

            profiles = {r.get("profile", "").strip() for r in timing_rows}
            if len(profiles) != 1 or not profiles.issubset(PROFILES):
                rejected.append((timing_name, "unknown/inconsistent profile"))
                continue

            profile = next(iter(profiles))
        except Exception as exc:
            rejected.append((timing_name, f"could not read timing file: {exc}"))
            continue

        candidates = []

        for status_path in glob.glob(os.path.join(RAW_DIR, "status_*.csv")):
            try:
                status_rows = read_csv(status_path)
            except Exception:
                continue

            for status in status_rows:
                run_id = status.get("run_id", "").strip()
                if not run_id:
                    continue

                try:
                    run_time = datetime.strptime(
                        run_id.split("_", 1)[0], "%Y%m%dT%H%M%S"
                    )
                except ValueError:
                    continue

                delta = abs((timing_time - run_time).total_seconds())

                if (
                    delta <= 15
                    and status.get("profile") == profile
                    and status.get("benchmark") == family
                    and status.get("status") == "success"
                    and status.get("exit_code") == "0"
                    and status.get("oom_confirmed", "").lower() == "false"
                ):
                    candidates.append((delta, run_id, status))

        if not candidates:
            rejected.append((timing_name, "no matching successful status record"))
            continue

        candidates.sort()
        delta, run_id, status = candidates[0]

        resource_name = f"resource_{run_id}.csv"
        resource_path = os.path.join(RAW_DIR, resource_name)

        if not os.path.isfile(resource_path):
            rejected.append((timing_name, "matching resource file missing"))
            continue

        try:
            resource_rows = read_csv(resource_path)
        except Exception:
            rejected.append((timing_name, "resource file unreadable"))
            continue

        matching_resource = any(
            r.get("profile") == profile
            and r.get("benchmark") == f"benchmark_{family}.py"
            and r.get("exit_code") == "0"
            for r in resource_rows
        )

        if not matching_resource:
            rejected.append((timing_name, "resource record did not validate"))
            continue

        verified[timing_name] = {
            "timing_file": timing_name,
            "run_id": run_id,
            "profile": profile,
            "benchmark": family,
            "status": status["status"],
            "exit_code": status["exit_code"],
            "resource_file": resource_name,
            "timestamp_delta_seconds": int(delta),
        }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for name in sorted(verified):
            writer.writerow(verified[name])

    print(f"Verified timing files: {len(verified)}")
    print(f"Rejected/unmatched timing files: {len(rejected)}")
    print(f"Manifest saved to: {OUTPUT_FILE}")

    for name, reason in rejected:
        print(f"  SKIPPED: {name} — {reason}")


if __name__ == "__main__":
    main()
