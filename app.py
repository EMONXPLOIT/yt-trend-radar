import os
import asyncio
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from googleapiclient.discovery import build
from apscheduler.schedulers.asyncio import AsyncIOScheduler

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

active_connections = set()
viral_insights = {
    "last_updated": None,
    "breakout_videos": [],
    "recommendation": "নতুন চ্যানেলে এখন অ্যানিমেশন, শর্ট স্টোরি ও রিলস ফরম্যাটে ৩ মিনিটের নিচের কনটেন্টে গ্রোথ রেট সবচেয়ে বেশি।"
}

def analyze_youtube_trends():
    global viral_insights
    if not YOUTUBE_API_KEY:
        viral_insights["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        viral_insights["recommendation"] = "API Key সেট করা হয়নি। দয়া করে Render Environment Variable-এ YOUTUBE_API_KEY যুক্ত করুন।"
        return

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode="US",
            maxResults=20
        )
        response = request.execute()

        analyzed_list = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for item in response.get("items", []):
            published_at_str = item["snippet"]["publishedAt"].replace("Z", "+00:00")
            published_at = datetime.datetime.fromisoformat(published_at_str)
            hours_live = max((now - published_at).total_seconds() / 3600, 0.5)

            views = int(item["statistics"].get("viewCount", 0))
            likes = int(item["statistics"].get("likeCount", 0))
            comments = int(item["statistics"].get("commentCount", 0))

            velocity = views / hours_live
            engagement_rate = ((likes + comments) / max(views, 1)) * 100
            viral_score = round((velocity * 0.7) + (engagement_rate * 1000 * 0.3))

            analyzed_list.append({
                "title": item["snippet"]["title"],
                "hours_live": round(hours_live, 1),
                "views": views,
                "velocity": round(velocity),
                "engagement": round(engagement_rate, 2),
                "viral_score": viral_score,
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })

        analyzed_list.sort(key=lambda x: x["viral_score"], reverse=True)

        viral_insights = {
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
            "breakout_videos": analyzed_list[:10],
            "recommendation": "নতুন চ্যানেলে এখন শর্টস ও স্টোরি অ্যানিমেশন ফরম্যাটে এঙ্গেজমেন্ট সবচেয়ে দ্রুত বৃদ্ধি পাচ্ছে।"
        }
    except Exception as e:
        print(f"Error fetching data: {e}")

scheduler = AsyncIOScheduler()
scheduler.add_job(analyze_youtube_trends, 'interval', minutes=30)
scheduler.start()

@app.on_event("startup")
async def startup_event():
    analyze_youtube_trends()

@app.get("/")
async def get_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Backend Running. Please ensure index.html exists.</h1>")

@app.websocket("/ws/trends")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        await websocket.send_json(viral_insights)
        while True:
            await asyncio.sleep(15)
            await websocket.send_json(viral_insights)
    except WebSocketDisconnect:
        active_connections.remove(websocket)