from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import logging

load_dotenv()
from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("YOUTUBE_API_KEY")
#API_KEY ="AIzaSyDLgTOkVHePbJIHK54A5vgDbvRtjTwbguA"
def get_comments(video_id: str, max_results: int= None):
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        comments = []

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )

        while request:
            response = request.execute()

            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": snippet.get("authorDisplayName"),
                    "text": snippet.get("textDisplay"),
                    "likes": snippet.get("likeCount"),
                    "published_at": snippet.get("publishedAt"),
                })

            request = youtube.commentThreads().list_next(request, response)

            if max_results is not None and len(comments) >= max_results:
                break


        return comments

    except Exception as e:
        logging.exception("Error fetching comments from YouTube API")
        return {"error": str(e)}
