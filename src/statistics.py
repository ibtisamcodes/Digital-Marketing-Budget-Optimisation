"""
Descriptive Statistics Module for YouTube Comment Engagement.
Computes parametric and non-parametric statistics for likes and reply_count.
"""

import math
from typing import Any
import numpy as np
import pandas as pd


def compute_gini(values: np.ndarray) -> float:
    """Computes the Gini coefficient of inequality for an array of values."""
    if len(values) == 0:
        return 0.0
    v = np.sort(np.asarray(values, dtype=float))
    n = len(v)
    if np.sum(v) == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float((2.0 * np.sum(index * v) - (n + 1) * np.sum(v)) / (n * np.sum(v)))


def calculate_descriptive_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Computes rigorous descriptive statistics for 'likes' and 'reply_count'.
    """
    stats_result: dict[str, Any] = {}

    for metric in ["likes", "reply_count"]:
        if metric not in df.columns:
            continue

        series = pd.to_numeric(df[metric], errors="coerce").fillna(0)
        q25 = float(series.quantile(0.25))
        median = float(series.median())
        q75 = float(series.quantile(0.75))
        iqr = float(q75 - q25)
        total_sum = float(series.sum())
        total_count = len(series)
        zero_count = int((series == 0).sum())
        zero_pct = round((zero_count / total_count) * 100, 2) if total_count > 0 else 0.0

        # Percentile concentrations
        p90 = float(series.quantile(0.90))
        p95 = float(series.quantile(0.95))
        p99 = float(series.quantile(0.99))

        # Top 1% share of total sum
        top_1_pct_count = max(1, int(np.ceil(total_count * 0.01)))
        top_1_pct_sum = float(series.nlargest(top_1_pct_count).sum())
        top_1_pct_share = round((top_1_pct_sum / total_sum * 100), 2) if total_sum > 0 else 0.0

        stats_result[metric] = {
            "count": int(total_count),
            "sum": total_sum,
            "mean": round(float(series.mean()), 3),
            "std": round(float(series.std()), 3),
            "variance": round(float(series.var()), 3),
            "min": float(series.min()),
            "q25": q25,
            "median": median,
            "q75": q75,
            "max": float(series.max()),
            "iqr": iqr,
            "skewness": round(float(series.skew()), 3),
            "kurtosis": round(float(series.kurtosis()), 3),
            "zero_count": zero_count,
            "zero_pct": zero_pct,
            "p90": p90,
            "p95": p95,
            "p99": p99,
            "top_1_pct_share": top_1_pct_share,
            "gini_coefficient": round(compute_gini(series.to_numpy()), 4),
        }

    # Extract Top 5 engaged comments safely
    avail_liked_cols = [c for c in ["author", "likes", "reply_count", "published_at", "comment"] if c in df.columns]
    top_liked = (
        df.sort_values(by="likes", ascending=False)
        .head(5)[avail_liked_cols]
        .to_dict(orient="records")
    ) if "likes" in df.columns and avail_liked_cols else []
    for record in top_liked:
        # truncate text to 150 chars for summary readability
        if "comment" in record:
            record["comment_preview"] = str(record["comment"])[:150]

    avail_replied_cols = [c for c in ["author", "reply_count", "likes", "published_at", "comment"] if c in df.columns]
    top_replied = (
        df.sort_values(by="reply_count", ascending=False)
        .head(5)[avail_replied_cols]
        .to_dict(orient="records")
    ) if "reply_count" in df.columns and avail_replied_cols else []
    for record in top_replied:
        if "comment" in record:
            record["comment_preview"] = str(record["comment"])[:150]

    stats_result["top_5_liked_comments"] = top_liked
    stats_result["top_5_replied_comments"] = top_replied

    # Correlation between likes and replies (Pearson and Spearman rank via ranking)
    if "likes" in df.columns and "reply_count" in df.columns:
        likes_series = pd.to_numeric(df["likes"], errors="coerce").fillna(0)
        replies_series = pd.to_numeric(df["reply_count"], errors="coerce").fillna(0)
        n = len(df)
        df_corr = max(1, n - 2)

        r_pearson = float(likes_series.corr(replies_series, method="pearson"))
        stats_result["pearson_correlation"] = round(r_pearson, 4)
        if abs(r_pearson) < 1.0:
            t_pearson = r_pearson * np.sqrt(df_corr / (1.0 - r_pearson**2))
            stats_result["pearson_t_stat"] = round(float(t_pearson), 3)
            stats_result["pearson_p_value"] = "< 0.0001" if abs(t_pearson) > 3.89 else str(round(float(2 * (1 - 0.5 * (1 + math.erf(abs(t_pearson) / np.sqrt(2))))), 4))

        # Spearman is Pearson on ranked data, avoiding optional scipy dependency
        r_spearman = float(likes_series.rank().corr(replies_series.rank()))
        stats_result["spearman_correlation"] = round(r_spearman, 4)
        if abs(r_spearman) < 1.0:
            t_spearman = r_spearman * np.sqrt(df_corr / (1.0 - r_spearman**2))
            stats_result["spearman_t_stat"] = round(float(t_spearman), 3)
            stats_result["spearman_df"] = df_corr
            stats_result["spearman_p_value"] = "< 0.0001" if abs(t_spearman) > 3.89 else str(round(float(2 * (1 - 0.5 * (1 + math.erf(abs(t_spearman) / np.sqrt(2))))), 4))

    return stats_result
