"""
Unified Marketing Intelligence & Big Data Analytics Platform.
Master Streamlit Application Entrypoint.

Integrates:
- Project A: YouTube Comment Scraper, Data Cleaning & Audience Engagement
- Project B: Digital Advertising Budget Optimizer & Big Data Processing Lab

Launch Command: streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd

# Page config must be the first Streamlit command executed
st.set_page_config(
    page_title="Unified Marketing Intelligence & Big Data Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and tables gracefully if needed
from src.database import init_database, get_database_status
try:
    db_stat = get_database_status()
    if not db_stat.get('exists', False):
        init_database()
except Exception:
    pass

# Import the 13 modular UI page renderers
from src.ui.page_01_overview import render_page_overview
from src.ui.page_02_youtube_analytics import render_page_youtube_analytics
from src.ui.page_03_youtube_sentiment import render_page_youtube_sentiment
from src.ui.page_04_youtube_engagement import render_page_youtube_engagement
from src.ui.page_05_advertising_analytics import render_page_advertising_analytics
from src.ui.page_06_audience_insights import render_page_audience_insights
from src.ui.page_07_bigdata_lab import render_page_bigdata_lab
from src.ui.page_08_budget_optimizer import render_page_budget_optimizer
from src.ui.page_09_dataset_management import render_page_dataset_management
from src.ui.page_10_database_explorer import render_page_database_explorer
from src.ui.page_11_unified_insights import render_page_unified_insights
from src.ui.page_12_reports import render_page_reports
from src.ui.page_13_assistant import render_page_assistant

# Master 13-Page Navigation Registry
PAGES = {
    "1. Executive Overview": render_page_overview,
    "2. YouTube Comment Analytics": render_page_youtube_analytics,
    "3. YouTube Sentiment Analysis": render_page_youtube_sentiment,
    "4. YouTube Engagement Insights": render_page_youtube_engagement,
    "5. Advertising Analytics": render_page_advertising_analytics,
    "6. Audience Insights": render_page_audience_insights,
    "7. Big Data Processing Lab": render_page_bigdata_lab,
    "8. Advertising Budget Optimizer": render_page_budget_optimizer,
    "9. Dataset Management": render_page_dataset_management,
    "10. Database Explorer": render_page_database_explorer,
    "11. Unified Marketing Insights": render_page_unified_insights,
    "12. Reports and Exports": render_page_reports,
    "13. Analytics Assistant": render_page_assistant,
}

# Sidebar Navigation
with st.sidebar:
    st.title("Navigation Hub")
    st.markdown("**Unified Analytics Platform**")
    
    selected_page_title = st.selectbox(
        "Select Modular Dashboard Page:",
        list(PAGES.keys()),
        index=0
    )
    
    st.divider()
    
    # Active Dataset Indicators
    st.caption("**Session Dataset Status:**")
    yt_loaded = st.session_state.get('youtube_clean_df') is not None
    ad_loaded = st.session_state.get('advertising_df') is not None
    
    if yt_loaded:
        st.success(f"🎥 YouTube: {len(st.session_state['youtube_clean_df']):,} rows")
    else:
        st.caption("🎥 YouTube: No dataset active")
        
    if ad_loaded:
        st.success(f"📈 Advertising: {len(st.session_state['advertising_df']):,} rows")
    else:
        st.caption("📈 Advertising: No dataset active")
        
    st.divider()
    st.caption("• **Project A**: YouTube Scraper & Cleaner")
    st.caption("• **Project B**: Ad Optimizer & Big Data Lab")
    st.caption("• **Engines**: Pandas, Chunk, MapReduce, Spark")
    st.info("DS391 Big Data Analytics  \nUnified Academic Submission")

# Execute selected page renderer
renderer = PAGES[selected_page_title]
renderer()
