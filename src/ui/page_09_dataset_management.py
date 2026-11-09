"""
Page 9: Central Dataset Management System.
Allows users to upload custom CSV or Excel files for YouTube comments and Advertising campaigns,
validate schemas, inspect metadata and nulls, download processed datasets, and reset session states.
Maintains strict separation between YouTube and Advertising data.
"""

import streamlit as st
import pandas as pd

from src.dataset_manager import (
    load_file_to_dataframe, validate_youtube_dataset, validate_advertising_dataset,
    normalize_advertising_columns, get_bundled_youtube_sample, get_bundled_advertising_sample
)
from src.cleaner import clean_dataset

def render_page_dataset_management():
    st.title("Central Dataset Management & Upload Center")
    st.markdown("""
    Upload, inspect, validate, and manage datasets for both **Project A (YouTube Comments)** and **Project B (Digital Advertising)**.  
    Supports **CSV and Excel (`.xlsx`, `.xls`)** files with automatic schema validation.
    """)
    st.divider()
    
    tab1, tab2 = st.tabs(["🎥 YouTube Comment Dataset", "📈 Advertising Campaign Dataset"])
    
    # ------------------ TAB 1: YOUTUBE DATASET ------------------
    with tab1:
        st.subheader("Manage YouTube Comment Dataset")
        
        ycol1, ycol2 = st.columns([2, 1])
        with ycol1:
            uploaded_yt = st.file_uploader(
                "Upload YouTube Comments File (CSV or Excel):",
                type=['csv', 'xlsx', 'xls'],
                key="yt_file_uploader"
            )
            if uploaded_yt is not None:
                yt_raw, err = load_file_to_dataframe(uploaded_yt)
                if err:
                    st.error(f"Upload Error: {err}")
                else:
                    is_valid, issues, meta = validate_youtube_dataset(yt_raw)
                    if not is_valid:
                        st.error(f"Schema Validation Failed: {issues}")
                    else:
                        st.session_state['youtube_raw_df'] = yt_raw.copy()
                        cleaned, metrics = clean_dataset(yt_raw)
                        st.session_state['youtube_clean_df'] = cleaned
                        st.session_state['cleaning_metrics'] = metrics
                        st.session_state['active_youtube_name'] = uploaded_yt.name
                        st.success(f"Uploaded and validated '{uploaded_yt.name}' ({len(cleaned):,} comments)!")
                        st.rerun()
                        
        with ycol2:
            st.write("**Quick Actions:**")
            if st.button("📥 Load Bundled YouTube Sample (2,349 Rows)", key="load_yt_sample"):
                sample = get_bundled_youtube_sample()
                if sample is not None:
                    st.session_state['youtube_raw_df'] = sample.copy()
                    c_df, c_metrics = clean_dataset(sample)
                    st.session_state['youtube_clean_df'] = c_df
                    st.session_state['cleaning_metrics'] = c_metrics
                    st.session_state['active_youtube_name'] = "Bundled Dual-Video YouTube Comments"
                    st.success("Loaded bundled YouTube comments dataset!")
                    st.rerun()
                    
            if st.button("🗑️ Remove YouTube Dataset from Session", key="clear_yt_btn"):
                st.session_state['youtube_raw_df'] = None
                st.session_state['youtube_clean_df'] = None
                st.session_state['active_youtube_name'] = None
                st.success("YouTube dataset removed from session.")
                st.rerun()
                
        # Status & Inspection
        yt_active = st.session_state.get('youtube_clean_df')
        if yt_active is not None and not yt_active.empty:
            st.success(f"Active YouTube Dataset: **{st.session_state.get('active_youtube_name', 'Active')}** ({len(yt_active):,} rows, {len(yt_active.columns)} columns)")
            
            scol1, scol2 = st.columns(2)
            with scol1:
                st.write("**Columns & Types:**")
                st.dataframe(pd.DataFrame({"Column": yt_active.columns, "Dtype": [str(d) for d in yt_active.dtypes]}), use_container_width=True)
            with scol2:
                st.write("**Missing Values Summary:**")
                st.dataframe(yt_active.isnull().sum().reset_index().rename(columns={'index': 'Column', 0: 'Null Count'}), use_container_width=True)
                
            st.markdown("#### Dataset Preview (First 50 Rows):")
            st.dataframe(yt_active.head(50), use_container_width=True)
            
            # Download
            csv_data = yt_active.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Active Cleaned YouTube Data (CSV)", data=csv_data, file_name="cleaned_youtube_dataset.csv", mime="text/csv")
        else:
            st.info("No active YouTube dataset in memory.")
            
    # ------------------ TAB 2: ADVERTISING DATASET ------------------
    with tab2:
        st.subheader("Manage Advertising Campaign Dataset")
        
        acol1, acol2 = st.columns([2, 1])
        with acol1:
            uploaded_ad = st.file_uploader(
                "Upload Advertising Dataset File (CSV or Excel):",
                type=['csv', 'xlsx', 'xls'],
                key="ad_file_uploader"
            )
            if uploaded_ad is not None:
                ad_raw, err = load_file_to_dataframe(uploaded_ad)
                if err:
                    st.error(f"Upload Error: {err}")
                else:
                    is_valid, issues, meta = validate_advertising_dataset(ad_raw)
                    if not is_valid:
                        st.error(f"Schema Validation Failed: {issues}")
                    else:
                        norm_df, mappings = normalize_advertising_columns(ad_raw)
                        st.session_state['advertising_df'] = norm_df
                        st.session_state['active_ad_name'] = uploaded_ad.name
                        st.success(f"Uploaded and mapped '{uploaded_ad.name}' ({len(norm_df):,} records)!")
                        if mappings:
                            st.info(f"Column aliases mapped: {mappings}")
                        st.rerun()
                        
        with acol2:
            st.write("**Quick Actions:**")
            if st.button("📥 Load Bundled Advertising Sample (250 Rows)", key="load_ad_sample"):
                sample = get_bundled_advertising_sample()
                if sample is not None:
                    st.session_state['advertising_df'] = sample.copy()
                    st.session_state['active_ad_name'] = "Bundled Multi-Channel Ad Telemetry"
                    st.success("Loaded bundled advertising dataset!")
                    st.rerun()
                    
            if st.button("🗑️ Remove Advertising Dataset from Session", key="clear_ad_btn"):
                st.session_state['advertising_df'] = None
                st.session_state['active_ad_name'] = None
                st.session_state['alloc_df'] = None
                st.success("Advertising dataset removed from session.")
                st.rerun()
                
        # Status & Inspection
        ad_active = st.session_state.get('advertising_df')
        if ad_active is not None and not ad_active.empty:
            st.success(f"Active Advertising Dataset: **{st.session_state.get('active_ad_name', 'Active')}** ({len(ad_active):,} rows, {len(ad_active.columns)} columns)")
            
            scol1, scol2 = st.columns(2)
            with scol1:
                st.write("**Columns & Types:**")
                st.dataframe(pd.DataFrame({"Column": ad_active.columns, "Dtype": [str(d) for d in ad_active.dtypes]}), use_container_width=True)
            with scol2:
                st.write("**Missing Values Summary:**")
                st.dataframe(ad_active.isnull().sum().reset_index().rename(columns={'index': 'Column', 0: 'Null Count'}), use_container_width=True)
                
            st.markdown("#### Dataset Preview (First 50 Rows):")
            st.dataframe(ad_active.head(50), use_container_width=True)
            
            csv_data = ad_active.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Active Advertising Data (CSV)", data=csv_data, file_name="advertising_dataset.csv", mime="text/csv")
        else:
            st.info("No active advertising dataset in memory.")

