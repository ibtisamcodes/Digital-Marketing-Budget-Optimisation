"""
Test Suite for Project A: YouTube Comment Scraper & Data Cleaning.
Tests loading, inspection, cleaning, statistics, temporal/lexical analysis,
sentiment classification, and scraper URL parsing.
"""

import io
import pytest
import numpy as np
import pandas as pd

from src.cleaner import clean_dataset
from src.statistics import calculate_descriptive_statistics, compute_gini
from src.text_temporal import analyze_temporal
from src.sentiment_engine import (
    analyze_youtube_sentiment, compute_comment_polarity, classify_sentiment, clean_comment_text
)
from src.youtube_scraper import extract_video_id, get_api_status
from src.dataset_manager import validate_youtube_dataset

@pytest.fixture
def sample_youtube_df():
    return pd.DataFrame([
        {
            'type': 'comment',
            'author': '@ViewerOne',
            'comment': 'Amazing video! Loved the background score and cinematography ❤️',
            'likes': 150,
            'reply_count': 12,
            'published_at': '2025-04-10T14:30:00Z',
            'video_name': 'Test Video'
        },
        {
            'type': 'comment',
            'author': '@ViewerTwo',
            'comment': 'Terrible editing and worst audio sync ever.',
            'likes': 2,
            'reply_count': 0,
            'published_at': '2025-04-11T09:15:00Z',
            'video_name': 'Test Video'
        },
        {
            'type': 'comment',
            'author': '@ViewerThree',
            'comment': 'Standard content. Nothing extraordinary.',
            'likes': 0,
            'reply_count': 0,
            'published_at': '2025-04-12T18:00:00Z',
            'video_name': 'Test Video'
        },
        {
            # Exact duplicate of ViewerThree to test deduplication
            'type': 'comment',
            'author': '@ViewerThree',
            'comment': 'Standard content. Nothing extraordinary.',
            'likes': 0,
            'reply_count': 0,
            'published_at': '2025-04-12T18:00:00Z',
            'video_name': 'Test Video'
        }
    ])

def test_youtube_schema_validation(sample_youtube_df):
    is_valid, issues, meta = validate_youtube_dataset(sample_youtube_df)
    assert is_valid is True
    assert meta['total_rows'] == 4
    assert meta['has_likes'] is True
    assert meta['has_replies'] is True

def test_youtube_cleaning_and_deduplication(sample_youtube_df):
    clean_df, metrics = clean_dataset(sample_youtube_df)
    assert metrics['initial_rows'] == 4
    assert metrics['final_rows'] == 3
    assert metrics['dropped_duplicates'] == 1
    assert len(clean_df) == 3

def test_descriptive_statistics(sample_youtube_df):
    stats = calculate_descriptive_statistics(sample_youtube_df)
    assert 'likes' in stats
    assert stats['likes']['sum'] == 152
    assert stats['likes']['max'] == 150
    assert 0.0 <= stats['likes']['gini_coefficient'] <= 1.0

def test_temporal_and_text_analysis(sample_youtube_df):
    temp = analyze_temporal(sample_youtube_df)
    assert 'yearly_distribution' in temp
    assert 'day_of_week_distribution' in temp

def test_youtube_sentiment_classification(sample_youtube_df):
    sent_df, summary = analyze_youtube_sentiment(sample_youtube_df, comment_col='comment')
    assert summary['total_comments'] == 4
    assert summary['positive_count'] >= 1
    assert summary['negative_count'] >= 1
    assert summary['neutral_count'] >= 1
    assert np.isclose(summary['positive_pct'] + summary['neutral_pct'] + summary['negative_pct'], 100.0)

def test_sentiment_handles_empty_input():
    empty_df = pd.DataFrame({'comment': ['', None, '   ']})
    sent_df, summary = analyze_youtube_sentiment(empty_df, comment_col='comment')
    assert summary['total_comments'] == 3
    assert summary['neutral_count'] == 3

def test_scraper_url_and_id_extraction():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("invalid-id") is None

def test_scraper_api_status_check():
    stat = get_api_status()
    assert isinstance(stat['configured'], bool)
    assert "status_label" in stat
