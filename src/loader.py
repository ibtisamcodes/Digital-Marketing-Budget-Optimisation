"""
Data Loader Module for YouTube Comment Scraper Analytics.
Discovers and loads the target CSV dataset automatically from data/raw/.
"""

import glob
import os
from pathlib import Path
import pandas as pd


def find_target_csv(
    data_dir: str = "data/raw",
    prefix: str = "high-heels-te-nachche-video-song-ki-ka-meet-bros-",
) -> Path:
    """
    Automatically search for the CSV file starting with the specified prefix
    inside the raw data directory. Returns the most recent matching file path.
    """
    raw_path = Path(data_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {data_dir}")

    pattern = str(raw_path / f"{prefix}*.csv")
    matches = glob.glob(pattern)

    if not matches:
        # Fall back to any CSV if specific prefix not found
        all_csvs = glob.glob(str(raw_path / "*.csv"))
        if not all_csvs:
            raise FileNotFoundError(
                f"No CSV files found in {data_dir} matching prefix '{prefix}'"
            )
        matches = all_csvs

    # Pick the latest matching file by modification time
    latest_file = max(matches, key=os.path.getmtime)
    return Path(latest_file)


def load_dataset(
    file_path: Path | str | None = None,
    prefer_processed: bool = True,
) -> tuple[pd.DataFrame, Path]:
    """
    Loads the YouTube comments CSV into a pandas DataFrame without mutating the file.
    Prefers data/processed/cleaned_comments.csv if present, falling back to data/raw/.
    Returns a tuple of (DataFrame, resolved_file_path).
    """
    if file_path is None:
        processed_path = Path("data/processed/cleaned_comments.csv")
        if prefer_processed and processed_path.is_file():
            file_path = processed_path
        else:
            file_path = find_target_csv()
    else:
        file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"Target dataset file not found: {file_path}")

    df = pd.read_csv(file_path, encoding="utf-8-sig")
    return df, file_path

