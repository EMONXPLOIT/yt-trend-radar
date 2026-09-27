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

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>YouTube Viral Trend & Niche Radar</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Hind+Siliguri:wght@500;600;700&display=swap');
    * { font-family: 'Hind Siliguri', sans-serif; }
    .font-mono { font-family: 'Rajdhani', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-3 sm:p-6 pb-20">

  <div class="max-w-4xl mx-auto space-y-4">

    <!-- Header -->
    <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-slate-900 border border-slate-800 p-4 rounded-2xl gap-3 shadow-lg">
      <div>
        <h1 class="text-lg sm:text-xl font-bold text-red-500 flex items-center gap-2">
          <i class="fa-brands fa-youtube"></i> YouTube Viral Niche Engine
        </h1>
        <p class="text-xs text-slate-400">রিয়েল-টাইম ট্রেন্ড অ্যানালাইসিস ও নতুন চ্যানেলের ভাইরাল প্রেডিকশন</p>
      </div>
      <div id="connectionStatus" class="flex items-center gap-2 text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        <span>WebSocket Live</span>
      </div>
    </header>

    <!-- Advice Card -->
    <div class="bg-gradient-to-r from-red-950/40 via-slate-900 to-indigo-950/40 border border-red-500/30 p-4 rounded-2xl shadow-md">
      <div class="flex items-center gap-2 mb-1">
        <i class="fa-solid fa-lightbulb text-amber-400"></i>
        <h3 class="text-sm font-bold text-amber-300">নতুন চ্যানেলে ভাইরাল হওয়ার স্ট্র্যাটেজি পরামর্শ:</h3>
      </div>
      <p id="recText" class="text-xs text-slate-300 leading-relaxed">ডেটা বিশ্লেষণ করা হচ্ছে...</p>
      <div class="text-[11px] text-slate-500 mt-2 font-mono">সর্বশেষ আপডেট: <span id="lastUpdated">--</span></div>
    </div>

    <!-- Growth Radar Table -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="p-3.5 border-b border-slate-800">
        <h2 class="text-sm font-bold flex items-center gap-2 text-cyan-300">
          <i class="fa-solid fa-chart-line text-cyan-400"></i> সর্বাধিক গতির ব্রেকআউট ভিডিও (Top Growth Radar)
        </h2>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-950/80 uppercase text-slate-400 border-b border-slate-800 font-mono">
            <tr>
              <th class="p-3">ভিডিও টাইটেল</th>
              <th class="p-3">আপলোড</th>
              <th class="p-3 text-right">গতি (Velocity)</th>
              <th class="p-3 text-right">এঙ্গেজমেন্ট</th>
              <th class="p-3 text-center">স্কোর</th>
            </tr>
          </thead>
          <tbody id="trendsBody" class="divide-y divide-slate-800/60 font-mono">
            <tr><td colspan="5" class="p-4 text-center text-slate-500">ডেটা লোড হচ্ছে...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>

  <script>
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/trends`;
    let socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      document.getElementById("lastUpdated").innerText = data.last_updated || "Live";
      document.getElementById("recText").innerText = data.recommendation || "";

      if(data.breakout_videos && data.breakout_videos.length > 0) {
        const tbody = document.getElementById("trendsBody");
        tbody.innerHTML = "";

        data.breakout_videos.forEach(v => {
          const tr = document.createElement("tr");
          tr.className = "hover:bg-slate-800/40 transition";
          tr.innerHTML = `
            <td class="p-3 font-medium text-slate-200 max-w-xs truncate font-sans">
              <a href="${v.url}" target="_blank" class="hover:text-cyan-400 flex items-center gap-1.5">
                <i class="fa-solid fa-arrow-up-right-from-square text-[10px] text-slate-500"></i> ${v.title}
              </a>
            </td>
            <td class="p-3 text-slate-400">${v.hours_live} ঘণ্টা আগে</td>
            <td class="p-3 text-right font-bold text-emerald-400">+${v.velocity.toLocaleString()} /hr</td>
            <td class="p-3 text-right text-cyan-300">${v.engagement}%</td>
            <td class="p-3 text-center">
              <span class="bg-amber-500/10 border border-amber-500/30 text-amber-400 px-2 py-0.5 rounded font-bold">
                ${v.viral_score}
              </span>
            </td>
          `;
          tbody.appendChild(tr);
        });
      }
    };

    socket.onerror = function() {
      document.getElementById("connectionStatus").innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500"></span><span>Offline</span>`;
      document.getElementById("connectionStatus").className = "flex items-center gap-2 text-xs font-mono bg-rose-950/60 text-rose-400 border border-rose-500/30 px-3 py-1.5 rounded-xl";
    };
  </script>
</body>
</html>
"""

def analyze_youtube_trends():
    global viral_insights
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    if not YOUTUBE_API_KEY:
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
    return HTMLResponse(content=HTML_TEMPLATE)

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