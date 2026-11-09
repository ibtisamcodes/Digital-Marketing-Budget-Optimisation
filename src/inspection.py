"""
Dataset Inspection Module for YouTube Comment Data.
Audits rows, columns, data types, missing values, and duplicate rows.
"""

from typing import Any
import pandas as pd


def inspect_dataset(df: pd.DataFrame) -> dict[str, Any]:
    """
    Performs comprehensive structural inspection of the YouTube comments dataset.
    """
    total_rows, total_cols = df.shape
    columns = list(df.columns)

    # Column-level data types and null audits
    column_info = {}
    for col in columns:
        null_count = int(df[col].isnull().sum())
        null_pct = float((null_count / total_rows) * 100) if total_rows > 0 else 0.0
        column_info[col] = {
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notnull().sum()),
            "null_count": null_count,
            "null_pct": round(null_pct, 3),
            "unique_values": int(df[col].nunique()),
        }

    # Duplicate audits
    full_duplicate_rows = int(df.duplicated().sum())
    duplicate_comments_text = int(df.duplicated(subset=["comment"]).sum()) if "comment" in df.columns else 0
    distinct_repeated_comments = int((df["comment"].value_counts() > 1).sum()) if "comment" in df.columns else 0
    duplicate_authors = int(df.duplicated(subset=["author"]).sum()) if "author" in df.columns else 0

    memory_bytes = int(df.memory_usage(deep=True).sum())
    memory_mb = round(memory_bytes / (1024 * 1024), 3)

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "column_names": columns,
        "column_inspection": column_info,
        "full_duplicate_rows": full_duplicate_rows,
        "duplicate_comments_text": duplicate_comments_text,
        "distinct_repeated_comments": distinct_repeated_comments,
        "duplicate_authors": duplicate_authors,
        "memory_bytes": memory_bytes,
        "memory_mb": memory_mb,
    }

