"""
Test Suite for Project B: Advertising Budget Optimizer.
Verifies exact budget conservation, boundary constraints, no negative allocations,
and handling of custom budget amounts and small/single-entity datasets.
"""

import pytest
import numpy as np
import pandas as pd

from src.budget_optimizer import optimize_budget, enforce_budget_constraints

@pytest.fixture
def summary_data():
    return pd.DataFrame([
        {'platform': 'Google', 'spend': 10000.0, 'revenue': 42000.0, 'conversions': 100, 'ROAS': 4.2, 'CPA': 100.0, 'CTR': 4.5, 'CVR': 8.0},
        {'platform': 'Instagram', 'spend': 12000.0, 'revenue': 38000.0, 'conversions': 85, 'ROAS': 3.17, 'CPA': 141.18, 'CTR': 3.8, 'CVR': 6.5},
        {'platform': 'Facebook', 'spend': 8000.0, 'revenue': 22000.0, 'conversions': 55, 'ROAS': 2.75, 'CPA': 145.45, 'CTR': 2.4, 'CVR': 5.0},
        {'platform': 'TikTok', 'spend': 6000.0, 'revenue': 13000.0, 'conversions': 45, 'ROAS': 2.17, 'CPA': 133.33, 'CTR': 4.8, 'CVR': 4.0}
    ])

def test_custom_budget_conservation(summary_data):
    for budget in [50_000.0, 500_000.0, 1_000_000.0, 2_500_000.0]:
        res = optimize_budget(summary_data, total_budget=budget, objective='Maximize ROAS')
        assert np.isclose(res['allocated_budget'].sum(), budget, atol=0.05)
        assert (res['allocated_budget'] >= 0.0).all()

def test_all_optimization_objectives(summary_data):
    objectives = [
        "Maximize ROAS",
        "Maximize Conversions",
        "Maximize Revenue",
        "Balanced (Composite)",
        "Equal Allocation"
    ]
    for obj in objectives:
        res = optimize_budget(summary_data, total_budget=1_000_000.0, objective=obj)
        assert np.isclose(res['allocated_budget'].sum(), 1_000_000.0, atol=0.05)
        assert len(res) == 4

def test_min_and_max_constraints_enforced(summary_data):
    min_pct = 0.10  # 10% = Rs. 100,000
    max_pct = 0.40  # 40% = Rs. 400,000
    res = optimize_budget(
        summary_data,
        total_budget=1_000_000.0,
        objective='Maximize ROAS',
        min_pct=min_pct,
        max_pct=max_pct
    )
    assert np.isclose(res['allocated_budget'].sum(), 1_000_000.0, atol=0.05)
    for amt in res['allocated_budget']:
        assert amt >= 99_999.0, f"Violated minimum bound: {amt}"
        assert amt <= 400_001.0, f"Violated maximum bound: {amt}"

def test_single_platform_handling():
    single_df = pd.DataFrame([{'platform': 'Google', 'spend': 1000.0, 'revenue': 4000.0, 'ROAS': 4.0, 'CPA': 50.0}])
    res = optimize_budget(single_df, total_budget=300_000.0)
    assert len(res) == 1
    assert np.isclose(res['allocated_budget'].iloc[0], 300_000.0)

def test_insufficient_or_empty_data():
    empty_df = pd.DataFrame(columns=['platform', 'spend', 'revenue', 'ROAS'])
    res = optimize_budget(empty_df, total_budget=100_000.0)
    assert res.empty

