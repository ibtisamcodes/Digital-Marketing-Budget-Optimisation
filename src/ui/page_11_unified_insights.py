"""
Page 11: Unified Marketing Insights & Strategic Synthesis.
Connects Project A (YouTube Organic Audience Signals) with Project B (Paid Advertising Telemetry).
Enforces academic rigor, non-causal attribution, and qualitative synergy discovery.
"""

import streamlit as st
import pandas as pd

from src.cross_domain import generate_unified_marketing_insights
from src.dataset_manager import get_bundled_youtube_sample, get_bundled_advertising_sample

def render_page_unified_insights():
    st.title("Unified Marketing Insights: Organic Signals vs Paid Telemetry")
    st.markdown("""
    Synthesizes **organic audience perception (YouTube comments)** with **paid performance marketing (Advertising ROI)**.  
    Enables holistic decision-making without incorrectly merging independent datasets.
    """)
    st.divider()
    
    yt_df = st.session_state.get('youtube_clean_df')
    ad_df = st.session_state.get('advertising_df')
    
    if (yt_df is None or yt_df.empty) and (ad_df is None or ad_df.empty):
        st.warning("⚠️ Neither YouTube nor Advertising datasets are loaded in memory.")
        qcol1, qcol2 = st.columns(2)
        if qcol1.button("📥 Load Bundled YouTube Sample"):
            sample_yt = get_bundled_youtube_sample()
            if sample_yt is not None:
                st.session_state['youtube_raw_df'] = sample_yt.copy()
                st.session_state['youtube_clean_df'] = sample_yt.copy()
                st.session_state['active_youtube_name'] = "Bundled Dual-Video YouTube Comments"
                st.rerun()
        if qcol2.button("📥 Load Bundled Advertising Sample"):
            sample_ad = get_bundled_advertising_sample()
            if sample_ad is not None:
                st.session_state['advertising_df'] = sample_ad.copy()
                st.session_state['active_ad_name'] = "Bundled Multi-Channel Ad Telemetry"
                st.rerun()
        return
        
    synth = generate_unified_marketing_insights(yt_df, ad_df)
    
    # 1. Macro Signal Comparison Cards
    st.subheader("1. Dual-Domain Macro Overview")
    scol1, scol2 = st.columns(2)
    
    with scol1:
        st.markdown("#### Organic Audience Signals (Project A)")
        if synth['has_youtube']:
            yt_s = synth['youtube_summary']
            st.metric("Total Analyzed Comments", f"{yt_s['total_comments']:,}")
            st.write(f"- **Audience Sentiment**: {yt_s['positive_pct']}% Positive | {yt_s['neutral_pct']}% Neutral | {yt_s['negative_pct']}% Negative")
            st.write(f"- **Total Reactions**: 👍 {yt_s['total_likes']:,} Likes | 💬 {yt_s['total_replies']:,} Replies")
        else:
            st.info("YouTube dataset not loaded.")
            
    with scol2:
        st.markdown("#### Paid Advertising Efficiency (Project B)")
        if synth['has_advertising']:
            ad_s = synth['advertising_summary']
            st.metric("Macro Return on Ad Spend (ROAS)", f"{ad_s['macro_roas']:.2f}x")
            st.write(f"- **Total Spend**: Rs. {ad_s['total_spend']:,.2f} | **Revenue**: Rs. {ad_s['total_revenue']:,.2f}")
            st.write(f"- **Efficiency Ratios**: CTR: {ad_s['macro_ctr']:.2f}% | CPA: Rs. {ad_s['macro_cpa']:.2f}")
            st.write(f"- **Top Yield Channel**: {ad_s['top_platform']}")
        else:
            st.info("Advertising dataset not loaded.")
            
    st.divider()
    
    # 2. Descriptive Strategic Synergies
    if synth['comparative_themes']:
        st.subheader("2. Descriptive Cross-Channel Strategic Synergies")
        st.write("How organic video engagement qualitative feedback informs paid advertising media planning:")
        theme_df = pd.DataFrame(synth['comparative_themes'])
        st.dataframe(theme_df, use_container_width=True)
        
    st.divider()
    
    # 3. Academic Non-Causality Governance
    st.subheader("3. Methodological Governance & Academic Safeguards")
    for safeguard in synth['methodological_safeguards']:
        st.warning(f"🛡️ **Academic Safeguard**: {safeguard}")
        
    st.info("""
    **Core Academic Rule:**
    Organic YouTube comments and paid advertising conversions are separate, unlinked data sources collected at different touchpoints.
    The platform explicitly refuses to allege false micro-level causality (e.g. claiming a positive YouTube comment directly generated an ad conversion).
    Comparisons are strictly descriptive and strategic.
    """)

