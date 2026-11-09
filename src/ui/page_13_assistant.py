"""
Page 13: Analytics Assistant & Natural Language Decision Support.
Answers questions across Project A (YouTube Comments) and Project B (Advertising & Big Data)
using actual computed figures from the active session. Works 100% offline without paid APIs.
"""

import streamlit as st
import pandas as pd

from src.cross_domain import answer_analytics_assistant_query

def render_page_assistant():
    st.title("Analytics Assistant & Decision Support")
    st.markdown("""
    Interactive analytics chatbot answering questions on **YouTube comment sentiment, community engagement,
    advertising ROAS/CPA efficiency, budget allocation, and Big Data benchmarks**.  
    
    100% Grounded & Deterministic: Answers are synthesized strictly from currently loaded datasets.
    No paid LLM API keys required. No hallucinations.
    """)
    st.divider()
    
    yt_df = st.session_state.get('youtube_clean_df')
    ad_df = st.session_state.get('advertising_df')
    alloc_df = st.session_state.get('alloc_df')
    bench_df = st.session_state.get('latest_benchmark_results')
    
    # Quick Prompt Shortcuts
    st.subheader("Executive Prompt Shortcuts (Click to Run):")
    pcol1, pcol2 = st.columns(2)
    
    selected_prompt = None
    if pcol1.button("1. Which advertising platform has the highest ROAS?"):
        selected_prompt = "Which advertising platform has the highest ROAS?"
    if pcol1.button("2. Which channel delivers the lowest CPA (cost per conversion)?"):
        selected_prompt = "Which channel delivers the lowest CPA?"
    if pcol1.button("3. What is the recommended budget allocation?"):
        selected_prompt = "What is the recommended budget allocation?"
        
    if pcol2.button("4. What is the overall YouTube sentiment distribution?"):
        selected_prompt = "What is the overall YouTube sentiment distribution?"
    if pcol2.button("5. Which YouTube comments received the highest likes?"):
        selected_prompt = "Which YouTube comments received the highest likes?"
    if pcol2.button("6. Which Big Data processing engine ran the fastest?"):
        selected_prompt = "Which Big Data processing engine ran the fastest?"
        
    st.divider()
    
    custom_query = st.text_input("Or enter your specific analytical inquiry:", value=selected_prompt or "")
    
    if custom_query:
        st.markdown("#### Assistant Response:")
        with st.spinner("Analyzing active session data..."):
            ans = answer_analytics_assistant_query(
                custom_query,
                youtube_df=yt_df,
                ad_df=ad_df,
                alloc_df=alloc_df,
                benchmark_df=bench_df
            )
            st.markdown(ans)
            
    st.divider()
    st.caption("Assistant Governance: Uses live session state. Never exposes secrets or API keys. Fully operational offline.")

