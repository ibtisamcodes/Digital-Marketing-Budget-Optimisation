"""
Page 8: Digital Advertising Budget Optimizer.
Allocates user-entered advertising budget across platforms or campaigns.
Supports custom optimization objectives, selection subsets, and boundary constraints.
Guarantees exact budget conservation invariant: sum(allocations) == entered_budget.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.advertising_analytics import aggregate_by_platform, aggregate_by_campaign
from src.budget_optimizer import optimize_budget
from src.dataset_manager import get_bundled_advertising_sample

def render_page_budget_optimizer():
    st.title("Project B: Advertising Budget Optimizer")
    st.markdown("""
    Answers the core enterprise question: **"Where should we invest our advertising budget?"**  
    Reallocates capital based on empirical historical performance while enforcing strict diversification guardrails.
    """)
    st.divider()
    
    ad_df = st.session_state.get('advertising_df')
    if ad_df is None or ad_df.empty:
        st.warning("⚠️ No advertising dataset is currently loaded.")
        if st.button("📥 Load Bundled Advertising Sample (250 Records)"):
            sample = get_bundled_advertising_sample()
            if sample is not None:
                st.session_state['advertising_df'] = sample.copy()
                st.session_state['active_ad_name'] = "Bundled Multi-Channel Ad Telemetry"
                st.rerun()
        st.info("Or upload your dataset in **Dataset Management**.")
        return
        
    plat_df = aggregate_by_platform(ad_df)
    camp_df = aggregate_by_campaign(ad_df)
    
    # 1. User Controls & Inputs
    st.subheader("1. Optimization Parameters & Strategy Controls")
    
    pcol1, pcol2, pcol3 = st.columns(3)
    
    alloc_entity = pcol1.selectbox("Optimize Budget Across:", ["Platforms", "Campaigns"])
    entity_col = "platform" if alloc_entity == "Platforms" else "campaign"
    source_summary = plat_df if alloc_entity == "Platforms" else camp_df
    
    if source_summary.empty or entity_col not in source_summary.columns:
        st.error(f"Cannot optimize: '{entity_col}' not found in current dataset.")
        return
        
    available_entities = source_summary[entity_col].tolist()
    
    total_budget_input = pcol2.number_input(
        "Total Available Budget to Allocate (Rs.):",
        min_value=10000.0,
        max_value=100000000.0,
        value=1000000.0,
        step=50000.0
    )
    
    objective = pcol3.selectbox(
        "Optimization Objective:",
        ["Maximize ROAS", "Maximize Conversions", "Maximize Revenue", "Balanced (Composite)", "Equal Allocation"]
    )
    
    # Advanced constraint controls
    with st.expander("⚙️ Boundary Constraints & Channel Selection", expanded=True):
        ccol1, ccol2 = st.columns(2)
        selected_entities = ccol1.multiselect(
            f"Select {alloc_entity} to Include in Optimization:",
            options=available_entities,
            default=available_entities
        )
        if not selected_entities:
            st.error("Please select at least one channel/campaign.")
            return
            
        bcol1, bcol2 = ccol2.columns(2)
        min_pct = bcol1.slider("Minimum Allocation (%):", 0.0, 15.0, 5.0, step=1.0) / 100.0
        max_pct = bcol2.slider("Maximum Allocation (%):", 25.0, 70.0, 45.0, step=5.0) / 100.0
        
    # 2. Execute Optimizer
    alloc_df = optimize_budget(
        source_summary,
        total_budget=float(total_budget_input),
        entity_col=entity_col,
        objective=objective,
        selected_entities=selected_entities,
        min_pct=min_pct,
        max_pct=max_pct
    )
    st.session_state['alloc_df'] = alloc_df
    
    total_allocated = alloc_df['allocated_budget'].sum()
    expected_rev = alloc_df['projected_revenue'].sum()
    expected_conv = alloc_df['projected_conversions'].sum()
    projected_roas = expected_rev / max(total_allocated, 1.0)
    
    st.divider()
    
    # 3. KPI Outcome Cards
    st.subheader("2. Recommended Budget Allocation & Projected Outcomes")
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Budget Allocated", f"Rs. {total_allocated:,.2f}", "Invariant Enforced")
    r2.metric("Projected Total Revenue", f"Rs. {expected_rev:,.2f}", f"{projected_roas:.2f}x Projected ROAS")
    r3.metric("Projected Total Conversions", f"{expected_conv:,} Acquisitions", "Estimated Customer Volume")
    r4.metric("Strategy Applied", objective, f"Min {min_pct*100:.0f}% / Max {max_pct*100:.0f}%")
    
    # Allocation Table
    st.dataframe(alloc_df, use_container_width=True)
    
    # Visualizations
    vcol1, vcol2 = st.columns(2)
    with vcol1:
        fig_pie = px.pie(
            alloc_df,
            names=entity_col,
            values='allocated_budget',
            title=f"Capital Distribution ({objective})",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with vcol2:
        comp_df = pd.melt(
            alloc_df,
            id_vars=[entity_col],
            value_vars=['allocated_budget', 'projected_revenue'],
            var_name='Type',
            value_name='Amount PKR'
        )
        fig_bar = px.bar(
            comp_df,
            x=entity_col,
            y='Amount PKR',
            color='Type',
            barmode='group',
            title="Allocated Budget vs Projected Return (PKR)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.divider()
    
    # 4. Strategic Rationale & Assumptions
    st.subheader("3. Strategic Allocation Rationale & Model Assumptions")
    top_entity = alloc_df.iloc[0]
    st.info(f"""
    **Strategic Explanation:**
    - **Highest Allocation ({top_entity['allocation_pct']}% / Rs. {top_entity['allocated_budget']:,.2f})**: Awarded to **{top_entity[entity_col]}** because its historical performance ({top_entity['historical_roas']:.2f}x ROAS / Rs. {top_entity['historical_cpa']:.2f} CPA) provides the strongest mathematical alignment with the objective '{objective}'.
    - **Boundary Guarantees:** Channels are constrained between {min_pct*100:.1f}% and {max_pct*100:.1f}% to prevent single-channel dependency and avoid starving emerging touchpoints.
    - **Crucial Disclaimer:** Projected revenue and conversions are mathematical estimates derived from historical efficiency. Future outcomes are subject to ad fatigue, audience saturation, and market shifts.
    """)
    
    # Download report
    csv_bytes = alloc_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Budget Allocation Schedule (CSV)",
        data=csv_bytes,
        file_name="budget_allocation_recommendations.csv",
        mime="text/csv"
    )

