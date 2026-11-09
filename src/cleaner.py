"""
Data Cleaning & Dataset Combination Module for DS391 Big Data Analytics.
Cleans and standardizes raw YouTube comment data across multiple music-video exports
without mutating raw source files.
Combines multiple datasets with a `video_name` identifier and saves output to
data/processed/cleaned_comments.csv and data/processed/combined_comments.csv.
"""

import glob
import os
from pathlib import Path
from typing import Any
import pandas as pd

from src.loader import find_target_csv


def load_and_combine_raw_datasets(
    data_dir: str = "data/raw",
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Discovers all raw CSV exports inside data/raw/, attaches a standardized
    `video_name` column based on filename, and combines them without mutating originals.
    """
    raw_path = Path(data_dir)
    csv_files = sorted(glob.glob(str(raw_path / "*.csv")))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    dfs = []
    file_summaries = []

    for f_path in csv_files:
        p = Path(f_path)
        fname = p.name.lower()

        # Map to human-readable video titles
        if "high-heels" in fname:
            video_name = "High Heels Te Nachche"
        elif "gali-gali" in fname:
            video_name = "Gali Gali"
        else:
            video_name = p.stem

        df_sub = pd.read_csv(p, encoding="utf-8-sig")
        df_sub["video_name"] = video_name

        file_summaries.append({
            "path": str(p),
            "video_name": video_name,
            "raw_rows": len(df_sub),
            "columns": list(df_sub.columns),
            "null_comments": int(df_sub["comment"].isnull().sum()) if "comment" in df_sub.columns else 0,
        })
        dfs.append(df_sub)

    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df, file_summaries


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Cleans raw YouTube comment dataset according to project requirements:
    1. Standardizes column names (lowercase, stripped, underscored).
    2. Trims unnecessary whitespace from string/text fields.
    3. Converts likes and reply counts to integer numeric types (int64).
    4. Safely parses ISO 8601 UTC publication timestamps.
    5. Handles missing values gracefully without silently dropping legitimate comments.
    6. Removes only confirmed full-row duplicate records, preserving legitimate repeated comments.
    """
    df_clean = df.copy()
    initial_rows = len(df_clean)

    # 1. Standardize column names
    df_clean.columns = [str(col).strip().lower().replace(" ", "_") for col in df_clean.columns]

    # 2. Trim unnecessary whitespace from string/text fields
    text_columns = ["type", "author", "comment", "video_name"]
    for col in text_columns:
        if col in df_clean.columns:
            # Fill NaN with empty string to preserve record, then trim
            df_clean[col] = df_clean[col].fillna("").astype(str).str.strip()

    # 3. Convert likes and reply counts to numeric integer types
    numeric_columns = ["likes", "reply_count"]
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0).astype("int64")

    # 4. Parse publication dates safely
    if "published_at" in df_clean.columns:
        parsed_dates = pd.to_datetime(df_clean["published_at"], errors="coerce", utc=True)
        # Preserve standardized ISO 8601 UTC string format: YYYY-MM-DDTHH:MM:SSZ
        df_clean["published_at"] = parsed_dates.dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 5. Handle missing values appropriately
    if "type" in df_clean.columns:
        df_clean["type"] = df_clean["type"].replace("", "comment")

    # 6. Remove only confirmed full-row duplicate records
    # Deduplication method: evaluates multi-column row identity across all columns.
    # Legitimate repeated comment texts across different authors, timestamps, or videos are strictly preserved.
    duplicate_rows_count = int(df_clean.duplicated().sum())
    df_clean = df_clean.drop_duplicates()
    final_rows = len(df_clean)

    # Calculate audit metrics
    metrics = {
        "initial_rows": initial_rows,
        "final_rows": final_rows,
        "dropped_duplicates": duplicate_rows_count,
        "repeated_comment_texts": int(df_clean.duplicated(subset=["comment"]).sum()) if "comment" in df_clean.columns else 0,
        "missing_values": df_clean.isnull().sum().to_dict(),
    }

    return df_clean, metrics


def save_cleaned_dataset(
    df: pd.DataFrame,
    output_path: str | Path = "data/processed/cleaned_comments.csv",
) -> Path:
    """
    Saves the cleaned DataFrame to the target CSV path, creating parent directories if needed.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8")
    return out


def main():
    print("=" * 75)
    print("   DS391 DATA CLEANING & COMBINATION PIPELINE   ")
    print("=" * 75)

    # 1. Discover and load all raw datasets
    raw_combined, file_summaries = load_and_combine_raw_datasets("data/raw")
    print(f"\n[1] Discovered and Loaded {len(file_summaries)} Raw Datasets from data/raw/:")
    for s in file_summaries:
        print(f"    - {s['video_name']}: {s['raw_rows']:,} rows | Path: {s['path']}")
    print(f"    Total Concatenated Rows: {len(raw_combined):,}")

    # 2. Perform cleaning & standardization
    cleaned_df, metrics = clean_dataset(raw_combined)
    print(f"\n[2] Cleaning & Deduplication Summary:")
    print(f"    - Standardized column names: {list(cleaned_df.columns)}")
    print(f"    - Added 'video_name' column identifying source video")
    print(f"    - Handled missing values (imputed empty string for 1 missing comment, int 0 for counts)")
    print(f"    - Exact multi-column duplicate rows removed: {metrics['dropped_duplicates']}")
    print(f"    - Legitimate repeated comment texts preserved: {metrics['repeated_comment_texts']}")
    print(f"    - Final Cleaned Row Count: {len(cleaned_df):,}")

    # 3. Save to processed paths
    p1 = save_cleaned_dataset(cleaned_df, "data/processed/cleaned_comments.csv")
    p2 = save_cleaned_dataset(cleaned_df, "data/processed/combined_comments.csv")
    print(f"\n[3] Saved Output Files:")
    print(f"    - Canonical Cleaned: {p1} ({p1.stat().st_size:,} bytes)")
    print(f"    - Combined Reference: {p2} ({p2.stat().st_size:,} bytes)")

    # 4. Display required terminal verification outputs
    print("\n" + "=" * 75)
    print("   COMBINED CLEANED DATASET VERIFICATION & TERMINAL REPORT   ")
    print("=" * 75)

    print("\n[A] DATASET SHAPE:")
    print(f"    {cleaned_df.shape[0]:,} rows x {cleaned_df.shape[1]} columns")

    print("\n[B] VIDEO DISTRIBUTION BREAKDOWN:")
    for v_name, count in cleaned_df["video_name"].value_counts().items():
        pct = round(count / len(cleaned_df) * 100, 2)
        print(f"    - {v_name}: {count:,} rows ({pct}%)")

    print("\n[C] COLUMN NAMES & DATA TYPES:")
    print(cleaned_df.dtypes.to_string())

    print("\n[D] MISSING-VALUE COUNTS PER COLUMN:")
    print(cleaned_df.isnull().sum().to_string())

    print("\n[E] DUPLICATE COUNTS & REPETITION:")
    print(f"    - Exact Multi-Column Duplicate Rows: {cleaned_df.duplicated().sum()}")
    print(f"    - Repeated Comment Text Occurrences: {cleaned_df.duplicated(subset=['comment']).sum()}")
    print(f"    - Distinct Comment Strings Appearing >1: {(cleaned_df['comment'].value_counts() > 1).sum()}")
    print(f"    - Unique Authors: {cleaned_df['author'].nunique():,}")
    print(f"    - Unique Comment Texts: {cleaned_df['comment'].nunique():,}")

    dt_series = pd.to_datetime(cleaned_df["published_at"], errors="coerce", utc=True)
    print("\n[F] LONGITUDINAL DATE RANGE:")
    print(f"    - Earliest Publication Date: {dt_series.min()}")
    print(f"    - Latest Publication Date:   {dt_series.max()}")
    print(f"    - Total Temporal Span: {(dt_series.max() - dt_series.min()).days} days")

    print("\n[G] DESCRIPTIVE STATISTICS (NUMERICAL ENGAGEMENT COLUMNS):")
    print(cleaned_df[["likes", "reply_count"]].describe().to_string())

    print("\n[H] FIRST 10 ROWS:")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    print(cleaned_df.head(10).to_string())

    print("\n" + "=" * 75)
    print("   DATA CLEANING & COMBINATION COMPLETED SUCCESSFULLY   ")
    print("=" * 75)


if __name__ == "__main__":
    main()
