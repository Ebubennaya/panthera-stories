import os
import random
import requests
from datetime import datetime, timedelta

def research_youtube():
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        return {'error': 'YouTube API key not configured', 'results': [], 'themes': []}

    all_queries = [
        'Nigerian AI film 2025', 'Nollywood AI generated film',
        'Nigerian folklore AI video', 'African AI short film viral',
        'Nigerian office drama 2025', 'Nollywood blockbuster film',
        'Nigerian corporate thriller film', 'African mythology short film',
        'Yoruba Igbo folklore film', 'Nigerian romance film viral 2025',
        'African AI cinematic video', 'Nigeria film award winner 2025'
    ]

    random.shuffle(all_queries)
    selected = all_queries[:5]
    days = random.choice([30, 60, 90])
    published_after = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')

    all_results = []
    seen_ids = set()

    for query in selected:
        try:
            resp = requests.get('https://www.googleapis.com/youtube/v3/search', params={
                'part': 'snippet', 'q': query, 'type': 'video',
                'order': 'viewCount', 'maxResults': 5, 'key': api_key,
                'videoDuration': 'medium', 'publishedAfter': published_after
            }, timeout=10)
            data = resp.json()
            if 'items' not in data:
                continue

            video_ids = [item['id']['videoId'] for item in data['items']]
            stats_resp = requests.get('https://www.googleapis.com/youtube/v3/videos', params={
                'part': 'statistics', 'id': ','.join(video_ids), 'key': api_key
            }, timeout=10)
            stats_map = {i['id']: i.get('statistics', {}) for i in stats_resp.json().get('items', [])}

            for item in data['items']:
                vid = item['id']['videoId']
                if vid in seen_ids:
                    continue
                seen_ids.add(vid)
                stats = stats_map.get(vid, {})
                views = int(stats.get('viewCount', 0))
                all_results.append({
                    'id': vid,
                    'title': item['snippet']['title'],
                    'channel': item['snippet']['channelTitle'],
                    'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                    'view_count': views,
                    'view_count_formatted': f"{views:,} views"
                })
        except Exception as e:
            print(f"Query error: {e}")
            continue

    all_results.sort(key=lambda x: x['view_count'], reverse=True)
    top = all_results[:10]
    return {'results': top, 'themes': extract_themes(top)}

def extract_themes(results):
    skip = {'with','that','this','from','have','will','been','they','part','latest',
            'full','movie','film','nigerian','nollywood','african','2024','2025'}
    counts = {}
    for r in results:
        for word in r['title'].lower().split():
            w = word.strip('|,-.()[]')
            if len(w) > 4 and w not in skip:
                counts[w] = counts.get(w, 0) + 1
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return [w.title() for w, _ in top]
