# backend/main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import requests
import logging

# Optional YouTube API
try:
    from googleapiclient.discovery import build as youtube_build
except Exception:
    youtube_build = None

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# --------------------------
# Pydantic models
# --------------------------
class Options(BaseModel):
    safe_run: Optional[bool] = False
    include_youtube: Optional[bool] = True
    max_tokens: Optional[int] = 1024

class ExplainRequest(BaseModel):
    code: str
    language: str
    user_level: str
    options: Optional[Options] = Options()

class ExplainLine(BaseModel):
    line_number: int
    code: str
    explanation: str

class ExplainResponse(BaseModel):
    summary: Optional[str]
    lines: Optional[List[ExplainLine]]
    related_videos: Optional[List[Dict[str, Any]]]

# --------------------------
# Helper functions
# --------------------------
def call_gemini_model(prompt: str, max_tokens: int = 1024) -> str:
    """Stub function to integrate Google Gemini later."""
    return "MOCK_RESPONSE: Explanation goes here."

def youtube_search(query: str, max_results: int = 3):
    if not YOUTUBE_API_KEY or youtube_build is None:
        return []
    try:
        youtube = youtube_build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        req = youtube.search().list(q=query, part="snippet", type="video", maxResults=max_results)
        resp = req.execute()
        videos = []
        for item in resp.get("items", []):
            videos.append({
                "title": item["snippet"]["title"],
                "video_id": item["id"]["videoId"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return videos
    except Exception as e:
        logger.exception("YouTube API error: %s", e)
        return []

# --------------------------
# Endpoints
# --------------------------
@app.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    try:
        lines = []
        for i, line in enumerate(req.code.splitlines(), start=1):
            if line.strip():
                lines.append({"line_number": i, "code": line, "explanation": f"Mock explanation for line {i}"})
        videos = youtube_search(req.code.splitlines()[0][:50]) if req.options.include_youtube else []
        return {"summary": f"Explained {len(lines)} lines.", "lines": lines, "related_videos": videos}
    except Exception as e:
        logger.exception("Error in /explain: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

# TODO: Add /fix and /practice endpoints similarly
