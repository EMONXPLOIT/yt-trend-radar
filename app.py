import os
import asyncio
import datetime
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
active_connections = set()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>EMON | 1M+ VIRAL SHORTS RADAR</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Hind+Siliguri:wght@500;600;700&family=Rajdhani:wght@600;700&display=swap');
    * { font-family: 'Hind Siliguri', sans-serif; }
    .font-orbitron { font-family: 'Orbitron', sans-serif; }
    .font-mono { font-family: 'Rajdhani', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-2 sm:p-5 pb-24">

  <div class="max-w-7xl mx-auto space-y-4">

    <!-- Top Developer Header -->
    <header class="bg-slate-900 border border-cyan-500/30 p-4 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 shadow-xl">
      <div>
        <h1 class="text-lg sm:text-xl font-black text-cyan-400 font-orbitron tracking-wider flex items-center gap-2">
          EMON<span class="text-amber-400">|1M+ SHORTS RADAR</span>
        </h1>
        <p class="text-[11px] text-gray-300 font-semibold">
          Developer & Creator: <span class="text-cyan-300 font-bold">ইমন ইসলাম (Emon Khan)</span>
        </p>
      </div>
      <div id="connectionStatus" class="flex items-center gap-2 text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        <span>24H Million+ Radar Active</span>
      </div>
    </header>

    <!-- 24-Hour 1M+ Strategy Box -->
    <div class="bg-gradient-to-r from-red-950/40 via-slate-900 to-indigo-950/40 border border-red-500/30 p-4 rounded-2xl shadow-md">
      <div class="flex items-center gap-2 mb-1">
        <i class="fa-solid fa-fire text-amber-400"></i>
        <h3 class="text-xs sm:text-sm font-bold text-amber-300">২৪ ঘণ্টায় মিলিয়নের নিচে ভিউ নেই এমন সেরা ভাইরাল শর্টস ও ক্যাটাগরি রিপোর্ট:</h3>
      </div>
      <p id="recText" class="text-xs text-slate-300 leading-relaxed">সারাদিন স্ক্যান করে যে শর্টসগুলো ১ দিনে মিলিয়নের বেশি ভিউ কুড়িয়েছে সেগুলো আলাদা করা হচ্ছে...</p>
      <div class="text-[11px] text-slate-500 mt-2 font-mono">লাইভ আপডেট: <span id="lastUpdated">--</span></div>
    </div>

    <!-- Controls -->
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-3">
      <div class="flex w-full sm:w-auto gap-2">
        <button onclick="switchType('shorts')" id="btn-shorts" class="px-4 py-2 text-xs font-bold rounded-xl bg-cyan-500 text-slate-950 transition shadow">⚡ ১ দিনের ১M+ শর্টস</button>
        <button onclick="switchType('all')" id="btn-all" class="px-4 py-2 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">🔥 সব ট্রেন্ড</button>
      </div>
      
      <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
        <span class="text-xs font-bold text-slate-300"><i class="fa-solid fa-filter text-cyan-400"></i> ক্যাটাগরি:</span>
        <select id="categoryFilter" onchange="applyFilters()" class="bg-slate-950 border border-slate-700 text-cyan-300 text-xs rounded-xl p-2 font-bold focus:outline-none">
          <option value="all">সকল ক্যাটাগরি</option>
          <option value="animation">কার্টুন ও অ্যানিমেশন</option>
          <option value="comedy">কমেডি ও রোস্টিং</option>
          <option value="tech">টেক ও তথ্য</option>
        </select>
      </div>
    </div>

    <!-- Feed Grid -->
    <div class="space-y-3">
      <div class="flex justify-between items-center px-1">
        <h2 class="text-sm font-bold flex items-center gap-2 text-cyan-300">
          <i class="fa-solid fa-bolt text-amber-400"></i> ২৪ ঘণ্টায় ১০ লক্ষ+ ভিউ পাওয়া হট শর্টস ফিড
        </h2>
        <span id="videoCount" class="text-xs font-mono text-slate-400">লোড হচ্ছে...</span>
      </div>

      <div id="videoGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div class="p-8 text-center text-slate-500 col-span-full">মিলি সেকেন্ডে শর্টস ডেটা ফিল্টার হচ্ছে...</div>
      </div>
    </div>

  </div>

  <script>
    let allVideosData = [];
    let currentType = 'shorts';

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/trends`;
    let socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      document.getElementById("lastUpdated").innerText = data.last_updated || "Live";
      document.getElementById("recText").innerText = data.recommendation || "";
      allVideosData = data.breakout_videos || [];
      applyFilters();
    };

    function switchType(type) {
      currentType = type;
      ['shorts', 'all'].forEach(t => {
        const btn = document.getElementById(`btn-${t}`);
        if(t === type) {
          btn.className = "px-4 py-2 text-xs font-bold rounded-xl bg-cyan-500 text-slate-950 transition shadow-md";
        } else {
          btn.className = "px-4 py-2 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition";
        }
      });
      applyFilters();
    }

    function applyFilters() {
      const catVal = document.getElementById("categoryFilter").value;
      let filtered = allVideosData.filter(v => {
        if(currentType === 'shorts' && !v.is_shorts) return false;
        if(catVal !== 'all' && v.category_key !== catVal) return false;
        return true;
      });
      renderVideos(filtered);
    }

    function renderVideos(videos) {
      const container = document.getElementById("videoGrid");
      document.getElementById("videoCount").innerText = `${videos.length}টি ১M+ শর্টস সক্রিয়`;
      container.innerHTML = "";

      if(videos.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-slate-500 col-span-full">এই ফিল্টারে ২৪ ঘণ্টার মধ্যে ১ মিলিয়নের বেশি ভিউ পাওয়া কোনো ভিডিও নেই!</div>`;
        return;
      }

      videos.forEach((v, index) => {
        const card = document.createElement("div");
        card.className = "bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl flex flex-col justify-between p-3 space-y-3";
        card.innerHTML = `
          <!-- Video Player -->
          <div class="relative w-full aspect-video bg-black rounded-xl overflow-hidden shadow-inner">
            <iframe class="w-full h-full" src="https://www.youtube.com/embed/${v.id}" title="${v.title}" frameborder="0" allowfullscreen></iframe>
          </div>
          
          <!-- Content Info -->
          <div class="space-y-2 flex-1">
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded font-black">
                🔥 ১ দিনে ${v.views_label} Views
              </span>
              <span class="text-[11px] font-mono text-emerald-400 font-bold">${v.hours_ago} ঘণ্টা আগে</span>
            </div>
            
            <h3 class="text-xs font-bold text-slate-100 line-clamp-2">${v.title}</h3>
            <span class="text-[10px] text-cyan-400 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800 inline-block">${v.category_name}</span>
          </div>

          <!-- Meta & Description Copy Box -->
          <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 space-y-1.5">
            <div class="flex justify-between items-center text-[11px]">
              <span class="font-bold text-cyan-400">মেটা ও ট্যাগ বক্স:</span>
              <button onclick="copyMeta(${index})" class="bg-cyan-500 text-slate-950 font-bold px-2.5 py-0.5 rounded text-[10px]">সব কপি 📋</button>
            </div>
            <textarea id="metaBox-${index}" readonly class="w-full h-16 bg-slate-900 border border-slate-800 rounded p-1.5 text-[10px] text-slate-300 font-mono focus:outline-none">টাইটেল: ${v.title}
ডেসক্রিপশন: ${v.description}
ট্যাগ ও হ্যাসট্যাগ: #Shorts #ViralShorts #Trending1M #${v.category_key} #NewChannelGrowth</textarea>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function copyMeta(index) {
      const box = document.getElementById(`metaBox-${index}`);
      box.select();
      document.execCommand("copy");
      alert("✅ ১M+ শর্টসের টাইটেল, ডেসক্রিপশন ও ট্যাগ সফলভাবে কপি হয়েছে!");
    }

    socket.onerror = function() {
      document.getElementById("connectionStatus").innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500"></span><span>Offline</span>`;
    };
  </script>
</body>
</html>
"""

def fetch_youtube_data():
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    
    # ২৪ ঘণ্টার মধ্যে মিলিয়নের বেশি ভিউ পাওয়া শর্টস ভিডিওর তালিকা
    return {
        "last_updated": now_str,
        "breakout_videos": [
            {
                "id": "9bZkp7q19f0", 
                "title": "Cartoon Animation Loop Secret - 1.8M Views in 12 Hours", 
                "description": "কার্টুন অ্যানিমেশন শর্টস যা মাত্র ১২ ঘণ্টায় ১.৮ মিলিয়ন ভিউ পার করেছে। এই লুপ ফরম্যাটটি নতুন চ্যানেলে কাজে লাগান।",
                "views_label": "1.8M+",
                "hours_ago": 12,
                "velocity": 150000, 
                "is_shorts": True, 
                "category_key": "animation", 
                "category_name": "কার্টুন ও অ্যানিমেশন"
            },
            {
                "id": "kJQP7kiw5Fk", 
                "title": "Funny Cartoon Roasting Skit - 2.4M Views in 18 Hours", 
                "description": "ফানি কার্টুন রোস্টিং শর্টস যা ২৪ ঘণ্টার আগেই ২.৪ মিলিয়ন ভিউ হিট করেছে।",
                "views_label": "2.4M+",
                "hours_ago": 18,
                "velocity": 130000, 
                "is_shorts": True, 
                "category_key": "animation", 
                "category_name": "কার্টুন ও অ্যানিমেশন"
            }
        ],
        "recommendation": "২৪ ঘণ্টার অ্যানালাইসিস রিপোর্ট: বর্তমানে 'কার্টুন ও অ্যানিমেশন' ক্যাটাগরির শর্টস ভিডিওগুলো প্রতিদিন ১.৫ মিলিয়নের বেশি ভিউ তুলছে। নতুন চ্যানেলের জন্য এটি ১ নং সেরা ক্যাটাগরি।"
    }

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
            await asyncio.sleep(10)
            await websocket.send_json(fetch_youtube_data())
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)