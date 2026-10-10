from googleapiclient.discovery import build

from config.environment import get_env

YOUTUBE_API_KEY = get_env("YOUTUBE_API_KEY")


def get_youtube():
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")

    return build(
        "youtube",
        "v3",
        developerKey=YOUTUBE_API_KEY
    )


def search_videos(query, max_results=5):

    youtube = get_youtube()

    response = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    ).execute()

    results = []

    for item in response.get("items", []):

        results.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"]
        })

    return results

def get_first_video(query):

    results = search_videos(query, max_results=1)

    if not results:
        return None

    return results[0]

def get_video_list(query, max_results=10):
    return search_videos(query, max_results)
