"""
Page 5: Digital Advertising Analytics & Marketing KPI Engine.
Computes CTR, CPC, CPA, CVR, and ROAS across platforms and campaigns.
Handles zero denominators and missing values safely (displays N/A when non-evaluable).
Dynamically supports whatever platforms exist in the dataset.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.advertising_analytics import (
    compute_portfolio_macro_summary, aggregate_by_platform,
    aggregate_by_campaign, format_metric, safe_divide
)
from src.dataset_manager import get_bundled_advertising_sample

def render_page_advertising_analytics():
    st.title("Project B: Advertising Analytics & Marketing KPI Engine")
    st.markdown("""
    Evaluates paid advertising performance across active channels and campaigns.  
    All metrics enforce mathematical precision and **zero-division protection**:
    - **CTR** = `(Clicks / Impressions) × 100`
    - **CPC** = `Spend / Clicks`
    - **CPA** = `Spend / Conversions`
    - **Conversion Rate (CVR)** = `(Conversions / Clicks) × 100`
    - **ROAS** = `Revenue / Spend`
    """)
    st.divider()
    
    ad_df = st.session_state.get('advertising_df')
    if ad_df is None or ad_df.empty:
        st.warning("⚠️ No advertising dataset is loaded in memory.")
        if st.button("📥 Load Bundled Advertising Sample (250 Records)", type="primary"):
            sample = get_bundled_advertising_sample()
            if sample is not None:
                st.session_state['advertising_df'] = sample.copy()
                st.session_state['active_ad_name'] = "Bundled Multi-Channel Ad Telemetry"
                st.rerun()
        st.info("Or upload your CSV/Excel dataset in **Dataset Management**.")
        return
        
    macro = compute_portfolio_macro_summary(ad_df)
    plat_df = aggregate_by_platform(ad_df)
    camp_df = aggregate_by_campaign(ad_df)
    
    # Portfolio Top Metrics
    st.subheader("1. Portfolio-Level Macro Performance")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Spend", f"Rs. {macro['total_spend']:,.2f}", f"{macro['total_clicks']:,} Clicks")
    m2.metric("Total Revenue", f"Rs. {macro['total_revenue']:,.2f}", f"Profit: Rs. {macro['total_profit']:,.2f}")
    m3.metric("Portfolio ROAS", format_metric(macro['macro_roas'], prefix="", suffix="x"), "Revenue / Spend")
    m4.metric("Macro CTR", format_metric(macro['macro_ctr'], suffix="%"), "Clicks / Imp")
    m5.metric("Macro CPA", format_metric(macro['macro_cpa'], prefix="Rs. "), "Spend / Conv")
    
    st.divider()
    
    # 2. Platform Comparison
    st.subheader("2. Multi-Platform Performance Comparison")
    if not plat_df.empty:
        st.dataframe(plat_df, use_container_width=True)
        
        pcol1, pcol2 = st.columns(2)
        with pcol1:
            if 'ROAS' in plat_df.columns:
                fig_roas = px.bar(
                    plat_df,
                    x='platform',
                    y='ROAS',
                    color='platform',
                    title="Return on Ad Spend (ROAS) by Platform",
                    text='ROAS'
                )
                fig_roas.update_traces(texttemplate='%{text:.2f}x', textposition='outside')
                st.plotly_chart(fig_roas, use_container_width=True)
                
        with pcol2:
            if 'CPA' in plat_df.columns:
                cpa_valid = plat_df.dropna(subset=['CPA']).sort_values(by='CPA')
                fig_cpa = px.bar(
                    cpa_valid,
                    x='platform',
                    y='CPA',
                    color='platform',
                    title="Cost per Conversion / Acquisition (Rs. CPA)",
                    text='CPA'
                )
                fig_cpa.update_traces(texttemplate='Rs. %{text:.1f}', textposition='outside')
                st.plotly_chart(fig_cpa, use_container_width=True)
    else:
        st.info("No platform column detected in current advertising dataset.")
        
    st.divider()
    
    # 3. Campaign Performance
    st.subheader("3. Campaign Performance Ranking")
    if not camp_df.empty:
        st.dataframe(camp_df, use_container_width=True)
        
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            st.markdown("#### Top Revenue Generating Campaigns:")
            top_c = camp_df.head(3)
            for _, r in top_c.iterrows():
                roas_str = f" | ROAS: {r['ROAS']:.2f}x" if 'ROAS' in r and pd.notna(r['ROAS']) else ""
                st.success(f"**{r['campaign']}**: Rs. {r.get('revenue', 0):,.2f} Revenue{roas_str}")
        with ccol2:
            st.markdown("#### Lowest Performing / Highest CPA Campaigns:")
            if 'CPA' in camp_df.columns:
                high_cpa = camp_df.dropna(subset=['CPA']).sort_values(by='CPA', ascending=False).head(3)
                for _, r in high_cpa.iterrows():
                    st.error(f"**{r['campaign']}**: CPA: Rs. {r['CPA']:.2f} | Spend: Rs. {r.get('spend', 0):,.2f}")
    else:
        st.info("No campaign column detected in current advertising dataset.")
        
    st.divider()
    
    # 4. Zero-Denominator Safety Demonstration
    with st.expander("🛡️ Live Zero-Denominator Formula Validator", expanded=False):
        st.write("Demonstrates how the mathematical engine prevents crashes on zero clicks, impressions, or conversions:")
        zcol1, zcol2, zcol3 = st.columns(3)
        t_clicks = zcol1.number_input("Test Clicks", value=0, min_value=0)
        t_imp = zcol2.number_input("Test Impressions", value=0, min_value=0)
        t_spend = zcol3.number_input("Test Spend (Rs.)", value=500.0, min_value=0.0)
        
        c_ctr = safe_divide(t_clicks * 100.0, t_imp)
        c_cpc = safe_divide(t_spend, t_clicks)
        st.code(f"Calculated CTR: {format_metric(c_ctr, suffix='%')} | Calculated CPC: {format_metric(c_cpc, prefix='Rs. ')}")

