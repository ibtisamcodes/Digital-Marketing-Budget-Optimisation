"""
Digital Advertising Analytics & Marketing KPI Engine.
Computes core marketing metrics with strict zero-denominator handling and flexible column mapping.
Displays N/A when metrics cannot be mathematically evaluated.
Never assumes fixed platforms or fixed demographic columns.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd

from src.dataset_manager import normalize_advertising_columns

def safe_divide(numerator: pd.Series | np.ndarray | float,
                denominator: pd.Series | np.ndarray | float,
                default_val: float = np.nan) -> pd.Series | np.ndarray | float:
    """
    Safely divides numerator by denominator, returning default_val (NaN) when denominator is 0, None, or NaN.
    """
    if isinstance(numerator, (pd.Series, np.ndarray)):
        denom_clean = np.where(pd.isna(denominator) | (denominator == 0), np.nan, denominator)
        res = np.where(np.isnan(denom_clean), default_val, numerator / denom_clean)
        res = np.nan_to_num(res, nan=default_val, posinf=default_val, neginf=default_val)
        if isinstance(numerator, pd.Series):
            return pd.Series(res, index=numerator.index)
        return res
    else:
        if denominator is None or pd.isna(denominator) or denominator == 0:
            return default_val
        return numerator / denominator


def format_metric(val: float, fmt: str = "{:.2f}", prefix: str = "", suffix: str = "") -> str:
    """Formats float metric cleanly, returning 'N/A' if value is NaN or None."""
    if val is None or pd.isna(val) or np.isinf(val):
        return "N/A"
    return f"{prefix}{fmt.format(val)}{suffix}"


def compute_row_level_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Computes row-level CTR, CPC, CPA, CVR, ROAS for an advertising DataFrame."""
    norm_df, _ = normalize_advertising_columns(df)
    data = norm_df.copy()
    
    # Calculate row-level metrics with safe divide returning NaN when invalid
    if 'clicks' in data.columns and 'impressions' in data.columns:
        data['CTR'] = safe_divide(data['clicks'] * 100.0, data['impressions'])
    if 'spend' in data.columns and 'clicks' in data.columns:
        data['CPC'] = safe_divide(data['spend'], data['clicks'])
    if 'spend' in data.columns and 'conversions' in data.columns:
        data['CPA'] = safe_divide(data['spend'], data['conversions'])
    if 'conversions' in data.columns and 'clicks' in data.columns:
        data['CVR'] = safe_divide(data['conversions'] * 100.0, data['clicks'])
    if 'revenue' in data.columns and 'spend' in data.columns:
        data['ROAS'] = safe_divide(data['revenue'], data['spend'])
        
    return data


def compute_portfolio_macro_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes corporate portfolio-level aggregated KPIs.
    Calculates macro ratios directly from aggregated totals rather than averages of averages.
    """
    norm_df, _ = normalize_advertising_columns(df)
    
    total_spend = float(norm_df['spend'].sum()) if 'spend' in norm_df.columns else 0.0
    total_rev = float(norm_df['revenue'].sum()) if 'revenue' in norm_df.columns else 0.0
    total_imp = int(norm_df['impressions'].sum()) if 'impressions' in norm_df.columns else 0
    total_clicks = int(norm_df['clicks'].sum()) if 'clicks' in norm_df.columns else 0
    total_conv = int(norm_df['conversions'].sum()) if 'conversions' in norm_df.columns else 0
    
    macro_ctr = safe_divide(total_clicks * 100.0, total_imp)
    macro_cpc = safe_divide(total_spend, total_clicks)
    macro_cpa = safe_divide(total_spend, total_conv)
    macro_cvr = safe_divide(total_conv * 100.0, total_clicks)
    macro_roas = safe_divide(total_rev, total_spend)
    
    return {
        'total_records': len(norm_df),
        'total_spend': total_spend,
        'total_revenue': total_rev,
        'total_profit': total_rev - total_spend,
        'total_impressions': total_imp,
        'total_clicks': total_clicks,
        'total_conversions': total_conv,
        'macro_ctr': macro_ctr,
        'macro_cpc': macro_cpc,
        'macro_cpa': macro_cpa,
        'macro_cvr': macro_cvr,
        'macro_roas': macro_roas,
    }


def aggregate_by_platform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates performance dynamically by whatever platforms exist in the dataset.
    Never assumes fixed 5 platforms.
    """
    norm_df, _ = normalize_advertising_columns(df)
    if 'platform' not in norm_df.columns:
        return pd.DataFrame()
        
    agg_dict = {}
    for col in ['impressions', 'clicks', 'spend', 'conversions', 'revenue']:
        if col in norm_df.columns:
            agg_dict[col] = 'sum'
            
    grouped = norm_df.groupby('platform', as_index=False).agg(agg_dict)
    
    # Calculate macro KPIs
    if 'clicks' in grouped.columns and 'impressions' in grouped.columns:
        grouped['CTR'] = safe_divide(grouped['clicks'] * 100.0, grouped['impressions'])
    if 'spend' in grouped.columns and 'clicks' in grouped.columns:
        grouped['CPC'] = safe_divide(grouped['spend'], grouped['clicks'])
    if 'spend' in grouped.columns and 'conversions' in grouped.columns:
        grouped['CPA'] = safe_divide(grouped['spend'], grouped['conversions'])
    if 'conversions' in grouped.columns and 'clicks' in grouped.columns:
        grouped['CVR'] = safe_divide(grouped['conversions'] * 100.0, grouped['clicks'])
    if 'revenue' in grouped.columns and 'spend' in grouped.columns:
        grouped['ROAS'] = safe_divide(grouped['revenue'], grouped['spend'])
    if 'revenue' in grouped.columns and 'spend' in grouped.columns:
        grouped['profit'] = grouped['revenue'] - grouped['spend']
        
    sort_col = 'ROAS' if 'ROAS' in grouped.columns else 'spend'
    return grouped.sort_values(by=sort_col, ascending=False).reset_index(drop=True)


def aggregate_by_campaign(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates performance by campaign."""
    norm_df, _ = normalize_advertising_columns(df)
    if 'campaign' not in norm_df.columns:
        return pd.DataFrame()
        
    agg_dict = {}
    for col in ['impressions', 'clicks', 'spend', 'conversions', 'revenue']:
        if col in norm_df.columns:
            agg_dict[col] = 'sum'
            
    grouped = norm_df.groupby('campaign', as_index=False).agg(agg_dict)
    
    if 'clicks' in grouped.columns and 'impressions' in grouped.columns:
        grouped['CTR'] = safe_divide(grouped['clicks'] * 100.0, grouped['impressions'])
    if 'spend' in grouped.columns and 'clicks' in grouped.columns:
        grouped['CPC'] = safe_divide(grouped['spend'], grouped['clicks'])
    if 'spend' in grouped.columns and 'conversions' in grouped.columns:
        grouped['CPA'] = safe_divide(grouped['spend'], grouped['conversions'])
    if 'conversions' in grouped.columns and 'clicks' in grouped.columns:
        grouped['CVR'] = safe_divide(grouped['conversions'] * 100.0, grouped['clicks'])
    if 'revenue' in grouped.columns and 'spend' in grouped.columns:
        grouped['ROAS'] = safe_divide(grouped['revenue'], grouped['spend'])
    if 'revenue' in grouped.columns and 'spend' in grouped.columns:
        grouped['profit'] = grouped['revenue'] - grouped['spend']
        
    sort_col = 'revenue' if 'revenue' in grouped.columns else 'spend'
    return grouped.sort_values(by=sort_col, ascending=False).reset_index(drop=True)


def analyze_audience_demographics(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyzes performance across demographic dimensions (age, gender, city, device)
    only if those columns exist in the dataset.
    """
    norm_df, _ = normalize_advertising_columns(df)
    demographic_results = {}
    
    for dim in ['age', 'gender', 'city', 'device']:
        if dim in norm_df.columns:
            # If age is numeric, group into brackets
            dim_df = norm_df.copy()
            if dim == 'age' and pd.api.types.is_numeric_dtype(dim_df['age']):
                dim_df['age_group'] = pd.cut(
                    dim_df['age'],
                    bins=[0, 18, 25, 35, 50, 100],
                    labels=['<18', '18-24', '25-34', '35-49', '50+'],
                    right=False
                )
                dim_key = 'age_group'
            else:
                dim_key = dim
                
            grouped = dim_df.groupby(dim_key, observed=False, as_index=False).agg({
                'spend': 'sum' if 'spend' in dim_df.columns else lambda x: 0,
                'revenue': 'sum' if 'revenue' in dim_df.columns else lambda x: 0,
                'conversions': 'sum' if 'conversions' in dim_df.columns else lambda x: 0,
                'clicks': 'sum' if 'clicks' in dim_df.columns else lambda x: 0
            })
            if 'revenue' in grouped.columns and 'spend' in grouped.columns:
                grouped['ROAS'] = safe_divide(grouped['revenue'], grouped['spend'])
            demographic_results[dim] = grouped
            
    return demographic_results
