"""
Central Dataset Manager & Validator for Unified Analytics Platform.
Handles session-state data persistence, CSV and Excel file ingestion,
schema validation, flexible column mapping, and sample dataset provisioning.
"""

import io
import os
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np

YOUTUBE_SAMPLE_PATH = os.path.join("data", "processed", "cleaned_comments.csv")
AD_SAMPLE_PATH = os.path.join("data", "raw", "advertising_sample.csv")

# Standard Column Aliases for Flexible Mapping
AD_COLUMN_MAPPINGS = {
    'platform': ['platform', 'channel', 'ad_platform', 'source', 'network'],
    'campaign': ['campaign', 'campaign_name', 'ad_group', 'campaign_id'],
    'date': ['date', 'day', 'timestamp', 'event_date'],
    'impressions': ['impressions', 'views', 'imps', 'impressions_count'],
    'clicks': ['clicks', 'link_clicks', 'click_count'],
    'spend': ['spend', 'cost', 'ad_spend', 'expenditure', 'amount_spent', 'budget_spent'],
    'conversions': ['conversions', 'orders', 'purchases', 'leads', 'acquisitions', 'convs'],
    'revenue': ['revenue', 'sales', 'conversion_value', 'total_revenue', 'income'],
    'age': ['age', 'age_group', 'age_bracket'],
    'gender': ['gender', 'sex'],
    'city': ['city', 'location', 'region', 'metro'],
    'device': ['device', 'device_type', 'platform_device']
}

def load_file_to_dataframe(uploaded_file) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safely reads uploaded CSV or Excel files into a pandas DataFrame.
    Returns: (DataFrame, error_message)
    """
    if uploaded_file is None:
        return None, "No file provided."
        
    fname = getattr(uploaded_file, 'name', 'uploaded_file').lower()
    try:
        if fname.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            # Try utf-8 first, fallback to latin-1
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                if hasattr(uploaded_file, 'seek'):
                    uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')
                
        if df.empty:
            return None, "Uploaded file contains no rows."
        return df, None
    except Exception as ex:
        return None, f"Error parsing file: {str(ex)}"


def validate_youtube_dataset(df: pd.DataFrame) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates that the DataFrame conforms to YouTube comment schema requirements.
    Must contain at least a comment text column.
    """
    issues = []
    metadata = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'has_likes': False,
        'has_replies': False,
        'has_dates': False,
        'has_author': False
    }
    
    col_map = {str(c).strip().lower(): c for c in df.columns}
    
    # Check comment text column
    comment_col = None
    for cand in ['comment', 'text', 'comment_text', 'body', 'message']:
        if cand in col_map:
            comment_col = col_map[cand]
            break
            
    if not comment_col:
        issues.append("Dataset must contain a comment text column (e.g. 'comment', 'text').")
        return False, issues, metadata
        
    metadata['comment_column'] = comment_col
    metadata['has_likes'] = any(c in col_map for c in ['likes', 'like_count', 'thumbs_up'])
    metadata['has_replies'] = any(c in col_map for c in ['reply_count', 'replies', 'reply_counts'])
    metadata['has_dates'] = any(c in col_map for c in ['published_at', 'date', 'timestamp', 'publishedat'])
    metadata['has_author'] = any(c in col_map for c in ['author', 'author_name', 'user'])
    metadata['null_comments'] = int(df[comment_col].isnull().sum())
    
    return True, issues, metadata


def normalize_advertising_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Maps variable column names to canonical advertising schema names.
    Returns: (renamed_df, mapping_used)
    """
    renamed = df.copy()
    existing_cols = {str(c).strip().lower(): c for c in renamed.columns}
    mapping_used = {}
    
    for canonical, aliases in AD_COLUMN_MAPPINGS.items():
        for alias in aliases:
            if alias in existing_cols:
                original = existing_cols[alias]
                if original != canonical:
                    renamed = renamed.rename(columns={original: canonical})
                    mapping_used[original] = canonical
                break
                
    return renamed, mapping_used


def validate_advertising_dataset(df: pd.DataFrame) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates advertising dataset schema.
    Must contain core performance columns: spend, clicks (or impressions), and revenue/conversions.
    """
    issues = []
    norm_df, mappings = normalize_advertising_columns(df)
    
    metadata = {
        'total_rows': len(norm_df),
        'total_columns': len(norm_df.columns),
        'columns': list(norm_df.columns),
        'mappings_applied': mappings,
        'has_spend': 'spend' in norm_df.columns,
        'has_clicks': 'clicks' in norm_df.columns,
        'has_impressions': 'impressions' in norm_df.columns,
        'has_conversions': 'conversions' in norm_df.columns,
        'has_revenue': 'revenue' in norm_df.columns,
        'has_platform': 'platform' in norm_df.columns,
        'has_campaign': 'campaign' in norm_df.columns,
        'has_demographics': any(c in norm_df.columns for c in ['age', 'gender', 'city', 'device'])
    }
    
    # Mandatory minimum requirements for advertising analytics
    missing_mandatory = []
    for req in ['spend', 'clicks', 'conversions']:
        if req not in norm_df.columns:
            missing_mandatory.append(req)
            
    if missing_mandatory:
        issues.append(f"Missing mandatory advertising metrics: {missing_mandatory}. Supported aliases: { {k: AD_COLUMN_MAPPINGS[k] for k in missing_mandatory} }")
        return False, issues, metadata
        
    return True, issues, metadata


def get_bundled_youtube_sample() -> Optional[pd.DataFrame]:
    """Loads bundled YouTube comment sample from processed or raw directory."""
    if os.path.exists(YOUTUBE_SAMPLE_PATH):
        return pd.read_csv(YOUTUBE_SAMPLE_PATH)
    # Fallback to any raw csv
    import glob
    raw_csvs = glob.glob("data/raw/*.csv")
    for f in raw_csvs:
        if "high-heels" in f.lower() or "gali-gali" in f.lower():
            return pd.read_csv(f)
    return None


def get_bundled_advertising_sample() -> Optional[pd.DataFrame]:
    """Loads or generates lightweight advertising sample (200 records)."""
    if os.path.exists(AD_SAMPLE_PATH):
        return pd.read_csv(AD_SAMPLE_PATH)
        
    # Generate a lightweight 250-row sample on demand
    from src.dataset_generator import generate_advertising_data
    df = generate_advertising_data(n_records=250, seed=42)
    os.makedirs(os.path.dirname(AD_SAMPLE_PATH), exist_ok=True)
    df.to_csv(AD_SAMPLE_PATH, index=False)
    return df
