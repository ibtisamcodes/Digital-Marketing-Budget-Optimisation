"""
Page 4: YouTube Engagement & Text Insights.
Analyzes likes and reply distributions, Gini concentration, publication timelines,
and lexical keyword frequencies.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.statistics import calculate_descriptive_statistics
from src.text_temporal import analyze_temporal, STOPWORDS
from src.dataset_manager import get_bundled_youtube_sample
from collections import Counter
import re

def render_page_youtube_engagement():
    st.title("Project A: YouTube Engagement & Text Analytics")
    st.markdown("""
    Detailed parametric and non-parametric evaluation of comment engagement (likes and replies),
    temporal activity pacing, and lexical keyword frequencies.
    """)
    st.divider()
    
    clean_df = st.session_state.get('youtube_clean_df')
    if clean_df is None or clean_df.empty:
        st.warning("⚠️ No YouTube dataset is currently loaded.")
        if st.button("📥 Load Bundled YouTube Comments Sample"):
            sample = get_bundled_youtube_sample()
            if sample is not None:
                st.session_state['youtube_raw_df'] = sample.copy()
                st.session_state['youtube_clean_df'] = sample.copy()
                st.session_state['active_youtube_name'] = "Bundled Dual-Video YouTube Comments"
                st.rerun()
        st.info("Or upload your dataset in **Dataset Management**.")
        return
        
    stats = calculate_descriptive_statistics(clean_df)
    temp = analyze_temporal(clean_df)
    
    # 1. Engagement Summary Metrics
    st.subheader("1. Engagement Distribution & Inequality")
    
    likes_stat = stats.get('likes', {})
    rep_stat = stats.get('reply_count', {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Likes", f"{int(likes_stat.get('sum', 0)):,}", f"Mean: {likes_stat.get('mean', 0):.1f}")
    col2.metric("Max Likes on Comment", f"{int(likes_stat.get('max', 0)):,}")
    col3.metric("Gini Inequality (Likes)", f"{likes_stat.get('gini_coefficient', likes_stat.get('gini', 0)):.3f}", "0 = Equal, 1 = Monopolized")
    col4.metric("Top 1% Share of Likes", f"{likes_stat.get('top_1_pct_share', 0)}%", "Engagement Concentration")
    
    # Visualizations
    vcol1, vcol2 = st.columns(2)
    with vcol1:
        if 'likes' in clean_df.columns:
            fig_likes = px.histogram(
                clean_df[clean_df['likes'] > 0],
                x='likes',
                log_x=True,
                nbins=30,
                title="Thumbs-Up Likes Distribution (Log-Scale)",
                color_discrete_sequence=['#3498db']
            )
            st.plotly_chart(fig_likes, use_container_width=True)
            
    with vcol2:
        if 'reply_count' in clean_df.columns:
            fig_replies = px.histogram(
                clean_df[clean_df['reply_count'] > 0],
                x='reply_count',
                log_x=True,
                nbins=25,
                title="Comment Thread Reply Count Distribution (Log-Scale)",
                color_discrete_sequence=['#e67e22']
            )
            st.plotly_chart(fig_replies, use_container_width=True)
            
    st.divider()
    
    # 2. Most Engaged Comments
    st.subheader("2. Top Engaged Comments (Community Champions)")
    mcol1, mcol2 = st.columns(2)
    
    c_col = 'comment' if 'comment' in clean_df.columns else clean_df.columns[0]
    
    with mcol1:
        st.markdown("#### Most Liked Comments:")
        if 'likes' in clean_df.columns:
            top_liked = clean_df.sort_values(by='likes', ascending=False).head(5)
            for _, r in top_liked.iterrows():
                st.write(f"👍 **{r['likes']:,} Likes** — *{r.get('author', 'Viewer')}*")
                st.caption(f"\"{r[c_col]}\"")
                
    with mcol2:
        st.markdown("#### Most Discussed Comments (Top Replies):")
        if 'reply_count' in clean_df.columns:
            top_replied = clean_df.sort_values(by='reply_count', ascending=False).head(5)
            for _, r in top_replied.iterrows():
                st.write(f"💬 **{r['reply_count']:,} Replies** — *{r.get('author', 'Viewer')}*")
                st.caption(f"\"{r[c_col]}\"")
                
    st.divider()
    
    # 3. Temporal Pacing Analysis
    st.subheader("3. Temporal Pacing & Publication Activity")
    if temp:
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            yearly_data = pd.DataFrame(list(temp.get('yearly_counts', {}).items()), columns=['Year', 'Comments'])
            if not yearly_data.empty:
                fig_year = px.bar(yearly_data, x='Year', y='Comments', title="Comment Volume by Publication Year")
                st.plotly_chart(fig_year, use_container_width=True)
                
        with tcol2:
            dow_data = pd.DataFrame(list(temp.get('day_of_week_counts', {}).items()), columns=['Day', 'Comments'])
            if not dow_data.empty:
                fig_dow = px.bar(dow_data, x='Day', y='Comments', title="Comment Volume by Day of Week", color_discrete_sequence=['#2ecc71'])
                st.plotly_chart(fig_dow, use_container_width=True)
                
    st.divider()
    
    # 4. Lexical & Keyword Frequency
    st.subheader("4. Text Analytics & Lexical Keywords")
    
    # Extract top keywords
    all_text = " ".join(clean_df[c_col].dropna().astype(str).tolist()).lower()
    words = re.findall(r'\b[a-z]{3,}\b', all_text)
    filtered_words = [w for w in words if w not in STOPWORDS]
    top_words = Counter(filtered_words).most_common(20)
    
    if top_words:
        kw_df = pd.DataFrame(top_words, columns=['Keyword', 'Frequency'])
        fig_kw = px.bar(
            kw_df,
            x='Frequency',
            y='Keyword',
            orientation='h',
            title="Top 20 Frequently Occurring Keywords (Stopwords Excluded)",
            color='Frequency',
            color_continuous_scale='Blues'
        )
        fig_kw.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_kw, use_container_width=True)
