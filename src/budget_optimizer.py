"""
Advertising Budget Optimizer Engine.
Solves capital allocation across user-selected advertising platforms or campaigns.
Supports custom total budgets, objective functions, and boundary constraints.
Guarantees exact budget conservation invariant: sum(allocations) == entered_budget.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.advertising_analytics import safe_divide, aggregate_by_platform

def enforce_budget_constraints(raw_weights: Dict[str, float],
                               total_budget: float,
                               min_pct: float = 0.05,
                               max_pct: float = 0.45) -> Dict[str, float]:
    """
    Applies lower and upper bounding constraints using iterative projection
    while guaranteeing that sum(allocations) == total_budget exactly.
    """
    items = list(raw_weights.keys())
    n = len(items)
    if n == 0 or total_budget <= 0:
        return {}
    if n == 1:
        return {items[0]: round(total_budget, 2)}
        
    min_pct = max(0.0, min(min_pct, 1.0 / n))
    max_pct = max(min_pct, min(max_pct, 1.0))
    min_val = total_budget * min_pct
    max_val = total_budget * max_pct
    
    total_w = sum(max(w, 1e-6) for w in raw_weights.values())
    alloc = {p: (max(raw_weights[p], 1e-6) / total_w) * total_budget for p in items}
    
    for _ in range(60):
        clipped = False
        excess = 0.0
        free_weight = 0.0
        free_items = []
        
        for p in items:
            if alloc[p] < min_val:
                excess += (min_val - alloc[p])
                alloc[p] = min_val
                clipped = True
            elif alloc[p] > max_val:
                excess -= (alloc[p] - max_val)
                alloc[p] = max_val
                clipped = True
            else:
                free_items.append(p)
                free_weight += max(raw_weights[p], 1e-6)
                
        if not clipped or abs(excess) < 1e-5:
            break
            
        if free_weight > 0 and free_items:
            for p in free_items:
                alloc[p] -= excess * (max(raw_weights[p], 1e-6) / free_weight)
        else:
            break

    rounded_alloc = {p: round(alloc[p], 2) for p in items}
    drift = round(total_budget - sum(rounded_alloc.values()), 2)
    sort_p = sorted(items, key=lambda k: raw_weights[k], reverse=True)
    rounded_alloc[sort_p[0]] = round(rounded_alloc[sort_p[0]] + drift, 2)
    
    return rounded_alloc


def optimize_budget(summary_df: pd.DataFrame,
                    total_budget: float = 1_000_000.0,
                    entity_col: str = 'platform',
                    objective: str = 'Maximize ROAS',
                    selected_entities: Optional[List[str]] = None,
                    min_pct: float = 0.05,
                    max_pct: float = 0.45) -> pd.DataFrame:
    """
    Allocates entered total budget across selected entities based on historical performance.
    
    Objectives:
    - 'Maximize ROAS': Proportional to historical Return on Ad Spend.
    - 'Maximize Conversions': Inversely proportional to CPA (lower acquisition cost gets higher weight).
    - 'Maximize Revenue': Proportional to revenue generation capacity.
    - 'Balanced (Composite)': Balances ROAS (40%), CVR (25%), CTR (20%), and CPA efficiency (15%).
    - 'Equal Allocation': Uniform split.
    """
    df = summary_df.copy()
    if entity_col not in df.columns:
        raise ValueError(f"Entity column '{entity_col}' not found in summary DataFrame.")
        
    if selected_entities:
        df = df[df[entity_col].isin(selected_entities)].reset_index(drop=True)
        
    if df.empty:
        return pd.DataFrame()
        
    entities = df[entity_col].tolist()
    
    # Extract historical metrics safely
    roas_map = dict(zip(df[entity_col], df['ROAS'].fillna(1.0).clip(lower=0.1))) if 'ROAS' in df.columns else {e: 1.0 for e in entities}
    cpa_map = dict(zip(df[entity_col], df['CPA'].fillna(50.0).clip(lower=1.0))) if 'CPA' in df.columns else {e: 50.0 for e in entities}
    ctr_map = dict(zip(df[entity_col], df['CTR'].fillna(1.0).clip(lower=0.1))) if 'CTR' in df.columns else {e: 1.0 for e in entities}
    cvr_map = dict(zip(df[entity_col], df['CVR'].fillna(1.0).clip(lower=0.1))) if 'CVR' in df.columns else {e: 1.0 for e in entities}
    rev_map = dict(zip(df[entity_col], df['revenue'].fillna(100.0).clip(lower=1.0))) if 'revenue' in df.columns else {e: 100.0 for e in entities}
    
    raw_weights = {}
    
    if objective == 'Equal Allocation':
        raw_weights = {e: 1.0 for e in entities}
    elif objective == 'Maximize ROAS':
        raw_weights = {e: max(roas_map.get(e, 1.0), 0.1) for e in entities}
    elif objective == 'Maximize Conversions':
        raw_weights = {e: (1.0 / max(cpa_map.get(e, 50.0), 1.0)) for e in entities}
    elif objective == 'Maximize Revenue':
        raw_weights = {e: max(rev_map.get(e, 1.0), 1.0) for e in entities}
    else:  # Balanced Composite
        max_roas = max(roas_map.values()) if max(roas_map.values()) > 0 else 1.0
        max_cvr = max(cvr_map.values()) if max(cvr_map.values()) > 0 else 1.0
        max_ctr = max(ctr_map.values()) if max(ctr_map.values()) > 0 else 1.0
        min_cpa = min(cpa_map.values()) if min(cpa_map.values()) > 0 else 1.0
        
        for e in entities:
            norm_roas = roas_map[e] / max_roas
            norm_cvr = cvr_map[e] / max_cvr
            norm_ctr = ctr_map[e] / max_ctr
            cpa_eff = min_cpa / max(cpa_map[e], 1e-3)
            raw_weights[e] = max((0.40 * norm_roas) + (0.25 * norm_cvr) + (0.20 * norm_ctr) + (0.15 * cpa_eff), 0.05)
            
    allocations = enforce_budget_constraints(raw_weights, total_budget, min_pct, max_pct)
    
    results = []
    for e in entities:
        amt = allocations[e]
        pct = (amt / max(total_budget, 1.0)) * 100.0
        e_roas = roas_map.get(e, 1.0)
        e_cpa = cpa_map.get(e, 50.0)
        
        exp_rev = amt * e_roas
        exp_conv = (amt / e_cpa) if e_cpa > 0 else 0
        
        results.append({
            entity_col: e,
            'historical_roas': round(e_roas, 2),
            'historical_cpa': round(e_cpa, 2),
            'historical_ctr': round(ctr_map.get(e, 0.0), 2),
            'allocation_pct': round(pct, 2),
            'allocated_budget': amt,
            'projected_revenue': round(exp_rev, 2),
            'projected_conversions': int(round(exp_conv))
        })
        
    res_df = pd.DataFrame(results)
    diff = round(total_budget - res_df['allocated_budget'].sum(), 2)
    if diff != 0 and len(res_df) > 0:
        res_df.loc[0, 'allocated_budget'] += diff
        res_df.loc[0, 'allocation_pct'] = round((res_df.loc[0, 'allocated_budget'] / total_budget) * 100.0, 2)
        
    return res_df.sort_values(by='allocated_budget', ascending=False).reset_index(drop=True)
