"""
Page 1: Executive Overview Dashboard.
Displays status of loaded datasets, record counts, schema validation, key metrics,
available processing engines, and quick action shortcuts.
"""

import streamlit as st
import pandas as pd

from src.dataset_manager import get_bundled_youtube_sample, get_bundled_advertising_sample
from src.advertising_analytics import compute_portfolio_macro_summary
from src.sentiment_engine import analyze_youtube_sentiment
from src.bigdata_engine import check_spark_environment

def render_page_overview():
    st.title("Executive Overview & Unified System Status")
    st.markdown("""
    Welcome to the **Unified Marketing Intelligence & Big Data Analytics Platform**.  
    This unified platform integrates **Project A (YouTube Comment Scraper & Data Cleaning)** with **Project B (Digital Advertising Budget Optimizer & Big Data Processing Lab)**.
    """)
    st.divider()
    
    # Dataset Status Cards
    yt_df = st.session_state.get('youtube_clean_df')
    ad_df = st.session_state.get('advertising_df')
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Card 1: YouTube Dataset
    if yt_df is not None and not yt_df.empty:
        col1.metric("YouTube Dataset", f"{len(yt_df):,} Comments", st.session_state.get('active_youtube_name', 'Loaded'))
    else:
        col1.metric("YouTube Dataset", "Not Loaded", "Upload CSV or Load Sample")
        
    # Card 2: Advertising Dataset
    if ad_df is not None and not ad_df.empty:
        col2.metric("Advertising Dataset", f"{len(ad_df):,} Records", st.session_state.get('active_ad_name', 'Loaded'))
    else:
        col2.metric("Advertising Dataset", "Not Loaded", "Upload CSV or Load Sample")
        
    # Card 3: Processing Engines
    spark_ok, _ = check_spark_environment()
    engine_status = "Pandas, MapReduce, Spark" if spark_ok else "Pandas, MapReduce (Spark Diagnostic)"
    col3.metric("Processing Engines", "3 Supported", "Active & Available")
    
    # Card 4: Budget Optimizer Target
    col4.metric("Budget Optimization Target", "Rs. 1,000,000", "Customizable Invariant")
    
    st.divider()
    
    # If neither dataset is loaded, display an informative empty state with quick actions
    if (yt_df is None or yt_df.empty) and (ad_df is None or ad_df.empty):
        st.info("💡 **Getting Started**: No datasets are currently loaded in session memory. You can upload your own CSV/Excel datasets or load bundled real sample datasets below:")
        qcol1, qcol2 = st.columns(2)
        with qcol1:
            if st.button("📥 Load Bundled YouTube Sample (2,349 Comments)", use_container_width=True):
                sample_yt = get_bundled_youtube_sample()
                if sample_yt is not None:
                    st.session_state['youtube_raw_df'] = sample_yt.copy()
                    st.session_state['youtube_clean_df'] = sample_yt.copy()
                    st.session_state['active_youtube_name'] = "Bundled Dual-Video YouTube Comments"
                    st.rerun()
        with qcol2:
            if st.button("📥 Load Bundled Advertising Sample (250 Records)", use_container_width=True):
                sample_ad = get_bundled_advertising_sample()
                if sample_ad is not None:
                    st.session_state['advertising_df'] = sample_ad.copy()
                    st.session_state['active_ad_name'] = "Bundled Multi-Channel Ad Telemetry"
                    st.rerun()
                    
    # Live Key Metric Highlights if data is present
    if (yt_df is not None and not yt_df.empty) or (ad_df is not None and not ad_df.empty):
        st.subheader("Active Key Performance Indicators")
        kcol1, kcol2 = st.columns(2)
        
        with kcol1:
            st.markdown("#### Project A: YouTube Audience Signals")
            if yt_df is not None and not yt_df.empty:
                c_col = 'comment' if 'comment' in yt_df.columns else yt_df.columns[0]
                _, sent_meta = analyze_youtube_sentiment(yt_df, comment_col=c_col)
                likes_sum = int(yt_df['likes'].sum()) if 'likes' in yt_df.columns else 0
                replies_sum = int(yt_df['reply_count'].sum()) if 'reply_count' in yt_df.columns else 0
                
                subcol1, subcol2, subcol3 = st.columns(3)
                subcol1.metric("Positive Sentiment", f"{sent_meta['positive_pct']}%")
                subcol2.metric("Total Thumbs-Up Likes", f"{likes_sum:,}")
                subcol3.metric("Total Thread Replies", f"{replies_sum:,}")
            else:
                st.caption("No YouTube dataset currently active.")
                
        with kcol2:
            st.markdown("#### Project B: Advertising Performance")
            if ad_df is not None and not ad_df.empty:
                ad_macro = compute_portfolio_macro_summary(ad_df)
                asub1, asub2, asub3 = st.columns(3)
                asub1.metric("Macro ROAS", f"{ad_macro['macro_roas']:.2f}x")
                asub2.metric("Total Spend", f"Rs. {ad_macro['total_spend']:,.0f}")
                asub3.metric("Total Conversions", f"{ad_macro['total_conversions']:,}")
            else:
                st.caption("No Advertising dataset currently active.")
                
    st.markdown("### Unified System Architecture & Workflow")
    st.markdown("""
```text
+---------------------------------------------------------------------------------------------------+
|                        UNIFIED MARKETING INTELLIGENCE & BIG DATA PLATFORM                         |
+-------------------------------------------------+-------------------------------------------------+
|   PROJECT A: YOUTUBE COMMENT ANALYTICS & CLEANING|  PROJECT B: ADVERTISING BUDGET OPTIMIZER       |
+-------------------------------------------------+-------------------------------------------------+
| • YouTube Data API v3 Comment Harvester         | • Multi-Channel Paid Telemetry (FB, IG, GG, etc)|
| • Raw CSV / Excel Ingestion & Deduplication     | • Core Marketing KPIs: CTR, CPC, CPA, CVR, ROAS |
| • Descriptive Parametric & Gini Analytics       | • Big Data Engine Lab: Pandas, Chunk, MR, Spark |
| • Rule-Based Lexicon Sentiment Approximation    | • Constrained Solver Allocating Target Budget   |
| • 10-Year Temporal Trends & Word Frequencies    | • Interactive Audience & Demographic Breakdown  |
+-------------------------------------------------+-------------------------------------------------+
                                         \\       /
                                          \\     /
+---------------------------------------------------------------------------------------------------+
|                        CROSS-DOMAIN SYNTHESIS & ACADEMIC GOVERNANCE                               |
| • Non-Causal Attribution Boundary: Organic audience reactions vs Paid marketing conversion ROI    |
| • SQLite Relational Database, Analytical Views, Automated Reports, & Natural Language Assistant    |
+---------------------------------------------------------------------------------------------------+
```
    """)

