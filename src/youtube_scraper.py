"""
YouTube Data API v3 Scraper Integration.
Safely harvests public YouTube comment threads using environment-configured API key.
Adheres strictly to credential protection rules: API keys are never exposed in UI or code.
"""

import os
import re
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import requests

YT_API_BASE = "https://www.googleapis.com/youtube/v3"

def get_api_key() -> Optional[str]:
    """Retrieves API key from environment or .env file."""
    key = os.getenv("YOUTUBE_API_KEY")
    if key and key != "your_api_key_here" and len(key.strip()) > 10:
        return key.strip()
    # Check .env file manually if dotenv not loaded
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("YOUTUBE_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val and val != "your_api_key_here":
                        return val
    return None


def get_api_status() -> Dict[str, Any]:
    """
    Returns public API status without exposing credential secrets.
    """
    key = get_api_key()
    is_configured = bool(key)
    return {
        "configured": is_configured,
        "status_label": "Configured (API Ready)" if is_configured else "Not Configured (Missing YOUTUBE_API_KEY in .env)",
        "can_scrape": is_configured
    }


def extract_video_id(url_or_id: str) -> Optional[str]:
    """
    Extracts 11-character YouTube video ID from various URL formats.
    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - Raw 11-char ID
    """
    if not url_or_id:
        return None
    text = url_or_id.strip()
    if len(text) == 11 and re.match(r'^[A-Za-z0-9_-]{11}$', text):
        return text
        
    patterns = [
        r'(?:v=|\/)([A-Za-z0-9_-]{11})(?:\&|\?|\/|$)',
        r'youtu\.be\/([A-Za-z0-9_-]{11})',
        r'shorts\/([A-Za-z0-9_-]{11})'
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def fetch_video_metadata(video_id: str, api_key: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Retrieves video title and comment count."""
    url = f"{YT_API_BASE}/videos"
    params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": api_key
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if resp.status_code != 200:
            err_msg = data.get("error", {}).get("message", "Video metadata lookup failed.")
            return None, err_msg
            
        items = data.get("items", [])
        if not items:
            return None, f"No YouTube video found with ID '{video_id}'."
            
        item = items[0]
        title = item.get("snippet", {}).get("title", f"Video {video_id}")
        stats = item.get("statistics", {})
        comment_count = int(stats.get("commentCount", 0))
        return {"id": video_id, "title": title, "comment_count": comment_count}, None
    except requests.exceptions.RequestException as e:
        return None, f"Network error during YouTube API call: {str(e)}"


def scrape_youtube_comments(video_url_or_id: str,
                            max_comments: int = 300,
                            include_replies: bool = False) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Harvests public comments via YouTube Data API v3 and returns a standardized DataFrame.
    """
    api_key = get_api_key()
    if not api_key:
        return None, "YouTube API key not found. Please set YOUTUBE_API_KEY in your .env file."
        
    vid = extract_video_id(video_url_or_id)
    if not vid:
        return None, "Invalid YouTube video URL or ID format."
        
    meta, err = fetch_video_metadata(vid, api_key)
    if err:
        return None, err
        
    video_title = meta["title"]
    records = []
    page_token = None
    
    try:
        while len(records) < max_comments:
            params = {
                "part": "snippet",
                "videoId": vid,
                "maxResults": min(100, max_comments - len(records)),
                "key": api_key,
                "textFormat": "plainText",
                "order": "relevance"
            }
            if page_token:
                params["pageToken"] = page_token
                
            resp = requests.get(f"{YT_API_BASE}/commentThreads", params=params, timeout=12)
            data = resp.json()
            
            if resp.status_code != 200:
                err_code = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
                if err_code == "commentsDisabled":
                    return None, "Comments are disabled for this YouTube video."
                elif err_code == "quotaExceeded":
                    return None, "YouTube Data API quota exceeded for today."
                else:
                    return None, data.get("error", {}).get("message", "API request failed.")
                    
            items = data.get("items", [])
            if not items:
                break
                
            for it in items:
                top = it.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                records.append({
                    "type": "comment",
                    "author": top.get("authorDisplayName", "Anonymous"),
                    "comment": top.get("textDisplay", ""),
                    "likes": int(top.get("likeCount", 0)),
                    "published_at": top.get("publishedAt", ""),
                    "reply_count": int(it.get("snippet", {}).get("totalReplyCount", 0)),
                    "video_name": video_title
                })
                if len(records) >= max_comments:
                    break
                    
            page_token = data.get("nextPageToken")
            if not page_token:
                break
                
        if not records:
            return None, "No comments were returned for this video."
            
        df = pd.DataFrame(records)
        return df, None
        
    except requests.exceptions.RequestException as rex:
        return None, f"Network communication error: {str(rex)}"

