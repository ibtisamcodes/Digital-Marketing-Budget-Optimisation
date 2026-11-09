"""
Standalone Benchmark Runner for DS391 Big Data Analytics.
Executes the synthetic scalability benchmark suite (1x, 10x, 100x)
and outputs structured JSON and chart artifacts.
"""

import io
import os
import sys
import tempfile

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

from src.loader import load_dataset
from src.benchmark import run_scalability_benchmarks
from src.visualizer import plot_benchmark_results
from src.report_gen import save_json_metrics, save_csv_benchmarks


def main():
    print("=" * 70)
    print("   DS391 BENCHMARK RUNNER: SYNTHETIC SCALABILITY STRESS TEST   ")
    print("=" * 70)

    df, file_path = load_dataset()
    print(f"Loaded ground-truth base data: {file_path} ({len(df):,} rows)")

    benchmarks = run_scalability_benchmarks(df, multipliers=[1, 10, 100], n_iterations=3)

    print("\nBenchmark Results Summary:")
    print("-" * 70)
    print(f"{'Scale':<12} {'Rows':<12} {'Mean Time (s)':<16} {'Peak Mem (MB)':<16} {'Throughput':<15}")
    print("-" * 70)
    for w in benchmarks["workloads"]:
        print(
            f"{w['multiplier']}x{'':<10} "
            f"{w['row_count']:<12,} "
            f"{w['mean_runtime_seconds']:<16.4f} "
            f"{w['peak_memory_mb']:<16.2f} "
            f"{w['throughput_rows_per_sec']:<15,.1f} rows/s"
        )
    print("-" * 70)

    json_path = save_json_metrics(benchmarks, "outputs/benchmark_results.json")
    csv_path = save_csv_benchmarks(benchmarks, "outputs/benchmark_results.csv")
    chart_path = plot_benchmark_results(benchmarks, "outputs/charts/scalability_benchmarks.png")

    print(f"\nSaved benchmark JSON to: {json_path}")
    print(f"Saved benchmark CSV to: {csv_path}")
    print(f"Saved benchmark visualization to: {chart_path}")


if __name__ == "__main__":
    main()

