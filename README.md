# Performance Analysis of Post-Quantum Cryptographic Algorithms Under Simulated Resource Constraints for IoT Applications

## Overview

This project investigates the performance of post-quantum cryptographic algorithms under different CPU-affinity settings, with a focus on their potential use in resource-constrained Internet of Things (IoT) environments.

The experiments benchmark key generation, encapsulation, and decapsulation for ML-KEM, alongside key generation, signing, and verification for ML-DSA. Repeated runs are used to examine timing variability and compare results across CPU-affinity settings.

**Note:** CPU affinity limits which logical processors a process may run on. It does not directly simulate a slower processor, a fixed CPU-frequency limit, or a complete IoT device.

## Algorithms

### ML-KEM — Key Encapsulation Mechanism

The experiments include:

- ML-KEM-512
- ML-KEM-768

Measured operations:

- Key generation
- Encapsulation
- Decapsulation

### ML-DSA — Digital Signature Algorithm

The experiments include:

- ML-DSA-44
- ML-DSA-65

Measured operations:

- Key generation
- Signing
- Verification

## Experimental Methodology

The benchmark scripts use Python bindings for `liboqs` and measure operation durations with a high-resolution performance timer.

The current experiments include:

- CPU-affinity settings of 1, 2, 4, and 8 logical CPUs
- Warm-up iterations before recorded measurements
- Repeated benchmark runs for selected settings
- Median timing summaries
- Raw timing data stored in CSV files
- Comparison plots and run-to-run variability analysis

The experiments were conducted on a Windows development machine. The findings should therefore be interpreted as preliminary measurements of this particular environment, rather than direct evidence of performance on an IoT device.

## Repository Structure

```text
pqc-iot-benchmark/
├── analysis/       # Data analysis and plotting scripts
├── benchmark/      # Supporting benchmark modules
├── benchmarks/     # ML-KEM and ML-DSA benchmark scripts
└── results/
    ├── raw/        # Raw timing measurements
    ├── summary/    # Summary tables
    └── *.png       # Generated plots
```

## Results and Analysis

The `results/` directory contains CSV files and plots generated during the experiments.

The analysis focuses on:

- Comparing operation timings between algorithm parameter sets
- Examining differences across CPU-affinity settings
- Comparing repeated runs
- Identifying variability that may affect interpretation

Timing results can be influenced by background processes, processor frequency, thermal conditions, and other system-level factors. Additional repetitions and more controlled experimental conditions are needed before drawing strong conclusions.

## Setup

The project was developed using Python and `liboqs` Python bindings.

To reproduce the experiments, you will need:

- Python
- Git
- CMake and a compatible C/C++ build toolchain
- A compatible build of `liboqs`
- The Python packages required by the benchmark scripts

Exact installation steps may vary by operating system and toolchain.

## Running the Benchmarks

From the project root, activate your Python virtual environment and configure `OQS_INSTALL_PATH` to point to your local `liboqs` build as required by the Python bindings.

Example PowerShell commands:

```powershell
$env:OQS_INSTALL_PATH = "C:\path\to\your\liboqs\build"
$env:BENCHMARK_CPUS = "2"
python benchmarks/benchmark_kem.py
```

For ML-DSA:

```powershell
$env:OQS_INSTALL_PATH = "C:\path\to\your\liboqs\build"
$env:BENCHMARK_CPUS = "2"
python benchmarks/benchmark_mldsa.py
```

Change `BENCHMARK_CPUS` to a supported setting when repeating experiments. These scripts may overwrite their default output CSV files, so preserve copies of each run if you want to compare repeated measurements.

## Limitations

- CPU affinity is not equivalent to simulating a slower IoT processor.
- The current measurements come from a Windows development environment rather than a representative range of IoT hardware.
- Run-to-run timing variability means that isolated results should not be overinterpreted.
- The Windows build toolchain produced a warning concerning optimization barriers and constant-time guarantees. These benchmarks should not be treated as a validation of production security or constant-time behavior.

## Future Work

Potential extensions include:

- Increasing the number of independent repetitions
- Controlling or recording system load and processor conditions
- Testing on Raspberry Pi or other representative IoT hardware
- Measuring memory consumption and resource usage
- Comparing the post-quantum algorithms with suitable classical cryptographic baselines
- Improving automated result aggregation and reproducibility

## Project Status

This is an ongoing experimental research project. Results and methodology may change as the experiments are extended and validated.