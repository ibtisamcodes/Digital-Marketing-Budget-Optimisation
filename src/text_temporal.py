"""
Temporal and Text Analysis Module for YouTube Comments.
Examines publication timelines, engagement pacing, comment length, and vocabulary.
"""

from collections import Counter
import re
from typing import Any
import pandas as pd


# Common English and Hinglish/Hindi stopwords to filter for clean lexical analysis
STOPWORDS = {
    "the", "and", "is", "in", "to", "of", "a", "it", "this", "that", "i", "you",
    "for", "on", "my", "with", "me", "song", "very", "are", "so", "at", "be",
    "was", "have", "has", "he", "she", "but", "not", "from", "by", "all", "we",
    "they", "will", "do", "no", "or", "an", "what", "who", "which", "there",
    "just", "like", "one", "can", "if", "out", "up", "about", "your", "as",
    "ki", "ka", "ke", "ko", "hai", "bhi", "ho", "se", "ye", "yeh", "kya", "toh",
    "ab", "aur", "tha", "thi", "the", "mai", "main", "par", "kar", "kare",
    "after", "watching", "still", "when", "how", "why", "their", "its", "into"
}


def analyze_temporal(df: pd.DataFrame) -> dict[str, Any]:
    """
    Analyzes comment publication timestamps.
    """
    if "published_at" not in df.columns:
        return {}

    dt_series = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    valid_dt = dt_series.dropna()

    if valid_dt.empty:
        return {}

    earliest = valid_dt.min()
    latest = valid_dt.max()
    span_days = round((latest - earliest).total_seconds() / 86400.0, 1)

    # Yearly breakdown
    yearly_counts = valid_dt.dt.year.value_counts().sort_index().to_dict()
    yearly_dict = {str(k): int(v) for k, v in yearly_counts.items()}

    # Day of week breakdown (0=Monday, 6=Sunday)
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_counts = valid_dt.dt.day_of_week.value_counts().sort_index().to_dict()
    dow_dict = {day_names[k]: int(dow_counts.get(k, 0)) for k in range(7)}

    # Hour of day breakdown (UTC)
    hour_counts = valid_dt.dt.hour.value_counts().sort_index().to_dict()
    hour_dict = {f"{h:02d}:00": int(hour_counts.get(h, 0)) for h in range(24)}

    # Longitudinal era categorization
    launch_era_2016 = int((valid_dt.dt.year == 2016).sum())
    catalog_era_2017_2024 = int(((valid_dt.dt.year >= 2017) & (valid_dt.dt.year <= 2024)).sum())
    resurgence_era_2025_2026 = int((valid_dt.dt.year >= 2025).sum())

    return {
        "earliest_comment_utc": earliest.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "latest_comment_utc": latest.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_span_days": span_days,
        "yearly_distribution": yearly_dict,
        "day_of_week_distribution": dow_dict,
        "hour_of_day_distribution_utc": hour_dict,
        "era_breakdown": {
            "launch_window_2016": launch_era_2016,
            "catalog_tail_2017_2024": catalog_era_2017_2024,
            "resurgence_phase_2025_2026": resurgence_era_2025_2026,
            "resurgence_share_pct": round(resurgence_era_2025_2026 / len(valid_dt) * 100, 2),
        },
    }


def analyze_text(df: pd.DataFrame) -> dict[str, Any]:
    """
    Analyzes lexical features, comment length, and domain keywords.
    """
    if "comment" not in df.columns:
        return {}

    comments = df["comment"].dropna().astype(str)
    total_comments = len(comments)

    char_lengths = comments.str.len()
    word_counts = comments.apply(lambda text: len(text.split()))

    # Punctuation and emoji expressions
    has_question = int(comments.str.contains(r"\?", regex=True).sum())
    has_exclamation = int(comments.str.contains(r"!", regex=True).sum())
    has_emoji = int(comments.apply(lambda s: bool(re.search(r"[\U00010000-\U0010ffff]", s))).sum())

    # Token frequency extraction
    tokens = []
    for comment in comments:
        clean_str = re.sub(r"[^\w\s]", " ", comment.lower())
        words = [w for w in clean_str.split() if len(w) > 2 and w not in STOPWORDS and not w.isdigit()]
        tokens.extend(words)

    word_freq = Counter(tokens).most_common(25)

    # Thematic entity mentions
    lower_comments = comments.str.lower()
    thematic_mentions = {
        "kareena_kapoor": int(lower_comments.str.contains(r"kareena|bebo", regex=True).sum()),
        "honey_singh": int(lower_comments.str.contains(r"honey\s*singh|yo\s*yo", regex=True).sum()),
        "arjun_kapoor": int(lower_comments.str.contains(r"arjun", regex=True).sum()),
        "meet_bros": int(lower_comments.str.contains(r"meet\s*bros", regex=True).sum()),
        "jaz_dhami": int(lower_comments.str.contains(r"jaz|dhami", regex=True).sum()),
        "nostalgia_attendance": int(
            lower_comments.str.contains(
                r"202\d|legend|still|childhood|old\s*is\s*gold|hajri|attendance|anyone\s*here",
                regex=True,
            ).sum()
        ),
        "dance_choreography": int(lower_comments.str.contains(r"dance|step|move|heel|heels", regex=True).sum()),
        "remix_comparison": int(lower_comments.str.contains(r"remix|original|better|version", regex=True).sum()),
        "mouni_roy": int(lower_comments.str.contains(r"mouni|muni", regex=True).sum()),
        "neha_kakkar": int(lower_comments.str.contains(r"neha|kakkar", regex=True).sum()),
        "kgf_yash": int(lower_comments.str.contains(r"kgf|yash|rocky", regex=True).sum()),
    }

    return {
        "total_analyzed_comments": total_comments,
        "char_length": {
            "min": int(char_lengths.min()),
            "mean": round(float(char_lengths.mean()), 2),
            "median": float(char_lengths.median()),
            "max": int(char_lengths.max()),
            "std": round(float(char_lengths.std()), 2),
        },
        "word_count": {
            "min": int(word_counts.min()),
            "mean": round(float(word_counts.mean()), 2),
            "median": float(word_counts.median()),
            "max": int(word_counts.max()),
        },
        "expression_counts": {
            "comments_with_question": has_question,
            "question_pct": round(has_question / total_comments * 100, 2) if total_comments > 0 else 0.0,
            "comments_with_exclamation": has_exclamation,
            "exclamation_pct": round(has_exclamation / total_comments * 100, 2) if total_comments > 0 else 0.0,
            "comments_with_emojis": has_emoji,
            "emoji_pct": round(has_emoji / total_comments * 100, 2) if total_comments > 0 else 0.0,
        },
        "top_keywords": [{"keyword": k, "count": c} for k, c in word_freq],
        "thematic_mentions": thematic_mentions,
    }
