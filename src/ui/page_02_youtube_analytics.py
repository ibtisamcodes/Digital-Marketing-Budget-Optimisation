"""
Page 2: YouTube Comment Analytics & Data Cleaning.
Features dataset inspection, automated cleaning pipeline, deduplication, and
YouTube Data API v3 comment harvesting integration.
"""

import streamlit as st
import pandas as pd

from src.cleaner import clean_dataset
from src.dataset_manager import get_bundled_youtube_sample
from src.youtube_scraper import get_api_status, scrape_youtube_comments

def render_page_youtube_analytics():
    st.title("Project A: YouTube Comment Analytics & Data Cleaning")
    st.markdown("""
    Inspect, audit, clean, and harvest YouTube public comment threads.  
    Preserves raw source text while generating a standardized analytical dataset.
    """)
    st.divider()
    
    # 1. Scraper Section
    with st.expander("🎥 Optional: Live YouTube Data API v3 Comment Harvester", expanded=False):
        api_stat = get_api_status()
        if api_stat["configured"]:
            st.success(f"YouTube API Status: **{api_stat['status_label']}**")
        else:
            st.info(f"YouTube API Status: **{api_stat['status_label']}**. (Note: Scraper requires YOUTUBE_API_KEY in .env, but CSV/Excel upload works without any key).")
            
        scol1, scol2 = st.columns([3, 1])
        video_input = scol1.text_input("Enter YouTube Video URL or 11-Character Video ID:", placeholder="e.g. https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        max_c = scol2.number_input("Max Comments to Harvest:", min_value=10, max_value=2000, value=150, step=50)
        
        if st.button("🚀 Harvest Comments via API", disabled=not api_stat["can_scrape"]):
            if not video_input:
                st.error("Please provide a valid YouTube Video URL or ID.")
            else:
                with st.spinner("Connecting to YouTube Data API v3..."):
                    scraped_df, err = scrape_youtube_comments(video_input, max_comments=int(max_c))
                    if err:
                        st.error(f"Scraper Notice: {err}")
                    elif scraped_df is not None:
                        st.session_state['youtube_raw_df'] = scraped_df.copy()
                        cleaned_df, metrics = clean_dataset(scraped_df)
                        st.session_state['youtube_clean_df'] = cleaned_df
                        st.session_state['cleaning_metrics'] = metrics
                        st.session_state['active_youtube_name'] = f"Scraped Video ({len(cleaned_df)} comments)"
                        st.success(f"Successfully harvested {len(cleaned_df):,} comments!")
                        st.rerun()
                        
    st.divider()
    
    # Check loaded dataset
    raw_df = st.session_state.get('youtube_raw_df')
    clean_df = st.session_state.get('youtube_clean_df')
    
    if raw_df is None and clean_df is None:
        st.warning("⚠️ No YouTube dataset is currently loaded in memory.")
        st.write("You can load the bundled dual-video YouTube comments (2,349 rows) or upload your own file:")
        if st.button("📥 Load Bundled YouTube Comments Dataset", type="primary"):
            sample = get_bundled_youtube_sample()
            if sample is not None:
                st.session_state['youtube_raw_df'] = sample.copy()
                c_df, c_metrics = clean_dataset(sample)
                st.session_state['youtube_clean_df'] = c_df
                st.session_state['cleaning_metrics'] = c_metrics
                st.session_state['active_youtube_name'] = "Bundled Dual-Video YouTube Comments"
                st.rerun()
        st.info("Or navigate to **Dataset Management** in the sidebar to upload a custom CSV or Excel file.")
        return
        
    active_df = clean_df if clean_df is not None else raw_df
    
    st.subheader("1. Data Inspection & Schema Summary")
    
    icol1, icol2, icol3, icol4 = st.columns(4)
    icol1.metric("Total Records", f"{len(active_df):,}")
    icol2.metric("Total Columns", f"{len(active_df.columns)}")
    unique_authors = active_df['author'].nunique() if 'author' in active_df.columns else "N/A"
    icol3.metric("Unique Commenters", f"{unique_authors:,}" if isinstance(unique_authors, int) else unique_authors)
    duplicate_rows = int(active_df.duplicated().sum())
    icol4.metric("Exact Duplicate Rows", f"{duplicate_rows}")
    
    # Schema inspection table
    schema_rows = []
    for col in active_df.columns:
        schema_rows.append({
            "Column Name": col,
            "Data Type": str(active_df[col].dtype),
            "Non-Null Count": int(active_df[col].notnull().sum()),
            "Null Count": int(active_df[col].isnull().sum()),
            "Null Percentage": f"{(active_df[col].isnull().sum() / len(active_df)) * 100:.2f}%",
            "Unique Values": int(active_df[col].nunique()),
            "Sample Value": str(active_df[col].iloc[0])[:60] if len(active_df) > 0 else ""
        })
    st.dataframe(pd.DataFrame(schema_rows), use_container_width=True)
    
    st.divider()
    
    # 2. Data Cleaning Section
    st.subheader("2. Automated Data Cleaning & Deduplication Pipeline")
    
    if st.button("🧹 Run / Re-run Cleaning Pipeline on Current Dataset"):
        source_df = raw_df if raw_df is not None else active_df
        c_df, c_metrics = clean_dataset(source_df)
        st.session_state['youtube_clean_df'] = c_df
        st.session_state['cleaning_metrics'] = c_metrics
        st.success("Cleaning pipeline executed successfully!")
        st.rerun()
        
    metrics = st.session_state.get('cleaning_metrics')
    if metrics:
        st.markdown("#### Cleaning Transformation Summary:")
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Initial Rows", f"{metrics.get('initial_rows', len(active_df)):,}")
        mcol2.metric("Final Rows", f"{metrics.get('final_rows', len(active_df)):,}")
        mcol3.metric("Duplicates Removed", f"{metrics.get('dropped_duplicates', 0):,}")
        mcol4.metric("Repeated Comments Preserved", f"{metrics.get('repeated_comment_texts', 0):,}")
        
    st.markdown("#### Cleaned Dataset Preview:")
    st.dataframe(active_df.head(100), use_container_width=True)
    
    # Download cleaned data
    csv_bytes = active_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned YouTube Dataset (CSV)",
        data=csv_bytes,
        file_name="cleaned_youtube_comments.csv",
        mime="text/csv"
    )

