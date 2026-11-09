"""
Page 3: YouTube Comment Sentiment Analysis.
Performs lexicon-based sentiment classification on YouTube comments,
displays positive/negative/neutral distributions, and highlights top positive/negative comments.
Enforces explicit academic limitation disclaimers.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.sentiment_engine import analyze_youtube_sentiment
from src.dataset_manager import get_bundled_youtube_sample

def render_page_youtube_sentiment():
    st.title("Project A: YouTube Comment Sentiment Analysis")
    st.markdown("""
    Analyzes emotional tone across YouTube comments using **lexicon-based polarity scoring and negation handling**.
    Categorizes comments into **Positive, Negative, and Neutral** expressions.
    """)
    st.divider()
    
    clean_df = st.session_state.get('youtube_clean_df')
    if clean_df is None or clean_df.empty:
        st.warning("⚠️ No YouTube dataset is loaded in memory.")
        if st.button("📥 Load Bundled YouTube Comments Sample"):
            sample = get_bundled_youtube_sample()
            if sample is not None:
                st.session_state['youtube_raw_df'] = sample.copy()
                st.session_state['youtube_clean_df'] = sample.copy()
                st.session_state['active_youtube_name'] = "Bundled Dual-Video YouTube Comments"
                st.rerun()
        st.info("Or upload your dataset in **Dataset Management**.")
        return
        
    c_col = 'comment' if 'comment' in clean_df.columns else clean_df.columns[0]
    
    with st.spinner("Classifying comment sentiment..."):
        sent_df, summary = analyze_youtube_sentiment(clean_df, comment_col=c_col)
        
    # KPI metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Analyzed Comments", f"{summary['total_comments']:,}")
    col2.metric("Positive Sentiment", f"{summary['positive_pct']}%", f"{summary['positive_count']:,} comments")
    col3.metric("Neutral Sentiment", f"{summary['neutral_pct']}%", f"{summary['neutral_count']:,} comments")
    col4.metric("Negative Sentiment", f"{summary['negative_pct']}%", f"{summary['negative_count']:,} comments")
    
    st.divider()
    
    st.subheader("1. Sentiment Distribution Visualizations")
    vcol1, vcol2 = st.columns(2)
    
    with vcol1:
        dist_df = pd.DataFrame({
            'Sentiment': ['Positive', 'Neutral', 'Negative'],
            'Count': [summary['positive_count'], summary['neutral_count'], summary['negative_count']],
            'Percentage': [summary['positive_pct'], summary['neutral_pct'], summary['negative_pct']]
        })
        fig_bar = px.bar(
            dist_df,
            x='Sentiment',
            y='Count',
            color='Sentiment',
            text='Percentage',
            color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#f1c40f', 'Negative': '#e74c3c'},
            title="Sentiment Breakdown (Volume & Percentage)"
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with vcol2:
        fig_pie = px.pie(
            dist_df,
            names='Sentiment',
            values='Count',
            hole=0.4,
            color='Sentiment',
            color_discrete_map={'Positive': '#2ecc71', 'Neutral': '#f1c40f', 'Negative': '#e74c3c'},
            title="Share of Voice (% Share)"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.divider()
    
    st.subheader("2. High-Engagement Sentiment Highlights")
    hcol1, hcol2 = st.columns(2)
    
    with hcol1:
        st.markdown("#### Top Positive Comments:")
        pos_subset = sent_df[sent_df['sentiment'] == 'Positive'].sort_values(by='likes', ascending=False).head(4) if 'likes' in sent_df.columns else sent_df[sent_df['sentiment'] == 'Positive'].head(4)
        for _, r in pos_subset.iterrows():
            likes_str = f" (👍 {r['likes']:,} likes)" if 'likes' in r else ""
            st.success(f"**{r.get('author', 'Viewer')}**{likes_str}:  \n\"{r[c_col]}\"  \n*Polarity: +{r['polarity']:.2f}*")
            
    with hcol2:
        st.markdown("#### High-Visibility Critical/Negative Comments:")
        neg_subset = sent_df[sent_df['sentiment'] == 'Negative'].sort_values(by='likes', ascending=False).head(4) if 'likes' in sent_df.columns else sent_df[sent_df['sentiment'] == 'Negative'].head(4)
        if not neg_subset.empty:
            for _, r in neg_subset.iterrows():
                likes_str = f" (👍 {r['likes']:,} likes)" if 'likes' in r else ""
                st.error(f"**{r.get('author', 'Viewer')}**{likes_str}:  \n\"{r[c_col]}\"  \n*Polarity: {r['polarity']:.2f}*")
        else:
            st.info("No strongly negative comments found in this dataset.")
            
    st.divider()
    
    st.subheader("3. Interactive Sentiment Filter & Review Table")
    selected_label = st.selectbox("Filter Comments by Sentiment:", ['All', 'Positive', 'Neutral', 'Negative'])
    search_q = st.text_input("Search Comments for Specific Keywords:", "")
    
    filtered_df = sent_df.copy()
    if selected_label != 'All':
        filtered_df = filtered_df[filtered_df['sentiment'] == selected_label]
    if search_q:
        filtered_df = filtered_df[filtered_df[c_col].str.lower().str.contains(search_q.lower(), na=False)]
        
    display_cols = [col for col in ['author', c_col, 'sentiment', 'polarity', 'likes', 'reply_count', 'published_at'] if col in filtered_df.columns]
    st.write(f"Showing **{len(filtered_df):,} matching comments**:")
    st.dataframe(filtered_df[display_cols], use_container_width=True)
    
    st.divider()
    
    st.info("""
    🛡️ **Academic Methodology & Limitations Disclosure:**
    - **Classification Model:** Rule-based lexical matching augmented with negation inversion.
    - **Important Disclaimer:** Sentiment predictions are algorithmic approximations and must not be treated as absolute ground truth. Sarcasm, emojis, and multilingual colloquialisms (e.g. Hinglish / Roman Urdu) may exhibit classification variance.
    """)

