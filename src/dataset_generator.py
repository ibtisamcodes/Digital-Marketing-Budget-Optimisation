"""
Synthetic Dataset Generator for Digital Advertising Telemetry.
Provides reproducible dataset generation for multi-platform Advertising Data
(Facebook, Instagram, Google, TikTok, YouTube).
Schema: date, campaign, platform, impressions, clicks, spend, conversions, revenue, age, gender, city, device
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

AD_PLATFORMS = ['Facebook', 'Instagram', 'Google', 'TikTok', 'YouTube']
CAMPAIGNS = [
    'Mega Audio Launch',
    'Wearable Tech Fest',
    'Summer Clearance 2026',
    'Brand Equity & Awareness',
    'High-ROAS Direct Response'
]
CITIES = ['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Multan', 'Peshawar', 'Quetta']
DEVICES = ['Mobile', 'Desktop', 'Tablet']
GENDERS = ['Male', 'Female', 'Other']

# Platform characteristic performance priors (CTR, CPC, CVR, ROAS multiplier)
PLATFORM_PRIORS = {
    'Google': {'ctr_mu': 0.042, 'cpc_mu': 35.0, 'cvr_mu': 0.075, 'roas_mu': 4.2},
    'Instagram': {'ctr_mu': 0.038, 'cpc_mu': 28.0, 'cvr_mu': 0.062, 'roas_mu': 3.6},
    'Facebook': {'ctr_mu': 0.025, 'cpc_mu': 22.0, 'cvr_mu': 0.048, 'roas_mu': 2.9},
    'YouTube': {'ctr_mu': 0.019, 'cpc_mu': 40.0, 'cvr_mu': 0.035, 'roas_mu': 2.7},
    'TikTok': {'ctr_mu': 0.045, 'cpc_mu': 18.0, 'cvr_mu': 0.041, 'roas_mu': 2.4},
}

def generate_advertising_data(n_records: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic, statistically coherent advertising dataset.
    Complies strictly with the 12-column schema required by the course specification:
    date, campaign, platform, impressions, clicks, spend, conversions, revenue, age, gender, city, device.
    """
    rng = np.random.default_rng(seed)
    
    # 1. Random categorical attributes
    platforms = rng.choice(AD_PLATFORMS, size=n_records)
    campaigns = rng.choice(CAMPAIGNS, size=n_records)
    cities = rng.choice(CITIES, size=n_records)
    devices = rng.choice(DEVICES, size=n_records, p=[0.75, 0.20, 0.05])
    genders = rng.choice(GENDERS, size=n_records, p=[0.52, 0.45, 0.03])
    ages = rng.integers(18, 65, size=n_records, dtype=np.uint8)
    
    # 2. Date distribution across 365 days leading to late 2026
    start_date = datetime(2025, 11, 1)
    day_offsets = rng.integers(0, 365, size=n_records)
    dates = [(start_date + timedelta(days=int(d))).strftime('%Y-%m-%d') for d in day_offsets]
    
    # 3. Numeric impressions
    impressions = rng.integers(200, 15000, size=n_records, dtype=np.uint32)
    
    # 4. Generate Clicks conditioned on platform priors + lognormal jitter
    clicks = np.zeros(n_records, dtype=np.uint32)
    spend = np.zeros(n_records, dtype=np.float64)
    conversions = np.zeros(n_records, dtype=np.uint32)
    revenue = np.zeros(n_records, dtype=np.float64)
    
    for plat, prior in PLATFORM_PRIORS.items():
        mask = (platforms == plat)
        cnt = np.sum(mask)
        if cnt == 0:
            continue
            
        imp_sub = impressions[mask]
        
        # CTR with lognormal variation
        ctr_draws = np.clip(rng.lognormal(mean=np.log(prior['ctr_mu']), sigma=0.25, size=cnt), 0.005, 0.15)
        raw_clicks = np.round(imp_sub * ctr_draws).astype(np.uint32)
        raw_clicks = np.clip(raw_clicks, 0, imp_sub)
        clicks[mask] = raw_clicks
        
        # Spend = Clicks * CPC
        cpc_draws = np.clip(rng.normal(loc=prior['cpc_mu'], scale=prior['cpc_mu'] * 0.2, size=cnt), 5.0, 150.0)
        spend_sub = np.round(raw_clicks * cpc_draws, 2)
        spend[mask] = spend_sub
        
        # Conversions = Clicks * CVR
        cvr_draws = np.clip(rng.lognormal(mean=np.log(prior['cvr_mu']), sigma=0.3, size=cnt), 0.005, 0.25)
        raw_conv = np.round(raw_clicks * cvr_draws).astype(np.uint32)
        raw_conv = np.clip(raw_conv, 0, raw_clicks)
        conversions[mask] = raw_conv
        
        # Revenue = Spend * ROAS + noise
        roas_draws = np.clip(rng.normal(loc=prior['roas_mu'], scale=prior['roas_mu'] * 0.25, size=cnt), 0.5, 12.0)
        # Boost revenue for actual conversions, flat base for zero conversions
        has_conv = (raw_conv > 0)
        rev_sub = np.zeros(cnt, dtype=np.float64)
        rev_sub[has_conv] = np.round(spend_sub[has_conv] * roas_draws[has_conv], 2)
        # 10% chance of high organic basket value
        jackpot = rng.random(cnt) < 0.05
        rev_sub[jackpot] += np.round(rng.uniform(5000, 25000, size=np.sum(jackpot)), 2)
        revenue[mask] = rev_sub
        
    # Zero-out spend for zero impressions
    zero_idx = (impressions == 0)
    clicks[zero_idx] = 0
    spend[zero_idx] = 0.0
    conversions[zero_idx] = 0
    revenue[zero_idx] = 0.0

    df = pd.DataFrame({
        'date': dates,
        'campaign': campaigns,
        'platform': platforms,
        'impressions': impressions,
        'clicks': clicks,
        'spend': spend,
        'conversions': conversions,
        'revenue': revenue,
        'age': ages,
        'gender': genders,
        'city': cities,
        'device': devices
    })
    return df
