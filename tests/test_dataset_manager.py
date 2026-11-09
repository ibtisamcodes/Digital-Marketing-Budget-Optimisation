"""
Test Suite for Central Dataset Management System.
Tests CSV and Excel ingestion, invalid file handling, schema validation,
and bundled sample provisioning without mandatory large datasets.
"""

import io
import pytest
import pandas as pd

from src.dataset_manager import (
    load_file_to_dataframe, validate_youtube_dataset, validate_advertising_dataset,
    get_bundled_youtube_sample, get_bundled_advertising_sample
)

def test_load_csv_from_buffer():
    csv_bytes = b"comment,likes,reply_count\nGreat song,100,5\nNice beat,50,2\n"
    buffer = io.BytesIO(csv_bytes)
    setattr(buffer, 'name', 'test.csv')
    df, err = load_file_to_dataframe(buffer)
    assert err is None
    assert len(df) == 2
    assert 'comment' in df.columns

def test_load_excel_from_buffer():
    df_orig = pd.DataFrame({'platform': ['Google', 'Meta'], 'spend': [500.0, 300.0]})
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
        df_orig.to_excel(writer, index=False)
    excel_buf.seek(0)
    setattr(excel_buf, 'name', 'test.xlsx')
    
    df, err = load_file_to_dataframe(excel_buf)
    assert err is None
    assert len(df) == 2
    assert 'platform' in df.columns

def test_invalid_empty_file():
    buf = io.BytesIO(b"")
    setattr(buf, 'name', 'empty.csv')
    df, err = load_file_to_dataframe(buf)
    assert df is None
    assert "error" in err.lower() or "no rows" in err.lower()

def test_bundled_samples_available_without_large_datasets():
    yt_sample = get_bundled_youtube_sample()
    assert yt_sample is not None
    assert len(yt_sample) > 0
    assert len(yt_sample) < 5000  # Not a massive 10M file
    
    ad_sample = get_bundled_advertising_sample()
    assert ad_sample is not None
    assert len(ad_sample) > 0
    assert len(ad_sample) <= 1000  # Lightweight sample

