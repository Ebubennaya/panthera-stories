import os
import random
import requests
from datetime import datetime, timedelta

SEARCH_QUERIES = [
    "Nigerian AI film",
    "Nollywood AI generated video",
    "Nigerian folklore AI",
    "African AI short film",
    "Yoruba legend AI video",
    "Igbo mythology AI",
    "African mythology AI film",
    "Nigeria AI animation",
    "Nollywood AI drama",
    "African epic AI film",
    "Nigerian supernatural AI story",
    "West Africa AI cinematic",
]


def _format_views(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M views"
    if n >= 1_000:
        return f"{n/1_000:.0f}K views"
    return f"{n} views"


def run_research():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not set")

    queries = random.sample(SEARCH_QUERIES, min(4, len(SEARCH_QUERIES)))
    days_back = random.choice([30, 60, 90, 180])
    published_after = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_video_ids = []
    seen = set()

    for query in queries:
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "key": api_key,
                    "q": query,
                    "type": "video",
                    "part": "id,snippet",
                    "maxResults": 10,
                    "publishedAfter": published_after,
                    "videoDuration": "medium",
                    "relevanceLanguage": "en",
                    "order": "viewCount",
                },
                timeout=15
            )
            for item in resp.json().get("items", []):
                vid_id = item.get("id", {}).get("videoId")
                if vid_id and vid_id not in seen:
                    seen.add(vid_id)
                    all_video_ids.append(vid_id)
        except Exception:
            continue

    if not all_video_ids:
        return {"results": [], "themes": ["No results — check YouTube API key or quota"]}

    # Second call: get view counts and thumbnails for all found IDs
    videos = []
    for i in range(0, len(all_video_ids), 50):
        batch = all_video_ids[i:i + 50]
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "key": api_key,
                    "id": ",".join(batch),
                    "part": "snippet,statistics",
                },
                timeout=15
            )
            for item in resp.json().get("items", []):
                vid_id = item["id"]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                view_count = int(stats.get("viewCount", 0))

                thumbs = snippet.get("thumbnails", {})
                thumbnail = (
                    thumbs.get("maxres") or
                    thumbs.get("high") or
                    thumbs.get("medium") or
                    thumbs.get("default") or {}
                ).get("url", "")

                videos.append({
                    "id": vid_id,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "title": snippet.get("title", "Untitled"),
                    "channel": snippet.get("channelTitle", ""),
                    "thumbnail": thumbnail,
                    "view_count": view_count,
                    "view_count_formatted": _format_views(view_count),
                    "published": snippet.get("publishedAt", "")[:10],
                })
        except Exception:
            continue

    videos.sort(key=lambda v: v["view_count"], reverse=True)
    top = videos[:12]

    return {"results": top, "themes": _extract_themes(top)}


def _extract_themes(videos):
    counts = {}
    keywords = ["folklore", "legend", "spirit", "curse", "warrior", "king", "queen",
                "village", "nollywood", "nigeria", "africa", "mystery", "love", "revenge"]
    for v in videos:
        t = v["title"].lower()
        for kw in keywords:
            if kw in t:
                counts[kw] = counts.get(kw, 0) + 1

    sorted_kw = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    themes = [f"{kw.title()} ({n} videos)" for kw, n in sorted_kw[:6]]
    return themes or ["Nigerian AI content", "Nollywood-style films", "African storytelling"]
