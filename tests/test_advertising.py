"""
Test Suite for Project B: Digital Advertising Analytics & Marketing KPIs.
Tests flexible column mapping, formula accuracy, zero denominators, missing values,
and platform/audience analytics.
"""

import pytest
import numpy as np
import pandas as pd

from src.advertising_analytics import (
    safe_divide, format_metric, compute_row_level_kpis,
    compute_portfolio_macro_summary, aggregate_by_platform,
    aggregate_by_campaign, analyze_audience_demographics
)
from src.dataset_manager import normalize_advertising_columns, validate_advertising_dataset

@pytest.fixture
def sample_ad_df():
    return pd.DataFrame([
        {
            'Channel': 'Google',
            'Campaign_Name': 'Search Launch',
            'Imps': 10000,
            'Link_Clicks': 500,
            'Ad_Spend': 10000.0,
            'Orders': 50,
            'Conversion_Value': 40000.0,
            'Age': 25,
            'Gender': 'Male',
            'City': 'Lahore',
            'Device': 'Mobile'
        },
        {
            'Channel': 'Facebook',
            'Campaign_Name': 'Feed Display',
            'Imps': 20000,
            'Link_Clicks': 400,
            'Ad_Spend': 8000.0,
            'Orders': 20,
            'Conversion_Value': 16000.0,
            'Age': 32,
            'Gender': 'Female',
            'City': 'Karachi',
            'Device': 'Mobile'
        }
    ])

def test_flexible_column_mapping(sample_ad_df):
    norm_df, mappings = normalize_advertising_columns(sample_ad_df)
    assert 'platform' in norm_df.columns
    assert 'campaign' in norm_df.columns
    assert 'impressions' in norm_df.columns
    assert 'clicks' in norm_df.columns
    assert 'spend' in norm_df.columns
    assert 'conversions' in norm_df.columns
    assert 'revenue' in norm_df.columns
    assert len(mappings) > 0

def test_advertising_kpi_formulas():
    df = pd.DataFrame([{
        'platform': 'Google',
        'impressions': 10000,
        'clicks': 500,
        'spend': 10000.0,
        'conversions': 50,
        'revenue': 40000.0
    }])
    kpis = compute_row_level_kpis(df)
    
    # CTR = (500 / 10000) * 100 = 5.0%
    assert np.isclose(kpis['CTR'].iloc[0], 5.0)
    # CPC = 10000 / 500 = 20.0
    assert np.isclose(kpis['CPC'].iloc[0], 20.0)
    # CPA = 10000 / 50 = 200.0
    assert np.isclose(kpis['CPA'].iloc[0], 200.0)
    # CVR = (50 / 500) * 100 = 10.0%
    assert np.isclose(kpis['CVR'].iloc[0], 10.0)
    # ROAS = 40000 / 10000 = 4.0
    assert np.isclose(kpis['ROAS'].iloc[0], 4.0)

def test_zero_denominator_safeguards():
    zero_df = pd.DataFrame([{
        'platform': 'TikTok',
        'impressions': 0,
        'clicks': 0,
        'spend': 500.0,
        'conversions': 0,
        'revenue': 0.0
    }])
    kpis = compute_row_level_kpis(zero_df)
    assert pd.isna(kpis['CTR'].iloc[0])
    assert pd.isna(kpis['CPC'].iloc[0])
    assert pd.isna(kpis['CPA'].iloc[0])
    assert pd.isna(kpis['CVR'].iloc[0])
    assert np.isclose(kpis['ROAS'].iloc[0], 0.0)

def test_format_metric_displays_na():
    assert format_metric(np.nan) == "N/A"
    assert format_metric(None) == "N/A"
    assert format_metric(float('inf')) == "N/A"
    assert format_metric(15.2, prefix="Rs. ") == "Rs. 15.20"

def test_missing_values_preservation():
    dirty_df = pd.DataFrame([{
        'platform': 'Instagram',
        'impressions': np.nan,
        'clicks': 100,
        'spend': np.nan,
        'conversions': np.nan,
        'revenue': 5000.0
    }])
    kpis = compute_row_level_kpis(dirty_df)
    assert pd.isna(kpis['CTR'].iloc[0])
    assert pd.isna(kpis['CPC'].iloc[0])
    assert pd.isna(kpis['ROAS'].iloc[0])

def test_platform_and_audience_aggregations(sample_ad_df):
    plat_df = aggregate_by_platform(sample_ad_df)
    assert len(plat_df) == 2  # Only Google and Facebook present
    assert 'ROAS' in plat_df.columns
    
    demos = analyze_audience_demographics(sample_ad_df)
    assert 'device' in demos
    assert 'city' in demos

