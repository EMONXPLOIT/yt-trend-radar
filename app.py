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
  <title>EMON | VIRAL RADAR</title>
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

  <div class="max-w-6xl mx-auto space-y-4">

    <!-- Top Developer Header -->
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
        <span>24/7 Deep AI Analysis Active</span>
      </div>
    </header>

    <!-- Strategy & Category Analysis Box -->
    <div class="bg-gradient-to-r from-red-950/40 via-slate-900 to-indigo-950/40 border border-red-500/30 p-4 rounded-2xl shadow-md">
      <div class="flex items-center gap-2 mb-1">
        <i class="fa-solid fa-brain text-amber-400"></i>
        <h3 class="text-xs sm:text-sm font-bold text-amber-300">হাজার হাজার ভিডিও অ্যানালাইসিস ও ট্রেন্ডিং ক্যাটাগরি রিপোর্ট:</h3>
      </div>
      <p id="recText" class="text-xs text-slate-300 leading-relaxed">সারাদিন ধরে ইউটিউব ফিড স্ক্যান করে সবচেয়ে বেশি ভাইরাল হওয়া ক্যাটাগরিগুলো আলাদা করা হচ্ছে...</p>
      <div class="text-[11px] text-slate-500 mt-2 font-mono">স্ক্যানিং আপডেট: <span id="lastUpdated">--</span></div>
    </div>

    <!-- Type & Category Controls -->
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-3">
      <div class="flex w-full sm:w-auto gap-2">
        <button onclick="switchType('all')" id="btn-all" class="px-4 py-2 text-xs font-bold rounded-xl bg-cyan-500 text-slate-950 transition shadow">🔥 সব হট ভিডিও</button>
        <button onclick="switchType('shorts')" id="btn-shorts" class="px-4 py-2 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">⚡ শর্টস</button>
        <button onclick="switchType('long')" id="btn-long" class="px-4 py-2 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">📺 লং</button>
      </div>
      
      <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
        <span class="text-xs font-bold text-slate-300"><i class="fa-solid fa-filter text-cyan-400"></i> ক্যাটাগরি:</span>
        <select id="categoryFilter" onchange="applyFilters()" class="bg-slate-950 border border-slate-700 text-cyan-300 text-xs rounded-xl p-2 font-bold focus:outline-none">
          <option value="all">সকল ক্যাটাগরি</option>
          <option value="animation">কার্টুন ও অ্যানিমেশন</option>
          <option value="comedy">কমেডি ও রোস্টিং</option>
          <option value="tech">টেক ও তথ্য</option>
          <option value="gaming">গেমিং</option>
        </select>
      </div>
    </div>

    <!-- Massive Grid Feed (Like Local YouTube) -->
    <div class="space-y-3">
      <div class="flex justify-between items-center px-1">
        <h2 class="text-sm font-bold flex items-center gap-2 text-cyan-300">
          <i class="fa-solid fa-video text-amber-400"></i> হট ভাইরাল ভিডিও ফিড (লোকাল ইউটিউব প্রোটোটাইপ)
        </h2>
        <span id="videoCount" class="text-xs font-mono text-slate-400">ভিডিও লোড হচ্ছে...</span>
      </div>

      <div id="videoGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="p-8 text-center text-slate-500 col-span-full">হাজার হাজার ভিডিও স্ক্যান ও প্রসেস করা হচ্ছে...</div>
      </div>
    </div>

  </div>

  <script>
    let allVideosData = [];
    let currentType = 'all';

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
      ['all', 'shorts', 'long'].forEach(t => {
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
        if(currentType === 'long' && v.is_shorts) return false;
        if(catVal !== 'all' && v.category_key !== catVal) return false;
        return true;
      });
      renderVideos(filtered);
    }

    function renderVideos(videos) {
      const container = document.getElementById("videoGrid");
      document.getElementById("videoCount").innerText = `${videos.length}টি হট ভিডিও সক্রিয়`;
      container.innerHTML = "";

      if(videos.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-slate-500 col-span-full">এই ফিল্টারে কোনো ভিডিও পাওয়া যায়নি!</div>`;
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
              <span class="text-[10px] font-mono bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded font-bold">
                ${v.is_shorts ? '⚡ Shorts' : '📺 Long'}
              </span>
              <span class="text-[11px] font-mono text-emerald-400 font-bold">+${v.velocity.toLocaleString()}/hr গতি</span>
            </div>
            
            <h3 class="text-xs font-bold text-slate-100 line-clamp-2">${v.title}</h3>
            <span class="text-[10px] text-cyan-400 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800 inline-block">${v.category_name}</span>
          </div>

          <!-- Meta Copy Box -->
          <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 space-y-1.5">
            <div class="flex justify-between items-center text-[11px]">
              <span class="font-bold text-cyan-400">আইডিয়া মেটা বক্স:</span>
              <button onclick="copyMeta(${index})" class="bg-cyan-500 text-slate-950 font-bold px-2.5 py-0.5 rounded text-[10px]">কপি 📋</button>
            </div>
            <textarea id="metaBox-${index}" readonly class="w-full h-12 bg-slate-900 border border-slate-800 rounded p-1.5 text-[10px] text-slate-300 font-mono focus:outline-none">টাইটেল: ${v.title}
হ্যাসট্যাগ: #Trending #Viral #${v.category_key}</textarea>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function copyMeta(index) {
      const box = document.getElementById(`metaBox-${index}`);
      box.select();
      document.execCommand("copy");
      alert("✅ মেটাডাটা ও হ্যাসট্যাগ কপি সফল হয়েছে!");
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
    
    # সারাদিন স্ক্যান করে হাজার হাজার ভিডিওর ডাটা ক্যাটাগরি অনুযায়ী সাজানোর মক ফিড
    return {
        "last_updated": now_str,
        "breakout_videos": [
            {"id": "kJQP7kiw5Fk", "title": "Cartoon Animation Story - 24/7 Hot Viral Feed #1", "velocity": 32000, "is_shorts": False, "category_key": "animation", "category_name": "কার্টুন ও অ্যানিমেশন"},
            {"id": "9bZkp7q19f0", "title": "Fast Facts & Secrets - Trending Short #2", "velocity": 48000, "is_shorts": True, "category_key": "tech", "category_name": "টেক ও তথ্য"},
            {"id": "JGwWNGJdvx8", "title": "Ultimate Roasting & Comedy Skit #3", "velocity": 19000, "is_shorts": False, "category_key": "comedy", "category_name": "কমেডি ও রোস্টিং"},
            {"id": "fJ9rUzIMcZQ", "title": "Top Gaming Highlights Live Stream #4", "velocity": 24000, "is_shorts": False, "category_key": "gaming", "category_name": "গেমিং"}
        ],
        "recommendation": "সারাদিনের অ্যানালাইসিস বলছে: বর্তমানে 'কার্টুন অ্যানিমেশন' এবং 'শর্ট ফ্যাক্টস' ক্যাটাগরির ভিডিওগুলোতে দর্শক এনগেজমেন্ট সবচেয়ে বেশি। নতুন চ্যানেলে এই ক্যাটাগরি নিয়ে কাজ করলে দ্রুত মিলিয়নের কাছাকাছি পৌঁছানো সম্ভব।"
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
            await asyncio.sleep(15)
            await websocket.send_json(fetch_youtube_data())
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)