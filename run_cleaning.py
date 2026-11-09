"""
Standalone Execution Script for DS391 YouTube Comment Data Cleaning.
Loads raw data from data/raw/, applies robust cleaning, and saves to
data/processed/cleaned_comments.csv while displaying audit metrics.
"""

import io
import sys

# Force UTF-8 stdout for Windows console emoji/unicode support
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.cleaner import main

if __name__ == "__main__":
    main()

