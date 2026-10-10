import requests

from config.environment import get_env


YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_videos(query, max_results=10):
    api_key = get_env("YOUTUBE_API_KEY")

    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "regionCode": "IN",
        "videoEmbeddable": "true",
    }

    response = requests.get(
        YOUTUBE_SEARCH_URL,
        params={
            **params,
            "key": api_key,
        },
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})

        if not video_id:
            continue

        results.append({
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "description": snippet.get("description", ""),
        })

    return results
