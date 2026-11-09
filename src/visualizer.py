"""
Visualization Module for YouTube Comment Analytics.
Generates publication-quality charts saved under outputs/charts/.
"""

import os
import tempfile
from pathlib import Path
from typing import Any

# Configure writable matplotlib cache before importing matplotlib
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Set styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.autolayout": False,
})


def plot_engagement_distribution(
    df: pd.DataFrame,
    output_path: str | Path = "outputs/charts/likes_replies_distribution.png",
) -> Path:
    """
    Generates distribution and correlation charts for likes and reply_count.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel 1: Log-transformed distributions
    likes = pd.to_numeric(df["likes"], errors="coerce").fillna(0)
    replies = pd.to_numeric(df["reply_count"], errors="coerce").fillna(0)

    # Use log1p to handle zeros gracefully
    log_likes = np.log1p(likes)
    log_replies = np.log1p(replies)

    sns.kdeplot(log_likes, ax=axes[0], fill=True, color="#1f77b4", label="Likes (log1p)", alpha=0.5, linewidth=2)
    sns.kdeplot(log_replies, ax=axes[0], fill=True, color="#ff7f0e", label="Replies (log1p)", alpha=0.5, linewidth=2)
    axes[0].set_title("Engagement Metric Density (Log1p Transformed)")
    axes[0].set_xlabel("log(1 + Count)")
    axes[0].set_ylabel("Kernel Density")
    axes[0].legend(frameon=True)
    axes[0].grid(True, linestyle="--", alpha=0.6)

    # Panel 2: Log-log scatter plot of Likes vs Replies
    scatter = axes[1].scatter(
        likes + 0.5,
        replies + 0.5,
        alpha=0.6,
        color="#2ca02c",
        edgecolors="none",
        s=30,
    )
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_title("Likes vs. Reply Count Correlation (Log Scale)")
    axes[1].set_xlabel("Likes + 0.5 (Log Scale)")
    axes[1].set_ylabel("Reply Count + 0.5 (Log Scale)")
    axes[1].grid(True, which="both", linestyle="--", alpha=0.5)

    # Annotate top outlier
    max_likes_idx = likes.idxmax()
    if pd.notnull(max_likes_idx):
        top_row = df.loc[max_likes_idx]
        axes[1].annotate(
            f"Top Liked: {int(top_row['likes'])} likes\n({top_row['author']})",
            xy=(top_row["likes"] + 0.5, top_row["reply_count"] + 0.5),
            xytext=(top_row["likes"] * 0.15, top_row["reply_count"] * 1.5),
            arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1.5, headwidth=6),
            fontsize=8,
            fontweight="semibold",
            bbox=dict(boxstyle="round,pad=0.3", fc="#fffae6", ec="#d62728", lw=1),
        )

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_temporal_trends(
    df: pd.DataFrame,
    temporal_data: dict[str, Any],
    output_path: str | Path = "outputs/charts/temporal_activity_trends.png",
) -> Path:
    """
    Generates temporal trends comparing yearly frequency and cumulative volume.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel 1: Yearly comment volume
    yearly = temporal_data.get("yearly_distribution", {})
    years = list(yearly.keys())
    counts = list(yearly.values())

    bars = axes[0].bar(years, counts, color="#4a90e2", edgecolor="#2c3e50", width=0.65)
    axes[0].set_title("Annual Comment Volume (2016 - 2026)")
    axes[0].set_xlabel("Year")
    axes[0].set_ylabel("Comment Count")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].grid(axis="y", linestyle="--", alpha=0.6)

    # Highlight resurgence bars
    for bar, yr in zip(bars, years):
        if yr in ["2025", "2026"]:
            bar.set_color("#e74c3c")
        h = bar.get_height()
        if h > 0:
            axes[0].text(bar.get_x() + bar.get_width() / 2, h + 8, str(h), ha="center", va="bottom", fontsize=8)

    # Panel 2: Cumulative trajectory over time
    dt_series = pd.to_datetime(df["published_at"], errors="coerce", utc=True).dropna().sort_values()
    cum_df = pd.DataFrame({"timestamp": dt_series, "count": np.arange(1, len(dt_series) + 1)})

    axes[1].plot(cum_df["timestamp"], cum_df["count"], color="#8e44ad", linewidth=2.5)
    axes[1].fill_between(cum_df["timestamp"], cum_df["count"], color="#8e44ad", alpha=0.15)
    axes[1].set_title("Cumulative Comment Growth Trajectory")
    axes[1].set_xlabel("Publication Date")
    axes[1].set_ylabel("Cumulative Comments")
    axes[1].grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_text_analysis(
    text_data: dict[str, Any],
    output_path: str | Path = "outputs/charts/top_keyword_frequency.png",
) -> Path:
    """
    Generates horizontal bar charts for top keywords and thematic categories.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel 1: Top 15 keywords
    top_kw = text_data.get("top_keywords", [])[:15]
    if top_kw:
        words = [item["keyword"] for item in reversed(top_kw)]
        freqs = [item["count"] for item in reversed(top_kw)]
        axes[0].barh(words, freqs, color="#16a085", edgecolor="#0e6655", height=0.65)
        axes[0].set_title("Top 15 Recurring Vocabulary Terms")
        axes[0].set_xlabel("Frequency Count")
        for i, val in enumerate(freqs):
            axes[0].text(val + 0.5, i, str(val), va="center", fontsize=8)
    axes[0].grid(axis="x", linestyle="--", alpha=0.6)

    # Panel 2: Thematic Entity Mentions
    thematics = text_data.get("thematic_mentions", {})
    if thematics:
        labels = [k.replace("_", " ").title() for k in thematics.keys()]
        values = list(thematics.values())
        axes[1].barh(labels, values, color="#d35400", edgecolor="#a04000", height=0.6)
        axes[1].set_title("Thematic & Artist Discussion Focus")
        axes[1].set_xlabel("Matching Comments")
        for i, val in enumerate(values):
            axes[1].text(val + 1, i, str(val), va="center", fontsize=8)
    axes[1].grid(axis="x", linestyle="--", alpha=0.6)

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_benchmark_results(
    benchmark_data: dict[str, Any],
    output_path: str | Path = "outputs/charts/scalability_benchmarks.png",
) -> Path:
    """
    Generates scaling plots showing execution runtime and memory usage across workloads.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    workloads = benchmark_data.get("workloads", [])
    if not workloads:
        return out

    labels = [w["scale_label"] for w in workloads]
    rows = [w["row_count"] for w in workloads]
    runtimes = [w["mean_runtime_seconds"] for w in workloads]
    memories = [w["peak_memory_mb"] for w in workloads]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.0))

    # Panel 1: Execution Runtime
    bars1 = axes[0].bar(labels, runtimes, color="#2980b9", edgecolor="#1a5276", width=0.55)
    axes[0].set_title("Pipeline Execution Runtime Scaling (Mean of 3 Runs)")
    axes[0].set_xlabel("Workload Scale")
    axes[0].set_ylabel("Runtime (Seconds)")
    axes[0].grid(axis="y", linestyle="--", alpha=0.6)
    for bar, val in zip(bars1, runtimes):
        axes[0].text(bar.get_x() + bar.get_width() / 2, val + (max(runtimes) * 0.02), f"{val:.4f}s", ha="center", fontsize=8, fontweight="bold")

    # Panel 2: Peak Memory Usage
    bars2 = axes[1].bar(labels, memories, color="#c0392b", edgecolor="#78281f", width=0.55)
    axes[1].set_title("Peak Memory Allocation Scaling (tracemalloc)")
    axes[1].set_xlabel("Workload Scale")
    axes[1].set_ylabel("Peak Memory (MB)")
    axes[1].grid(axis="y", linestyle="--", alpha=0.6)
    for bar, val in zip(bars2, memories):
        axes[1].text(bar.get_x() + bar.get_width() / 2, val + (max(memories) * 0.02), f"{val:.2f} MB", ha="center", fontsize=8, fontweight="bold")

    plt.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out

