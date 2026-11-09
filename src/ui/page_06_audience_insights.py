"""
Page 6: Advertising Audience & Demographic Insights.
Evaluates performance across age groups, gender, cities, and device types.
Only displays demographic sections when the corresponding columns are present.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.advertising_analytics import analyze_audience_demographics
from src.dataset_manager import get_bundled_advertising_sample

def render_page_audience_insights():
    st.title("Project B: Advertising Audience & Demographic Insights")
    st.markdown("""
    Examines customer conversion and revenue distribution across audience dimensions.  
    Only dimensions genuinely present in the active dataset are analyzed.
    """)
    st.divider()
    
    ad_df = st.session_state.get('advertising_df')
    if ad_df is None or ad_df.empty:
        st.warning("⚠️ No advertising dataset is loaded in memory.")
        if st.button("📥 Load Bundled Advertising Sample (250 Records)"):
            sample = get_bundled_advertising_sample()
            if sample is not None:
                st.session_state['advertising_df'] = sample.copy()
                st.session_state['active_ad_name'] = "Bundled Multi-Channel Ad Telemetry"
                st.rerun()
        st.info("Or upload your dataset in **Dataset Management**.")
        return
        
    demographics = analyze_audience_demographics(ad_df)
    
    if not demographics:
        st.info("ℹ️ The loaded advertising dataset does not contain demographic columns (`age`, `gender`, `city`, `device`).")
        st.write("Columns present in current dataset:", list(ad_df.columns))
        return
        
    st.subheader(f"Available Demographic Dimensions: {list(demographics.keys())}")
    
    # 1. Device Breakdown
    if 'device' in demographics:
        st.markdown("### 1. Device Type Performance")
        dev_df = demographics['device']
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            st.dataframe(dev_df, use_container_width=True)
        with dcol2:
            fig_dev = px.pie(dev_df, names='device', values='conversions', hole=0.35, title="Conversions by Device Type")
            st.plotly_chart(fig_dev, use_container_width=True)
            
    # 2. Gender Breakdown
    if 'gender' in demographics:
        st.markdown("### 2. Gender Targeting Performance")
        gen_df = demographics['gender']
        gcol1, gcol2 = st.columns(2)
        with gcol1:
            st.dataframe(gen_df, use_container_width=True)
        with gcol2:
            fig_gen = px.bar(gen_df, x='gender', y='revenue', color='gender', title="Attributed Revenue by Gender (PKR)")
            st.plotly_chart(fig_gen, use_container_width=True)
            
    # 3. City Breakdown
    if 'city' in demographics:
        st.markdown("### 3. Geographic / City Performance")
        city_df = demographics['city']
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            st.dataframe(city_df.sort_values(by='revenue', ascending=False), use_container_width=True)
        with ccol2:
            fig_city = px.bar(
                city_df.sort_values(by='revenue', ascending=False),
                x='city',
                y='revenue',
                color='city',
                title="Revenue by Urban Center (PKR)"
            )
            st.plotly_chart(fig_city, use_container_width=True)
            
    # 4. Age Bracket Breakdown
    if 'age' in demographics:
        st.markdown("### 4. Age Bracket Performance")
        age_df = demographics['age']
        acol1, acol2 = st.columns(2)
        with acol1:
            st.dataframe(age_df, use_container_width=True)
        with acol2:
            fig_age = px.bar(age_df, x=age_df.columns[0], y='conversions', title="Conversions by Age Bracket")
            st.plotly_chart(fig_age, use_container_width=True)

