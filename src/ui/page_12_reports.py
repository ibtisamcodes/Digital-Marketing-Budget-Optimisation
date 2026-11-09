"""
Page 12: Reporting and Academic Exports Center.
Generates, previews, and exports 6 formal Markdown reports and CSV data extracts
directly from active session datasets:
1. YouTube Comment Analysis Report
2. YouTube Data Cleaning Audit Report
3. Digital Advertising Campaign Performance Report
4. Advertising Budget Optimization Proposal
5. Big Data Engine Scalability Benchmark Report
6. Unified Marketing Insights Synthesis Report
"""

import streamlit as st
import pandas as pd

from src.report_generator_unified import (
    generate_youtube_analysis_report, generate_youtube_cleaning_report,
    generate_advertising_report, generate_budget_optimization_report,
    generate_bigdata_benchmarking_report, generate_combined_marketing_report
)

def render_page_reports():
    st.title("Reporting & Academic Submission Exports")
    st.markdown("""
    Generate, preview, and download formal analytical reports and CSV exports.  
    All generated reports synthesize **actual computed figures** from current session datasets.
    """)
    st.divider()
    
    yt_df = st.session_state.get('youtube_clean_df')
    ad_df = st.session_state.get('advertising_df')
    alloc_df = st.session_state.get('alloc_df')
    bench_df = st.session_state.get('latest_benchmark_results')
    metrics = st.session_state.get('cleaning_metrics', {})
    
    report_type = st.selectbox(
        "Select Report Document to Generate:",
        [
            "1. YouTube Comment Analysis Report",
            "2. YouTube Data Cleaning Audit Report",
            "3. Digital Advertising Campaign Performance Report",
            "4. Advertising Budget Optimization Proposal",
            "5. Big Data Processing Scalability Report",
            "6. Unified Cross-Domain Marketing Insights Report"
        ]
    )
    
    report_content = ""
    report_filename = "report.md"
    
    if report_type.startswith("1."):
        if yt_df is None or yt_df.empty:
            st.warning("Please load or upload a YouTube dataset to generate this report.")
            return
        report_content = generate_youtube_analysis_report(yt_df, source_name=st.session_state.get('active_youtube_name', 'YouTube Dataset'))
        report_filename = "YouTube_Comment_Analytics_Report.md"
        
    elif report_type.startswith("2."):
        report_content = generate_youtube_cleaning_report(metrics, source_name=st.session_state.get('active_youtube_name', 'YouTube Dataset'))
        report_filename = "YouTube_Data_Cleaning_Audit_Report.md"
        
    elif report_type.startswith("3."):
        if ad_df is None or ad_df.empty:
            st.warning("Please load or upload an advertising dataset to generate this report.")
            return
        report_content = generate_advertising_report(ad_df, source_name=st.session_state.get('active_ad_name', 'Advertising Dataset'))
        report_filename = "Digital_Advertising_Performance_Report.md"
        
    elif report_type.startswith("4."):
        if alloc_df is None or alloc_df.empty:
            st.warning("Please run the Budget Optimizer page to generate allocation schedules first.")
            return
        tot = alloc_df['allocated_budget'].sum()
        report_content = generate_budget_optimization_report(alloc_df, total_budget=tot, strategy="Optimized Performance")
        report_filename = "Budget_Optimization_Proposal.md"
        
    elif report_type.startswith("5."):
        if bench_df is None or bench_df.empty:
            st.warning("Please execute a benchmark in the Big Data Processing Lab first.")
            return
        report_content = generate_bigdata_benchmarking_report(bench_df)
        report_filename = "Big_Data_Scalability_Benchmark_Report.md"
        
    elif report_type.startswith("6."):
        report_content = generate_combined_marketing_report(yt_df, ad_df, alloc_df)
        report_filename = "Unified_Marketing_Intelligence_Report.md"
        
    st.subheader(f"Generated Document: {report_filename}")
    
    st.download_button(
        label=f"📥 Download {report_filename} (Markdown)",
        data=report_content,
        file_name=report_filename,
        mime="text/markdown",
        type="primary"
    )
    
    with st.expander("📄 Document Preview", expanded=True):
        st.markdown(report_content)

