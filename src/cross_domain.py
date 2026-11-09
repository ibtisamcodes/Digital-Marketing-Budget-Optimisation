"""
Unified Marketing Insights & Dual-Project Analytics Assistant.
Integrates Project A (YouTube Organic Audience Signals) with Project B (Paid Advertising Telemetry).

Academic Notice:
YouTube comments and paid advertising conversions represent separate, distinct data sources.
All cross-domain comparisons are strictly descriptive and qualitative.
The platform explicitly enforces non-causal attribution boundaries.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.advertising_analytics import compute_portfolio_macro_summary, aggregate_by_platform, aggregate_by_campaign
from src.sentiment_engine import analyze_youtube_sentiment

def generate_unified_marketing_insights(youtube_df: Optional[pd.DataFrame] = None,
                                        ad_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Generates a descriptive, non-causal synthesis connecting organic YouTube audience
    reception with paid advertising efficiency.
    """
    insights = {
        'has_youtube': youtube_df is not None and not youtube_df.empty,
        'has_advertising': ad_df is not None and not ad_df.empty,
        'youtube_summary': {},
        'advertising_summary': {},
        'comparative_themes': [],
        'methodological_safeguards': [
            "Descriptive Independence: Organic YouTube audience comments and paid advertising conversions represent separate data streams.",
            "Non-Causal Distinction: No direct micro-level causality is claimed between individual viewer comments and ad conversion events.",
            "Qualitative Synergy: High organic resonance (likes, positive sentiment) indicates creative themes suitable for paid media creative concepts."
        ]
    }
    
    if insights['has_youtube']:
        c_col = 'comment' if 'comment' in youtube_df.columns else youtube_df.columns[0]
        _, sent_summary = analyze_youtube_sentiment(youtube_df, comment_col=c_col)
        total_likes = int(youtube_df['likes'].sum()) if 'likes' in youtube_df.columns else 0
        total_replies = int(youtube_df['reply_count'].sum()) if 'reply_count' in youtube_df.columns else 0
        
        insights['youtube_summary'] = {
            'total_comments': len(youtube_df),
            'positive_pct': sent_summary['positive_pct'],
            'negative_pct': sent_summary['negative_pct'],
            'neutral_pct': sent_summary['neutral_pct'],
            'total_likes': total_likes,
            'total_replies': total_replies
        }
        
    if insights['has_advertising']:
        macro = compute_portfolio_macro_summary(ad_df)
        plat_df = aggregate_by_platform(ad_df)
        best_plat = plat_df.iloc[0]['platform'] if not plat_df.empty and 'platform' in plat_df.columns else "N/A"
        
        insights['advertising_summary'] = {
            'total_spend': macro['total_spend'],
            'total_revenue': macro['total_revenue'],
            'macro_roas': macro['macro_roas'],
            'macro_ctr': macro['macro_ctr'],
            'macro_cpa': macro['macro_cpa'],
            'top_platform': best_plat
        }
        
    if insights['has_youtube'] and insights['has_advertising']:
        insights['comparative_themes'] = [
            {
                'channel': 'YouTube Platform',
                'organic_signal': f"{insights['youtube_summary']['positive_pct']}% Positive sentiment across {insights['youtube_summary']['total_comments']:,} organic comments.",
                'paid_ad_role': f"Delivers paid reach with macro ROAS of {insights['advertising_summary']['macro_roas']:.2f}x.",
                'strategic_implication': "Strong organic video affinity can be amplified with paid video view retargeting."
            },
            {
                'channel': 'Multi-Channel Synthesis',
                'organic_signal': f"{insights['youtube_summary']['total_likes']:,} organic thumbs-up engagements.",
                'paid_ad_role': f"Rs. {insights['advertising_summary']['total_spend']:,.0f} invested across paid performance channels.",
                'strategic_implication': "Use top recurring audience keywords as creative search terms and ad headlines on Google and Meta."
            }
        ]
        
    return insights


def answer_analytics_assistant_query(query: str,
                                    youtube_df: Optional[pd.DataFrame] = None,
                                    ad_df: Optional[pd.DataFrame] = None,
                                    alloc_df: Optional[pd.DataFrame] = None,
                                    benchmark_df: Optional[pd.DataFrame] = None) -> str:
    """
    Deterministic Analytics Assistant answering inquiries across both Project A and Project B.
    Grounds answers strictly on active data state without external API dependencies.
    """
    q = query.lower()
    
    # 1. Advertising ROAS / Best Platform
    if 'roas' in q or 'return on ad spend' in q or 'best platform' in q:
        if ad_df is None or ad_df.empty:
            return "No advertising dataset is currently loaded. Please upload an advertising dataset or load the sample data in Dataset Management."
        plat_df = aggregate_by_platform(ad_df)
        if plat_df.empty or 'ROAS' not in plat_df.columns:
            return "Unable to calculate ROAS from the loaded advertising dataset (missing spend or revenue columns)."
        best = plat_df.iloc[0]
        return (
            f"**Highest ROAS Platform:**\n\n"
            f"**{best['platform']}** leads with a ROAS of **{best['ROAS']:.2f}x** "
            f"(Total Revenue: Rs. {best.get('revenue', 0):,.2f} on Rs. {best.get('spend', 0):,.2f} spend).\n\n"
            f"*Summary Ranking:*\n" +
            "\n".join([f"- {r['platform']}: {r['ROAS']:.2f}x ROAS" for _, r in plat_df.iterrows() if pd.notna(r.get('ROAS'))])
        )
        
    # 2. CPA / Lowest Cost per Conversion
    elif 'cpa' in q or 'cost per acquisition' in q or 'cheapest' in q or 'lowest cpa' in q:
        if ad_df is None or ad_df.empty:
            return "No advertising dataset is currently loaded."
        plat_df = aggregate_by_platform(ad_df)
        if plat_df.empty or 'CPA' not in plat_df.columns:
            return "Unable to calculate CPA (missing spend or conversions data)."
        valid_cpa = plat_df.dropna(subset=['CPA']).sort_values(by='CPA', ascending=True)
        if valid_cpa.empty:
            return "CPA cannot be calculated (zero or missing conversions)."
        cheapest = valid_cpa.iloc[0]
        return (
            f"**Lowest CPA Channel:**\n\n"
            f"**{cheapest['platform']}** delivers the lowest customer acquisition cost at **Rs. {cheapest['CPA']:.2f} per conversion**.\n\n"
            f"*Platform CPA Overview:*\n" +
            "\n".join([f"- {r['platform']}: Rs. {r['CPA']:.2f}" for _, r in valid_cpa.iterrows()])
        )
        
    # 3. Budget Recommendation
    elif 'budget' in q or 'allocation' in q or 'where should we spend' in q or '1 million' in q:
        if alloc_df is None or alloc_df.empty:
            return "Please run the Advertising Budget Optimizer page to generate a specific allocation model, or load the advertising dataset."
        total = alloc_df['allocated_budget'].sum()
        alloc_lines = "\n".join([
            f"- **{r.iloc[0]}**: Rs. {r['allocated_budget']:,.2f} ({r['allocation_pct']}%) -> Projected Revenue: Rs. {r['projected_revenue']:,.2f}"
            for _, r in alloc_df.iterrows()
        ])
        return (
            f"### Recommended Budget Allocation (Total: Rs. {total:,.2f})\n\n"
            f"{alloc_lines}\n\n"
            f"**Total Projected Return:** Rs. {alloc_df['projected_revenue'].sum():,.2f} "
            f"({alloc_df['projected_conversions'].sum():,} estimated conversions).\n"
            f"*Constraint Invariant:* 100% of the requested budget is allocated without negative distributions."
        )
        
    # 4. YouTube Sentiment Distribution
    elif 'sentiment' in q or 'positive' in q or 'negative' in q:
        if youtube_df is None or youtube_df.empty:
            return "No YouTube comment dataset is currently loaded. Please load or upload YouTube comments in Dataset Management."
        c_col = 'comment' if 'comment' in youtube_df.columns else youtube_df.columns[0]
        _, sent_summary = analyze_youtube_sentiment(youtube_df, comment_col=c_col)
        return (
            f"### YouTube Comment Sentiment Distribution\n\n"
            f"- **Total Comments Analyzed:** {sent_summary['total_comments']:,}\n"
            f"- **Positive Sentiment:** {sent_summary['positive_pct']}% ({sent_summary['positive_count']:,} comments)\n"
            f"- **Neutral Sentiment:** {sent_summary['neutral_pct']}% ({sent_summary['neutral_count']:,} comments)\n"
            f"- **Negative Sentiment:** {sent_summary['negative_pct']}% ({sent_summary['negative_count']:,} comments)\n\n"
            f"*Method:* {sent_summary['method']} (Approximation model)."
        )
        
    # 5. YouTube Engagement
    elif 'engagement' in q or 'liked' in q or 'likes' in q or 'reply' in q or 'popular' in q:
        if youtube_df is None or youtube_df.empty:
            return "No YouTube comment dataset is currently loaded."
        if 'likes' not in youtube_df.columns:
            return "The loaded YouTube dataset does not contain a 'likes' engagement column."
        top_likes = youtube_df.sort_values(by='likes', ascending=False).head(3)
        comment_col = 'comment' if 'comment' in youtube_df.columns else youtube_df.columns[0]
        author_col = 'author' if 'author' in youtube_df.columns else None
        
        lines = []
        for _, r in top_likes.iterrows():
            auth = f" by {r[author_col]}" if author_col else ""
            lines.append(f"- **{r['likes']:,} Likes**{auth}: \"{str(r[comment_col])[:80]}...\"")
        return (
            f"### Top Engaged YouTube Comments\n\n" +
            "\n".join(lines) +
            f"\n\n*Total Likes across dataset:* {youtube_df['likes'].sum():,}"
        )
        
    # 6. Big Data Engine Benchmarks
    elif 'engine' in q or 'fastest' in q or 'benchmark' in q or 'mapreduce' in q or 'spark' in q:
        if benchmark_df is None or benchmark_df.empty:
            return "No benchmark runs have been recorded yet in this session. Visit the Big Data Processing Lab to execute a benchmark."
        stat_col = 'Status' if 'Status' in benchmark_df.columns else ('status' if 'status' in benchmark_df.columns else None)
        valid = benchmark_df[benchmark_df[stat_col] == 'PASS'] if stat_col else benchmark_df
        time_col = 'Execution Time (s)' if 'Execution Time (s)' in benchmark_df.columns else ('execution_time_sec' if 'execution_time_sec' in benchmark_df.columns else None)
        engine_col = 'Engine' if 'Engine' in benchmark_df.columns else ('engine' if 'engine' in benchmark_df.columns else benchmark_df.columns[0])
        
        if valid.empty or not time_col:
            return "Benchmark runs recorded were diagnostics or unavailable."
        valid = valid.sort_values(by=time_col, ascending=True)
        fastest = valid.iloc[0]
        rec_col = 'Records Processed' if 'Records Processed' in fastest else ('actual_records' if 'actual_records' in fastest else None)
        rec_val = f" on {fastest[rec_col]:,} rows" if rec_col else ""
        tp_col = 'Throughput (Rec/Sec)' if 'Throughput (Rec/Sec)' in fastest else ('throughput_rec_sec' if 'throughput_rec_sec' in fastest else None)
        tp_val = f" ({fastest[tp_col]:,.0f} records/sec)" if tp_col else ""
        
        return (
            f"**Processing Engine Benchmark Finding:**\n\n"
            f"**{fastest[engine_col]}** completed the operation fastest in **{fastest[time_col]:.4f} seconds**"
            f"{tp_val}{rec_val}.\n\n"
            f"*Engine Summary:*\n" +
            "\n".join([f"- {r[engine_col]}: {r[time_col]:.4f}s" for _, r in valid.iterrows()])
        )
        
    else:
        return (
            f"### Unified Analytics Assistant Active\n"
            f"- Loaded YouTube Records: {len(youtube_df) if youtube_df is not None else 0:,}\n"
            f"- Loaded Advertising Records: {len(ad_df) if ad_df is not None else 0:,}\n\n"
            f"You can ask me:\n"
            f"1. *'Which advertising platform has the highest ROAS?'*\n"
            f"2. *'What is our lowest CPA acquisition channel?'*\n"
            f"3. *'What is the YouTube sentiment distribution?'*\n"
            f"4. *'Which comments received the highest likes and engagement?'*\n"
            f"5. *'What is the recommended budget allocation?'*\n"
            f"6. *'Which processing engine ran the fastest?'*"
        )
