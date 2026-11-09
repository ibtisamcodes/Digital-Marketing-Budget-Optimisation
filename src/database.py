"""
Database Management & SQLite Analytical Engine.
Provides schema definitions, automated ingestion, analytical SQL views,
and export utilities for academic submission and reporting.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join('data', 'marketing_intelligence.db')

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Creates directory if needed and opens an SQLite connection."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_database(db_path: str = DB_PATH):
    """
    Initializes database tables, indices, and analytical views.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    # 1. Advertising campaigns table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS advertising_campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        campaign TEXT,
        platform TEXT,
        impressions INTEGER,
        clicks INTEGER,
        spend REAL,
        conversions INTEGER,
        revenue REAL,
        age INTEGER,
        gender TEXT,
        city TEXT,
        device TEXT
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ad_platform ON advertising_campaigns(platform);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ad_campaign ON advertising_campaigns(campaign);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ad_date ON advertising_campaigns(date);")

    # 2. YouTube comments table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS youtube_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_name TEXT,
        author TEXT,
        comment TEXT,
        likes INTEGER,
        published_at TEXT,
        reply_count INTEGER,
        sentiment TEXT,
        polarity REAL
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_yt_video ON youtube_comments(video_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_yt_sentiment ON youtube_comments(sentiment);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_yt_author ON youtube_comments(author);")

    # 3. Budget optimizations table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS budget_optimizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        strategy TEXT,
        total_budget REAL,
        platform TEXT,
        allocation_pct REAL,
        allocated_amount REAL,
        expected_revenue REAL,
        expected_conversions INTEGER
    );
    """)

    # 4. Benchmark records table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS benchmark_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        workload_target INTEGER,
        actual_records INTEGER,
        engine TEXT,
        execution_time_sec REAL,
        memory_mb REAL,
        status TEXT,
        throughput_rec_sec REAL,
        notes TEXT
    );
    """)

    # 5. Analytical Views with zero-denominator safety
    cur.execute("DROP VIEW IF EXISTS view_platform_kpis;")
    cur.execute("""
    CREATE VIEW view_platform_kpis AS
    SELECT 
        platform,
        COUNT(*) AS record_count,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        ROUND(SUM(spend), 2) AS total_spend,
        SUM(conversions) AS total_conversions,
        ROUND(SUM(revenue), 2) AS total_revenue,
        ROUND(SUM(revenue) - SUM(spend), 2) AS total_profit,
        ROUND(CASE WHEN SUM(impressions) > 0 THEN (SUM(clicks) * 100.0) / SUM(impressions) ELSE 0.0 END, 2) AS CTR,
        ROUND(CASE WHEN SUM(clicks) > 0 THEN SUM(spend) / SUM(clicks) ELSE 0.0 END, 2) AS CPC,
        ROUND(CASE WHEN SUM(conversions) > 0 THEN SUM(spend) / SUM(conversions) ELSE 0.0 END, 2) AS CPA,
        ROUND(CASE WHEN SUM(clicks) > 0 THEN (SUM(conversions) * 100.0) / SUM(clicks) ELSE 0.0 END, 2) AS CVR,
        ROUND(CASE WHEN SUM(spend) > 0 THEN SUM(revenue) / SUM(spend) ELSE 0.0 END, 2) AS ROAS
    FROM advertising_campaigns
    GROUP BY platform
    ORDER BY ROAS DESC;
    """)

    cur.execute("DROP VIEW IF EXISTS view_youtube_engagement_summary;")
    cur.execute("""
    CREATE VIEW view_youtube_engagement_summary AS
    SELECT 
        video_name,
        COUNT(*) AS total_comments,
        SUM(likes) AS total_likes,
        ROUND(AVG(likes), 2) AS avg_likes,
        MAX(likes) AS max_likes,
        SUM(reply_count) AS total_replies,
        ROUND(AVG(reply_count), 2) AS avg_replies,
        SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) AS positive_comments,
        SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) AS neutral_comments,
        SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative_comments
    FROM youtube_comments
    GROUP BY video_name;
    """)

    cur.execute("DROP VIEW IF EXISTS view_campaign_performance;")
    cur.execute("""
    CREATE VIEW view_campaign_performance AS
    SELECT 
        campaign,
        COUNT(*) AS record_count,
        SUM(impressions) AS total_impressions,
        SUM(clicks) AS total_clicks,
        ROUND(SUM(spend), 2) AS total_spend,
        SUM(conversions) AS total_conversions,
        ROUND(SUM(revenue), 2) AS total_revenue,
        ROUND(SUM(revenue) - SUM(spend), 2) AS total_profit,
        ROUND(CASE WHEN SUM(spend) > 0 THEN SUM(revenue) / SUM(spend) ELSE 0.0 END, 2) AS ROAS
    FROM advertising_campaigns
    GROUP BY campaign
    ORDER BY total_revenue DESC;
    """)

    conn.commit()
    conn.close()

def import_advertising_dataframe(df: pd.DataFrame, db_path: str = DB_PATH, if_exists: str = 'replace'):
    """Populates advertising_campaigns table from DataFrame."""
    conn = get_connection(db_path)
    df.to_sql('advertising_campaigns', conn, if_exists=if_exists, index=False)
    conn.commit()
    conn.close()

def import_youtube_dataframe(df: pd.DataFrame, db_path: str = DB_PATH, if_exists: str = 'replace'):
    """Populates youtube_comments table from DataFrame."""
    conn = get_connection(db_path)
    data = df.copy()
    data.to_sql('youtube_comments', conn, if_exists=if_exists, index=False)
    conn.commit()
    conn.close()

def query_view(view_name: str, db_path: str = DB_PATH) -> pd.DataFrame:
    """Executes SELECT query on analytical view."""
    conn = get_connection(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {view_name}", conn)
    conn.close()
    return df

def get_database_status(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Returns database size and record counts for all core tables."""
    if not os.path.exists(db_path):
        return {'exists': False, 'size_kb': 0, 'tables': {}}
        
    conn = get_connection(db_path)
    cur = conn.cursor()
    tables = ['advertising_campaigns', 'youtube_comments', 'budget_optimizations', 'benchmark_records']
    counts = {}
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
        except Exception:
            counts[t] = 0
            
    conn.close()
    size_kb = os.path.getsize(db_path) / 1024.0
    return {
        'exists': True,
        'size_kb': round(size_kb, 2),
        'tables': counts
    }
