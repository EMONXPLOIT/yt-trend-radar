import os
import asyncio
import datetime
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

active_connections = set()
viral_insights = {
    "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
    "breakout_videos": [],
    "recommendation": "নতুন চ্যানেলে এখন অ্যানিমেশন, শর্ট স্টোরি ও রিলস ফরম্যাটে ৩ মিনিটের নিচের কনটেন্টে গ্রোথ রেট সবচেয়ে বেশি।"
}

def analyze_youtube_trends():
    global viral_insights
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    if not YOUTUBE_API_KEY:
        # ডেমো ডাটা যাতে API Key ছাড়াও লাইভ সার্ভার সুন্দরভাবে চলে
        viral_insights = {
            "last_updated": now_str,
            "breakout_videos": [
                {
                    "title": "Viral 3D Animation Breakdown & Tips",
                    "hours_live": 4.5,
                    "velocity": 18450,
                    "engagement": 8.4,
                    "viral_score": 92,
                    "url": "https://www.youtube.com"
                },
                {
                    "title": "Shorts Storytelling Algorithm Secrets",
                    "hours_live": 8.2,
                    "velocity": 9200,
                    "engagement": 7.1,
                    "viral_score": 85,
                    "url": "https://www.youtube.com"
                }
            ],
            "recommendation": "নতুন চ্যানেলে এখন ৩ মিনিটের নিচে কার্টুন অ্যানিমেশন ও স্টোরি শর্টস তৈরি করলে ভাইরাল হওয়ার গতি সবচেয়ে বেশি।"
        }
        return

    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=15&key={YOUTUBE_API_KEY}"
        res = requests.get(url, timeout=10).json()
        
        analyzed = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for item in res.get("items", []):
            pub_date = datetime.datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))
            hours_live = max((now - pub_date).total_seconds() / 3600, 0.5)
            views = int(item["statistics"].get("viewCount", 0))
            likes = int(item["statistics"].get("likeCount", 0))
            comments = int(item["statistics"].get("commentCount", 0))

            velocity = views / hours_live
            engagement = ((likes + comments) / max(views, 1)) * 100
            score = round((velocity * 0.6) + (engagement * 1000 * 0.4))

            analyzed.append({
                "title": item["snippet"]["title"],
                "hours_live": round(hours_live, 1),
                "velocity": round(velocity),
                "engagement": round(engagement, 2),
                "viral_score": score,
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })
        
        analyzed.sort(key=lambda x: x["viral_score"], reverse=True)
        viral_insights = {
            "last_updated": now_str,
            "breakout_videos": analyzed[:10],
            "recommendation": "অ্যালগরিদম এখন হাই-রিটেনশন শর্টস ভিডিওগুলোকে বেশি পুশ করছে।"
        }
    except Exception as e:
        print(f"Error fetching: {e}")

@app.on_event("startup")
async def startup_event():
    analyze_youtube_trends()

@app.get("/")
async def get_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Backend Active</h1>")

@app.websocket("/ws/trends")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        await websocket.send_json(viral_insights)
        while True:
            await asyncio.sleep(10)
            await websocket.send_json(viral_insights)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)