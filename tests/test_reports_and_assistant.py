"""
Test Suite for Reporting Engine & Analytics Assistant.
Tests generation of all 6 report types from active data,
and tests assistant resolution of questions across Project A and Project B.
"""

import pytest
import pandas as pd

from src.report_generator_unified import (
    generate_youtube_analysis_report, generate_youtube_cleaning_report,
    generate_advertising_report, generate_budget_optimization_report,
    generate_bigdata_benchmarking_report, generate_combined_marketing_report
)
from src.cross_domain import answer_analytics_assistant_query, generate_unified_marketing_insights

@pytest.fixture
def test_data():
    yt_df = pd.DataFrame([
        {'comment': 'Amazing track and visuals!', 'likes': 500, 'reply_count': 25, 'published_at': '2025-01-01T00:00:00Z'},
        {'comment': 'Not good, poor editing.', 'likes': 5, 'reply_count': 1, 'published_at': '2025-01-02T00:00:00Z'}
    ])
    ad_df = pd.DataFrame([
        {'platform': 'Google', 'spend': 5000.0, 'revenue': 20000.0, 'clicks': 250, 'impressions': 5000, 'conversions': 25},
        {'platform': 'Instagram', 'spend': 4000.0, 'revenue': 12000.0, 'clicks': 200, 'impressions': 4000, 'conversions': 15}
    ])
    alloc_df = pd.DataFrame([
        {'platform': 'Google', 'allocated_budget': 600000.0, 'allocation_pct': 60.0, 'projected_revenue': 2400000.0, 'projected_conversions': 3000},
        {'platform': 'Instagram', 'allocated_budget': 400000.0, 'allocation_pct': 40.0, 'projected_revenue': 1200000.0, 'projected_conversions': 1500}
    ])
    bench_df = pd.DataFrame([
        {'Engine': 'Pandas', 'Records Processed': 1000, 'Execution Time (s)': 0.005, 'Peak Memory (MB)': 0.2, 'Throughput (Rec/Sec)': 200000, 'Status': 'PASS'}
    ])
    return yt_df, ad_df, alloc_df, bench_df

def test_all_six_reports_generation(test_data):
    yt_df, ad_df, alloc_df, bench_df = test_data
    
    r1 = generate_youtube_analysis_report(yt_df)
    assert "YouTube Comment Analytics" in r1
    assert "Executive Summary" in r1
    
    r2 = generate_youtube_cleaning_report({"initial_rows": 100, "final_rows": 98, "dropped_duplicates": 2})
    assert "Cleaning & Integrity Audit" in r2
    
    r3 = generate_advertising_report(ad_df)
    assert "Advertising Campaign Performance" in r3
    assert "Google" in r3
    
    r4 = generate_budget_optimization_report(alloc_df, total_budget=1_000_000.0, strategy="Maximize ROAS")
    assert "Budget Optimization Proposal" in r4
    assert "1,000,000" in r4
    
    r5 = generate_bigdata_benchmarking_report(bench_df)
    assert "Big Data Processing Engine Scalability" in r5
    
    r6 = generate_combined_marketing_report(yt_df, ad_df, alloc_df)
    assert "Cross-Domain Strategic Report" in r6

def test_analytics_assistant_query_handling(test_data):
    yt_df, ad_df, alloc_df, bench_df = test_data
    
    # Ad inquiries
    ans_roas = answer_analytics_assistant_query("Which platform has highest ROAS?", yt_df, ad_df, alloc_df, bench_df)
    assert "Google" in ans_roas
    
    ans_cpa = answer_analytics_assistant_query("What is the lowest CPA?", yt_df, ad_df, alloc_df, bench_df)
    assert "CPA" in ans_cpa
    
    ans_budget = answer_analytics_assistant_query("What is the recommended budget allocation?", yt_df, ad_df, alloc_df, bench_df)
    assert "Google" in ans_budget and "Instagram" in ans_budget
    
    # YouTube inquiries
    ans_sent = answer_analytics_assistant_query("What is the sentiment distribution?", yt_df, ad_df, alloc_df, bench_df)
    assert "Positive Sentiment" in ans_sent
    
    ans_eng = answer_analytics_assistant_query("Which comments had highest engagement?", yt_df, ad_df, alloc_df, bench_df)
    assert "Likes" in ans_eng
    
    # Big Data inquiries
    ans_bench = answer_analytics_assistant_query("Which engine ran the fastest?", yt_df, ad_df, alloc_df, bench_df)
    assert "Pandas" in ans_bench

def test_assistant_graceful_empty_states():
    ans = answer_analytics_assistant_query("Which platform has highest ROAS?", None, None, None, None)
    assert "No advertising dataset" in ans

