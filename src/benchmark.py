"""
Scalability Benchmarking Module for DS391 Big Data Analytics.
Executes performance stress tests on 1x, 10x, and 100x synthetic workloads,
measuring precise wall-clock runtime and peak heap memory via tracemalloc.
"""

import time
import tracemalloc
from typing import Any
import numpy as np
import pandas as pd

from src.inspection import inspect_dataset
from src.statistics import calculate_descriptive_statistics
from src.text_temporal import analyze_temporal, analyze_text


def run_pipeline_operations(workload_df: pd.DataFrame) -> dict[str, Any]:
    """
    Executes the analytical pipeline processing tasks on a given DataFrame.
    """
    insp = inspect_dataset(workload_df)
    stats = calculate_descriptive_statistics(workload_df)
    temp = analyze_temporal(workload_df)
    text = analyze_text(workload_df)
    return {
        "inspection": insp,
        "statistics": stats,
        "temporal": temp,
        "text": text,
    }


def benchmark_workload(
    df: pd.DataFrame,
    multiplier: int,
    scale_label: str,
    n_iterations: int = 3,
) -> dict[str, Any]:
    """
    Runs repeated benchmark iterations for a specified synthetic workload scale,
    tracking runtime and peak memory usage.
    """
    if multiplier == 1:
        workload_df = df.copy()
        is_synthetic = False
        workload_note = "Original Ground-Truth Dataset"
    else:
        # Synthetic scalability replication
        workload_df = pd.concat([df] * multiplier, ignore_index=True)
        is_synthetic = True
        workload_note = f"Synthetic Scalability Experiment (Replicated {multiplier}x)"

    row_count, col_count = workload_df.shape
    runtimes = []
    peak_memories = []

    for _ in range(n_iterations):
        tracemalloc.start()
        tracemalloc.reset_peak()
        start_time = time.perf_counter()

        _ = run_pipeline_operations(workload_df)

        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        runtimes.append(end_time - start_time)
        peak_memories.append(peak_mem / (1024 * 1024))  # Convert bytes to MB

    mean_runtime = float(np.mean(runtimes))
    std_runtime = float(np.std(runtimes))
    peak_memory_mb = float(np.max(peak_memories))
    throughput_rows_sec = round(row_count / mean_runtime, 1) if mean_runtime > 0 else 0.0

    return {
        "multiplier": multiplier,
        "scale_label": scale_label,
        "is_synthetic": is_synthetic,
        "workload_note": workload_note,
        "row_count": row_count,
        "col_count": col_count,
        "iterations": n_iterations,
        "mean_runtime_seconds": round(mean_runtime, 4),
        "std_runtime_seconds": round(std_runtime, 4),
        "min_runtime_seconds": round(float(np.min(runtimes)), 4),
        "max_runtime_seconds": round(float(np.max(runtimes)), 4),
        "peak_memory_mb": round(peak_memory_mb, 3),
        "throughput_rows_per_sec": throughput_rows_sec,
    }


def run_scalability_benchmarks(
    df: pd.DataFrame,
    multipliers: list[int] | None = None,
    n_iterations: int = 3,
) -> dict[str, Any]:
    """
    Executes benchmark suites across 1x, 10x, and 100x workloads.
    """
    if multipliers is None:
        multipliers = [1, 10, 100]

    workload_results = []
    for mult in multipliers:
        label = f"{mult}x ({mult * len(df):,} rows)"
        res = benchmark_workload(df, mult, label, n_iterations=n_iterations)
        workload_results.append(res)

    # Calculate empirical complexity scaling ratios
    base_runtime = workload_results[0]["mean_runtime_seconds"]
    base_memory = workload_results[0]["peak_memory_mb"]

    for w in workload_results:
        w["runtime_scale_factor"] = round(w["mean_runtime_seconds"] / base_runtime, 2) if base_runtime > 0 else 1.0
        w["memory_scale_factor"] = round(w["peak_memory_mb"] / base_memory, 2) if base_memory > 0 else 1.0

    return {
        "experiment_name": "DS391 Synthetic Scalability Stress Test",
        "dataset_name": "high-heels-te-nachche-video-song-ki-ka-meet-bros-",
        "label": "Synthetic Scalability Experiment",
        "disclaimer": (
            "NOTICE: The 10x and 100x workloads are generated via synthetic in-memory "
            "replication of the original ground-truth 1,166 rows to simulate large-scale "
            "data stream processing and evaluate algorithmic time/space complexity."
        ),
        "iterations_per_workload": n_iterations,
        "workloads": workload_results,
    }

