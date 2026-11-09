"""
Main Execution Script for the DS391 YouTube Comment Analytics Pipeline.
Executes data loading, inspection, statistics, NLP/temporal analysis,
visualizations, synthetic scalability benchmarking, and report generation.
"""

import io
import os
import sys
import tempfile
from pathlib import Path

# Force UTF-8 stdout for Windows console emoji support
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Writable directory for matplotlib
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

from src.loader import load_dataset
from src.inspection import inspect_dataset
from src.statistics import calculate_descriptive_statistics
from src.text_temporal import analyze_temporal, analyze_text
from src.visualizer import (
    plot_engagement_distribution,
    plot_temporal_trends,
    plot_text_analysis,
    plot_benchmark_results,
)
from src.benchmark import run_scalability_benchmarks
from src.report_gen import save_json_metrics, save_csv_benchmarks, generate_markdown_report


def main():
    print("=" * 75)
    print("   DS391 BIG DATA ANALYTICS PIPELINE: YOUTUBE COMMENT ANALYSIS   ")
    print("=" * 75)

    # 1. Automated CSV Discovery and Loading
    print("\n[Step 1/7] Discovering and loading CSV from data/raw/...")
    try:
        df, file_path = load_dataset()
        print(f"  --> Successfully loaded dataset: {file_path}")
        print(f"  --> Dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    except Exception as e:
        print(f"  [ERROR] Failed to load dataset: {e}")
        sys.exit(1)

    # 2. Structural Inspection
    print("\n[Step 2/7] Inspecting schema, missing values, and duplicates...")
    inspection = inspect_dataset(df)
    print(f"  --> Total Rows: {inspection['total_rows']:,}")
    print(f"  --> Total Columns: {inspection['total_columns']} -> {inspection['column_names']}")
    print(f"  --> Full Duplicate Rows: {inspection['full_duplicate_rows']}")
    print(f"  --> Duplicate Comment Strings: {inspection['duplicate_comments_text']}")
    print(f"  --> Missing Values: {sum(c['null_count'] for c in inspection['column_inspection'].values())}")

    # 3. Descriptive Statistics
    print("\n[Step 3/7] Calculating descriptive statistics for likes and reply_count...")
    stats = calculate_descriptive_statistics(df)
    likes_s = stats["likes"]
    rep_s = stats["reply_count"]
    print(f"  --> Likes: Mean={likes_s['mean']}, Median={likes_s['median']}, Std={likes_s['std']}, Max={likes_s['max']}")
    print(f"  --> Replies: Mean={rep_s['mean']}, Median={rep_s['median']}, Std={rep_s['std']}, Max={rep_s['max']}")
    print(f"  --> Gini Coefficients: Likes={likes_s['gini_coefficient']}, Replies={rep_s['gini_coefficient']}")

    # 4. Temporal and Text Analysis
    print("\n[Step 4/7] Performing temporal timeline and text NLP analysis...")
    temporal = analyze_temporal(df)
    text_data = analyze_text(df)
    era = temporal["era_breakdown"]
    print(f"  --> Timeline: {temporal['earliest_comment_utc'][:10]} to {temporal['latest_comment_utc'][:10]} ({temporal['total_span_days']} days)")
    print(f"  --> Resurgence Era (2025-2026): {era['resurgence_phase_2025_2026']} comments ({era['resurgence_share_pct']}%)")
    print(f"  --> Top Thematic Mentions: Honey Singh ({text_data['thematic_mentions']['honey_singh']}), Kareena Kapoor ({text_data['thematic_mentions']['kareena_kapoor']})")

    # 5. Scalability Benchmarking
    print("\n[Step 5/7] Running synthetic scalability benchmarking (1x, 10x, 100x workloads)...")
    benchmarks = run_scalability_benchmarks(df, multipliers=[1, 10, 100], n_iterations=3)
    for w in benchmarks["workloads"]:
        print(f"  --> {w['scale_label']}: {w['mean_runtime_seconds']:.4f}s | Peak Mem: {w['peak_memory_mb']:.2f} MB | {w['throughput_rows_per_sec']:,.1f} rows/s")

    # 6. Chart Generation
    print("\n[Step 6/7] Generating publication-quality charts in outputs/charts/...")
    c1 = plot_engagement_distribution(df, "outputs/charts/likes_replies_distribution.png")
    c2 = plot_temporal_trends(df, temporal, "outputs/charts/temporal_activity_trends.png")
    c3 = plot_text_analysis(text_data, "outputs/charts/top_keyword_frequency.png")
    c4 = plot_benchmark_results(benchmarks, "outputs/charts/scalability_benchmarks.png")
    print(f"  --> Chart 1: {c1}")
    print(f"  --> Chart 2: {c2}")
    print(f"  --> Chart 3: {c3}")
    print(f"  --> Chart 4: {c4}")

    # 7. Summary JSON & Markdown Report Generation
    print("\n[Step 7/7] Compiling JSON metrics and Markdown report...")
    summary_metrics = {
        "inspection": inspection,
        "statistics": stats,
        "temporal": temporal,
        "text": text_data,
    }
    j1 = save_json_metrics(summary_metrics, "outputs/summary_metrics.json")
    j2 = save_json_metrics(benchmarks, "outputs/benchmark_results.json")
    c_bm = save_csv_benchmarks(benchmarks, "outputs/benchmark_results.csv")
    rep = generate_markdown_report(
        inspection=inspection,
        statistics=stats,
        temporal=temporal,
        text_data=text_data,
        benchmarks=benchmarks,
        raw_csv_path=file_path,
        output_path="report/Project_Report.md",
        df=df,
    )
    print(f"  --> Saved Metrics JSON: {j1}")
    print(f"  --> Saved Benchmarks JSON: {j2}")
    print(f"  --> Saved Benchmarks CSV: {c_bm}")
    print(f"  --> Generated Project Report: {rep}")

    print("\n" + "=" * 75)
    print("   PIPELINE EXECUTION COMPLETED SUCCESSFULLY!   ")
    print("=" * 75)


if __name__ == "__main__":
    main()

