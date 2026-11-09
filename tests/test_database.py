"""
Test Suite for SQLite Database Engine and Analytical Views.
Verifies table schemas, automated ingestion, and view query execution.
"""

import os
import sqlite3
import pandas as pd
import pytest
from src.database import (
    init_database,
    import_advertising_dataframe,
    import_youtube_dataframe,
    query_view,
    get_database_status
)

@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_marketing.db")
    init_database(db_file)
    return db_file

def test_database_tables_and_indices_created(temp_db):
    conn = sqlite3.connect(temp_db)
    cur = conn.cursor()
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert 'advertising_campaigns' in tables
    assert 'youtube_comments' in tables
    assert 'budget_optimizations' in tables
    assert 'benchmark_records' in tables
    conn.close()

def test_advertising_and_youtube_ingestion(temp_db):
    # Test Ad Ingestion
    ad_df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-02'],
        'campaign': ['C1', 'C2'],
        'platform': ['Google', 'Facebook'],
        'impressions': [1000, 2000],
        'clicks': [100, 200],
        'spend': [500.0, 1000.0],
        'conversions': [10, 20],
        'revenue': [2500.0, 4000.0],
        'age': [25, 30],
        'gender': ['Male', 'Female'],
        'city': ['Karachi', 'Lahore'],
        'device': ['Mobile', 'Desktop']
    })
    import_advertising_dataframe(ad_df, temp_db)
    
    # Test YouTube Ingestion
    yt_df = pd.DataFrame({
        'video_name': ['V1', 'V1'],
        'author': ['A1', 'A2'],
        'comment': ['Great video!', 'Needs work'],
        'likes': [15, 2],
        'published_at': ['2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z'],
        'reply_count': [3, 0],
        'sentiment': ['Positive', 'Negative'],
        'polarity': [0.85, -0.40]
    })
    import_youtube_dataframe(yt_df, temp_db)
    
    status = get_database_status(temp_db)
    assert status['tables']['advertising_campaigns'] == 2
    assert status['tables']['youtube_comments'] == 2

def test_analytical_views_execution(temp_db):
    ad_df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-02'],
        'campaign': ['Launch', 'Launch'],
        'platform': ['Google', 'Google'],
        'impressions': [1000, 1000],
        'clicks': [100, 100],
        'spend': [500.0, 500.0],
        'conversions': [10, 10],
        'revenue': [2000.0, 2000.0],
        'age': [25, 30],
        'gender': ['Male', 'Female'],
        'city': ['Karachi', 'Lahore'],
        'device': ['Mobile', 'Desktop']
    })
    import_advertising_dataframe(ad_df, temp_db)
    
    yt_df = pd.DataFrame({
        'video_name': ['MusicVideo', 'MusicVideo'],
        'author': ['User1', 'User2'],
        'comment': ['Awesome', 'Love it'],
        'likes': [10, 20],
        'published_at': ['2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z'],
        'reply_count': [2, 4],
        'sentiment': ['Positive', 'Positive'],
        'polarity': [0.8, 0.9]
    })
    import_youtube_dataframe(yt_df, temp_db)
    
    # Query Platform KPIs View
    v_plat = query_view('view_platform_kpis', temp_db)
    assert not v_plat.empty
    assert 'ROAS' in v_plat.columns
    assert v_plat.loc[v_plat['platform'] == 'Google', 'ROAS'].values[0] == 4.0
    
    # Query YouTube Engagement Summary View
    v_yt = query_view('view_youtube_engagement_summary', temp_db)
    assert not v_yt.empty
    assert v_yt.loc[v_yt['video_name'] == 'MusicVideo', 'total_comments'].values[0] == 2
    assert v_yt.loc[v_yt['video_name'] == 'MusicVideo', 'total_likes'].values[0] == 30

