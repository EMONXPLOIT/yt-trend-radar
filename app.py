import os
import asyncio
import datetime
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# Render-এর Environment Variable থেকে API Key নিবে
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

active_connections = set()

# ক্যাটাগরি আইডি ম্যাপিং
CATEGORIES = {
    "all": {"name": "সব ক্যাটাগরি", "id": None},
    "animation": {"name": "কার্টুন ও অ্যানিমেশন", "id": "1"},
    "gaming": {"name": "গেমিং", "id": "20"},
    "comedy": {"name": "কমেডি ও রোস্টিং", "id": "23"},
    "tech": {"name": "টেক ও গ্যাজেট", "id": "28"},
    "shorts": {"name": "ভাইরাল শর্টস", "id": "24"}
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>EMON SMART RADAR | Viral YouTube Engine</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Hind+Siliguri:wght@500;600;700&family=Rajdhani:wght@600;700&display=swap');
    * { font-family: 'Hind Siliguri', sans-serif; }
    .font-orbitron { font-family: 'Orbitron', sans-serif; }
    .font-mono { font-family: 'Rajdhani', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-3 sm:p-6 pb-24">

  <div class="max-w-4xl mx-auto space-y-4">

    <!-- Top Developer Branding Header -->
    <header class="bg-slate-900 border border-cyan-500/30 p-4 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 shadow-xl">
      <div>
        <h1 class="text-lg sm:text-xl font-black text-cyan-400 font-orbitron tracking-wider flex items-center gap-2">
          EMON<span class="text-amber-400">|VIRAL RADAR</span>
        </h1>
        <p class="text-[11px] text-gray-300 font-semibold">
          Developer & Creator: <span class="text-cyan-300 font-bold">ইমন ইসলাম (Emon Khan)</span>
        </p>
      </div>
      <div id="connectionStatus" class="flex items-center gap-2 text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        <span>WebSocket Live Radar</span>
      </div>
    </header>

    <!-- Strategy Advice Box -->
    <div class="bg-gradient-to-r from-red-950/40 via-slate-900 to-indigo-950/40 border border-red-500/30 p-4 rounded-2xl shadow-md">
      <div class="flex items-center gap-2 mb-1">
        <i class="fa-solid fa-lightbulb text-amber-400"></i>
        <h3 class="text-xs sm:text-sm font-bold text-amber-300">নতুন চ্যানেলে যে ধরনের ভিডিও সবচেয়ে দ্রুত ভাইরাল হচ্ছে:</h3>
      </div>
      <p id="recText" class="text-xs text-slate-300 leading-relaxed">অ্যালগরিদম বিশ্লেষণ চলছে...</p>
      <div class="text-[11px] text-slate-500 mt-2 font-mono">আপডেট সময়: <span id="lastUpdated">--</span></div>
    </div>

    <!-- Category Selector Controls -->
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-2 text-xs font-bold text-slate-300">
        <i class="fa-solid fa-filter text-cyan-400"></i> ক্যাটাগরি বাছাই করুন:
      </div>
      <select id="categoryFilter" onchange="filterCategory(this.value)" class="bg-slate-950 border border-slate-700 text-cyan-300 text-xs rounded-xl p-2 font-bold focus:outline-none focus:border-cyan-400">
        <option value="all">🔥 সব ক্যাটাগরি (All Trends)</option>
        <option value="animation">🎬 কার্টুন ও অ্যানিমেশন</option>
        <option value="comedy">😂 রোস্টিং ও কমেডি</option>
        <option value="gaming">🎮 গেমিং ও লাইভস্ট্রিম</option>
        <option value="tech">📱 টেক ও গ্যাজেট</option>
        <option value="shorts">⚡ ভাইরাল শর্টস</option>
      </select>
    </div>

    <!-- Live Videos Container With Integrated Players -->
    <div class="space-y-4">
      <div class="flex justify-between items-center px-1">
        <h2 class="text-sm font-bold flex items-center gap-2 text-cyan-300">
          <i class="fa-solid fa-fire text-amber-400"></i> সর্বাধিক সম্ভাব্য ভাইরাল ভিডিও (লাইভ প্লেয়ার)
        </h2>
        <span id="videoCount" class="text-xs font-mono text-slate-400">লোড হচ্ছে...</span>
      </div>

      <div id="videoGrid" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Dynamic Video Cards Will Render Here -->
        <div class="p-6 text-center text-slate-500 col-span-2">ভিডিও লোড হচ্ছে...</div>
      </div>
    </div>

  </div>

  <script>
    let allVideosData = [];
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/trends`;
    let socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      document.getElementById("lastUpdated").innerText = data.last_updated || "Live";
      document.getElementById("recText").innerText = data.recommendation || "";
      allVideosData = data.breakout_videos || [];
      renderVideos(allVideosData);
    };

    function renderVideos(videos) {
      const container = document.getElementById("videoGrid");
      document.getElementById("videoCount").innerText = `${videos.length}টি ব্রেকআউট ভিডিও পাওয়া গেছে`;
      container.innerHTML = "";

      if(videos.length === 0) {
        container.innerHTML = `<div class="p-6 text-center text-slate-500 col-span-2">কোনো ভিডিও পাওয়া যায়নি!</div>`;
        return;
      }

      videos.forEach(v => {
        const card = document.createElement("div");
        card.className = "bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg flex flex-col justify-between";
        card.innerHTML = `
          <!-- Embedded YouTube Video Player -->
          <div class="relative w-full aspect-video bg-black">
            <iframe 
              class="w-full h-full" 
              src="https://www.youtube.com/embed/${v.id}?enablejsapi=1" 
              title="${v.title}" 
              frameborder="0" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen>
            </iframe>
          </div>

          <!-- Video Details & Metrics -->
          <div class="p-3.5 space-y-2.5">
            <h3 class="text-xs font-bold text-slate-200 line-clamp-2" title="${v.title}">
              ${v.title}
            </h3>

            <div class="grid grid-cols-3 gap-1.5 text-center text-[10px] font-mono">
              <div class="bg-slate-950 p-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400 block">আপলোড</span>
                <span class="font-bold text-white">${v.hours_live} ঘণ্টা আগে</span>
              </div>
              <div class="bg-slate-950 p-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400 block">গতি (Velocity)</span>
                <span class="font-bold text-emerald-400">+${v.velocity.toLocaleString()}/hr</span>
              </div>
              <div class="bg-slate-950 p-1.5 rounded-lg border border-amber-500/30 bg-amber-500/5">
                <span class="text-amber-300 block">ভাইরাল স্কোর</span>
                <span class="font-black text-amber-400 text-xs">${v.viral_score}</span>
              </div>
            </div>

            <div class="flex justify-between items-center pt-1 border-t border-slate-800/80 text-[11px]">
              <span class="text-cyan-400 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800">${v.category_name}</span>
              <a href="${v.url}" target="_blank" class="text-slate-400 hover:text-white flex items-center gap-1 font-semibold">
                ইউটিউবে দেখুন <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
              </a>
            </div>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function filterCategory(catKey) {
      if(catKey === "all") {
        renderVideos(allVideosData);
      } else {
        const filtered = allVideosData.filter(v => v.category_key === catKey);
        renderVideos(filtered);
      }
    }

    socket.onerror = function() {
      document.getElementById("connectionStatus").innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500"></span><span>Offline</span>`;
      document.getElementById("connectionStatus").className = "flex items-center gap-2 text-xs font-mono bg-rose-950/60 text-rose-400 border border-rose-500/30 px-3 py-1.5 rounded-xl";
    };
  </script>
</body>
</html>
"""

def fetch_youtube_data():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    # API Key না থাকলে বিভিন্ন ক্যাটাগরির রিয়েল ডেমো ভিডিও যাতে লাইভ চলে
    if not YOUTUBE_API_KEY:
        return {
            "last_updated": now_str,
            "breakout_videos": [
                {
                    "id": "kJQP7kiw5Fk",
                    "title": "Despacito - Global Record Breaking Animation Concept",
                    "hours_live": 3.2,
                    "velocity": 24500,
                    "viral_score": 98,
                    "category_key": "animation",
                    "category_name": "কার্টুন ও অ্যানিমেশন",
                    "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk"
                },
                {
                    "id": "JGwWNGJdvx8",
                    "title": "Shape of You - Short Story Audio Beat Breakdown",
                    "hours_live": 5.4,
                    "velocity": 19200,
                    "viral_score": 94,
                    "category_key": "comedy",
                    "category_name": "রোস্টিং ও কমেডি",
                    "url": "https://www.youtube.com/watch?v=JGwWNGJdvx8"
                },
                {
                    "id": "fJ9rUzIMcZQ",
                    "title": "Queen - Live Aid Analysis: High Engagement Dynamics",
                    "hours_live": 7.1,
                    "velocity": 12800,
                    "viral_score": 89,
                    "category_key": "tech",
                    "category_name": "টেক ও গ্যাজেট",
                    "url": "https://www.youtube.com/watch?v=fJ9rUzIMcZQ"
                },
                {
                    "id": "9bZkp7q19f0",
                    "title": "PSY - Viral Storytelling Loop Secret For New Creators",
                    "hours_live": 9.0,
                    "velocity": 9800,
                    "viral_score": 84,
                    "category_key": "shorts",
                    "category_name": "ভাইরাল শর্টস",
                    "url": "https://www.youtube.com/watch?v=9bZkp7q19f0"
                }
            ],
            "recommendation": "নতুন চ্যানেলে এখন কার্টুন/অ্যানিমেশন ও শর্ট স্টোরিতে প্রতি ঘণ্টায় ভিউ বৃদ্ধির গতি (Velocity) সবচেয়ে বেশি।"
        }

    # API Key থাকলে ইউটিউব থেকে সরাসরি ফেচ করবে
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode=US&maxResults=30&key={YOUTUBE_API_KEY}"
        res = requests.get(url, timeout=12).json()
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
                "id": item["id"],
                "title": item["snippet"]["title"],
                "hours_live": round(hours_live, 1),
                "velocity": round(velocity),
                "viral_score": score,
                "category_key": "animation" if item["snippet"]["categoryId"] == "1" else "comedy",
                "category_name": "ইউটিউব ট্রেন্ডিং",
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })

        analyzed.sort(key=lambda x: x["viral_score"], reverse=True)
        return {
            "last_updated": now_str,
            "breakout_videos": analyzed,
            "recommendation": "অ্যালগরিদম এখন হাই-রিটেনশন শর্ট স্টোরি ভিডিওগুলোকে বেশি রিকমেন্ড করছে।"
        }
    except Exception as e:
        print(f"Fetch Error: {e}")
        return fetch_youtube_data()

@app.get("/")
async def get_index():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.websocket("/ws/trends")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        data = fetch_youtube_data()
        await websocket.send_json(data)
        while True:
            await asyncio.sleep(15)
            await websocket.send_json(fetch_youtube_data())
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)