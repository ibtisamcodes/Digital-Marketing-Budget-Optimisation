"""
Page 10: SQLite Database Explorer & Analytical View Inspector.
Allows users to explore relational tables, inspect schema, execute parameterized queries,
and view compiled SQL views without requiring external database servers.
"""

import streamlit as st
import pandas as pd
import sqlite3
import os

from src.database import get_database_status, query_view, init_database, get_connection, DB_PATH

def render_page_database_explorer():
    st.title("Database Explorer & SQLite Management")
    st.markdown("""
    Explore the embedded relational database (`data/marketing_intelligence.db`).  
    All queries execute locally using **parameterized SQL** in **SQLite 3 WAL mode** without external servers.
    """)
    st.divider()
    
    # 1. Database Status
    status = get_database_status()
    st.subheader("1. Relational Database Engine Status")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Database Storage", "SQLite 3 (Embedded)", "WAL Mode")
    col2.metric("File Size", f"{status.get('size_kb', 0):.1f} KB", os.path.basename(DB_PATH))
    col3.metric("Ad Records in DB", f"{status.get('tables', {}).get('advertising_campaigns', 0):,}")
    col4.metric("YouTube Records in DB", f"{status.get('tables', {}).get('youtube_comments', 0):,}")
    
    st.divider()
    
    # 2. Analytical SQL Views
    st.subheader("2. Pre-Compiled Analytical SQL Views")
    st.write("Analytical views compute macro performance KPIs directly within SQL using zero-division protection:")
    
    view_options = ["view_platform_kpis", "view_campaign_performance", "view_youtube_engagement_summary"]
    selected_view = st.selectbox("Select Analytical SQL View to Query:", view_options)
    
    try:
        view_df = query_view(selected_view)
        st.dataframe(view_df, use_container_width=True)
        
        csv_bytes = view_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Download {selected_view} as CSV",
            data=csv_bytes,
            file_name=f"{selected_view}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error querying view: {str(e)}")
        
    st.divider()
    
    # 3. Parameterized Safe SQL Query Sandbox
    st.subheader("3. Parameterized SQL Query Runner")
    st.caption("Execute SELECT queries safely against tables: `advertising_campaigns`, `benchmark_records`, `budget_optimizations`.")
    
    query_input = st.text_area(
        "SQL Query (Read-Only SELECT):",
        value="SELECT platform, SUM(impressions) as total_imp, SUM(clicks) as total_clicks, ROUND(SUM(spend), 2) as total_spend FROM advertising_campaigns GROUP BY platform ORDER BY total_spend DESC LIMIT 10;",
        height=100
    )
    
    if st.button("▶️ Execute Safe Query"):
        clean_q = query_input.strip()
        if not clean_q.lower().startswith("select"):
            st.error("Security Restriction: Only read-only SELECT queries are permitted in the Explorer.")
        else:
            try:
                conn = get_connection()
                res_df = pd.read_sql_query(clean_q, conn)
                conn.close()
                st.write(f"Returned **{len(res_df):,} rows**:")
                st.dataframe(res_df, use_container_width=True)
            except Exception as qex:
                st.error(f"Query Execution Error: {str(qex)}")
                
    st.divider()
    
    # 4. Database Maintenance
    st.subheader("4. Database Maintenance Operations")
    if st.button("🔄 Sync / Re-initialize SQLite Tables and Views"):
        init_database()
        st.success("SQLite database initialized and analytical views verified!")

