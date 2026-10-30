import argparse
import csv
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_DIR / "config" / "profiles.json"
RAW_DIR = PROJECT_DIR / "results" / "raw"

BENCHMARKS = {
    "kem": "benchmark_kem.py",
    "mldsa": "benchmark_mldsa.py",
    "classical": "benchmark_classical.py",
}


def load_config():
    with CONFIG_FILE.open("r") as file:
        return json.load(file)


def find_profile(config, profile_id):
    for profile in config["profiles"]:
        if profile["id"] == profile_id:
            return profile
    raise ValueError(f"Unknown profile: {profile_id}")


def docker_call(args, check=True):
    return subprocess.run(
        ["sudo", "docker", *args],
        cwd=PROJECT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def write_csv(path, fieldnames, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description="Run a cryptographic benchmark in Docker."
    )
    parser.add_argument(
        "--profile", required=True, choices=["C0", "C1", "C2", "C3"]
    )
    parser.add_argument(
        "--benchmark", required=True, choices=BENCHMARKS.keys()
    )
    args = parser.parse_args()

    config = load_config()
    profile = find_profile(config, args.profile)
    benchmark_file = BENCHMARKS[args.benchmark]

    run_id = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S"
    ) + f"_{time.time_ns() % 1_000_000:06d}"

    container_name = f"pqc-{run_id.lower()}"
    resource_file = RAW_DIR / f"resource_{run_id}.csv"
    status_file = RAW_DIR / f"status_{run_id}.csv"
    container_resource_path = f"/app/results/raw/{resource_file.name}"

    command = ["run", "--name", container_name]

    if profile["cpus"] is not None:
        command.extend(["--cpus", str(profile["cpus"])])

    if profile["memory_mib"] is not None:
        command.extend([
            "--memory", f"{profile['memory_mib']}m",
            "--memory-swap", f"{profile['memory_swap_mib']}m",
        ])

    # Run the benchmark and record cgroup measurements before exit.
    shell_script = (
        f"python /app/benchmarks/{benchmark_file}; "
        "benchmark_status=$?; "

        # Memory measurements
        "peak=$(cat /sys/fs/cgroup/memory.peak 2>/dev/null || true); "
        "limit=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || true); "

        # CPU measurements: read all counters from one snapshot
        "cpu_stats=$(cat /sys/fs/cgroup/cpu.stat 2>/dev/null || true); "
        "cpu_usage=$(printf '%s\\n' \"$cpu_stats\" | "
        "awk '$1 == \"usage_usec\" {print $2}'); "
        "cpu_periods=$(printf '%s\\n' \"$cpu_stats\" | "
        "awk '$1 == \"nr_periods\" {print $2}'); "
        "cpu_throttled=$(printf '%s\\n' \"$cpu_stats\" | "
        "awk '$1 == \"nr_throttled\" {print $2}'); "
        "cpu_throttled_usec=$(printf '%s\\n' \"$cpu_stats\" | "
        "awk '$1 == \"throttled_usec\" {print $2}'); "

        # Write resource CSV header
        f"printf '%s\\n' "
        "'profile,benchmark,exit_code,memory_limit_bytes,"
        "peak_memory_bytes,cpu_usage_usec,cpu_nr_periods,"
        "cpu_nr_throttled,cpu_throttled_usec' "
        f"> '{container_resource_path}'; "

        # Write resource CSV data
        "printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\\n' "
        f"'{profile['id']}' '{benchmark_file}' "
        '"$benchmark_status" "$limit" "$peak" '
        '"$cpu_usage" "$cpu_periods" "$cpu_throttled" '
        '"$cpu_throttled_usec" '
        f">> '{container_resource_path}'; "

        # Preserve the original benchmark exit code
        'exit "$benchmark_status"'
    )

    command.extend([
        "-e", f"PQC_PROFILE={profile['id']}",
        "-v", f"{PROJECT_DIR}:/app",
        "pqc-benchmark:latest",
        "sh", "-c", shell_script,
    ])

    print(f"Run ID: {run_id}")
    print(f"Profile: {profile['id']} — {profile['name']}")
    print(f"Benchmark: {args.benchmark}")
    print("Starting benchmark...\n", flush=True)

    exit_code = None
    oom_confirmed = "unknown"
    status = "failed"

    try:
        result = docker_call(command, check=False)
        exit_code = result.returncode

        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")

        # Inspect the named container before cleanup.
        inspect_result = docker_call([
            "inspect", "--format",
            "{{.State.OOMKilled}}|{{.State.ExitCode}}",
            container_name,
        ], check=False)

        if inspect_result.returncode == 0:
            details = inspect_result.stdout.strip().split("|")
            if len(details) == 2:
                oom_confirmed = details[0].lower()
                if details[1].isdigit():
                    exit_code = int(details[1])

        if oom_confirmed == "true":
            status = "oom_killed"
        elif exit_code == 0:
            status = "success"

    except (OSError, subprocess.SubprocessError) as error:
        print(f"Docker execution/inspection error: {error}")

    finally:
        write_csv(
            status_file,
            [
                "run_id", "profile", "benchmark", "exit_code",
                "status", "oom_confirmed",
            ],
            {
                "run_id": run_id,
                "profile": profile["id"],
                "benchmark": args.benchmark,
                "exit_code": (
                    exit_code if exit_code is not None else ""
                ),
                "status": status,
                "oom_confirmed": oom_confirmed,
            },
        )

        # Remove only this run's named container.
        cleanup = docker_call(
            ["rm", "-f", container_name],
            check=False,
        )
        if cleanup.returncode != 0 and cleanup.stderr:
            print(
                f"Container cleanup note: {cleanup.stderr.strip()}"
            )

    print(f"\nRun status saved to {status_file}")
    if resource_file.exists():
        print(f"Resource measurements saved to {resource_file}")

    if status != "success":
        raise SystemExit(
            f"Benchmark did not complete successfully: {status}. "
            "Review the status CSV and Docker output."
        )

    print("\nBenchmark completed successfully.")


if __name__ == "__main__":
    main()

