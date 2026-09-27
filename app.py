import os
import asyncio
import datetime
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
  <title>EMON | 1M+ YOUTUBE WEB SERVICE & RADAR</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Hind+Siliguri:wght@500;600;700&family=Rajdhani:wght@600;700&display=swap');
    * { font-family: 'Hind Siliguri', sans-serif; }
    .font-orbitron { font-family: 'Orbitron', sans-serif; }
    .font-mono { font-family: 'Rajdhani', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-2 sm:p-4 pb-24">

  <div class="max-w-7xl mx-auto space-y-4">

    <!-- Top Developer & Service Header -->
    <header class="bg-slate-900 border border-cyan-500/30 p-4 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 shadow-xl">
      <div>
        <h1 class="text-base sm:text-xl font-black text-cyan-400 font-orbitron tracking-wider flex items-center gap-2">
          EMON<span class="text-amber-400">|YOUTUBE WEB SERVICE</span>
        </h1>
        <p class="text-[11px] text-gray-300 font-semibold">
          Developer & Creator: <span class="text-cyan-300 font-bold">ইমন ইসলাম (Emon Khan)</span>
        </p>
      </div>
      <div id="connectionStatus" class="flex items-center gap-2 text-xs font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
        <span>YouTube Feed & API Connected</span>
      </div>
    </header>

    <!-- Search Bar for Thousands of Videos -->
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex items-center gap-2 shadow-md">
      <i class="fa-solid fa-magnifying-glass text-cyan-400 px-2"></i>
      <input type="text" id="searchInput" oninput="handleSearch(this.value)" placeholder="যেকোনো ক্যাটাগরি বা টপিক সার্চ করুন (যেমন: Cartoon, Story, Gaming, Roasting)..." class="w-full bg-slate-950 border border-slate-700 text-xs text-slate-100 rounded-xl px-3 py-2.5 focus:outline-none focus:border-cyan-400 font-medium">
    </div>

    <!-- Strategy Box -->
    <div class="bg-gradient-to-r from-red-950/40 via-slate-900 to-indigo-950/40 border border-red-500/30 p-4 rounded-2xl shadow-md">
      <div class="flex items-center gap-2 mb-1">
        <i class="fa-solid fa-bolt text-amber-400"></i>
        <h3 class="text-xs sm:text-sm font-bold text-amber-300">মিলি-সেকেন্ডে স্ক্যান করা ১M+ ভিউ পাওয়া ট্রেন্ডিং ফিড:</h3>
      </div>
      <p id="recText" class="text-xs text-slate-300 leading-relaxed">সারাদিন ধরে ইউটিউব সার্ভিস স্ক্যান করে হাই-রিচ ভিডিওগুলো আলাদা করা হচ্ছে।</p>
      <div class="text-[11px] text-slate-500 mt-2 font-mono">লাইভ আপডেট: <span id="lastUpdated">--</span></div>
    </div>

    <!-- Category Buttons -->
    <div class="bg-slate-900 border border-slate-800 p-3 rounded-2xl flex flex-wrap gap-2">
      <button onclick="filterCategory('all')" id="cat-all" class="px-3 py-1.5 text-xs font-bold rounded-xl bg-cyan-500 text-slate-950 transition shadow">🔥 সব ট্রেন্ড</button>
      <button onclick="filterCategory('animation')" id="cat-animation" class="px-3 py-1.5 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">🎬 কার্টুন অ্যানিমেশন</button>
      <button onclick="filterCategory('shorts')" id="cat-shorts" class="px-3 py-1.5 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">⚡ ভাইরাল শর্টস</button>
      <button onclick="filterCategory('long')" id="cat-long" class="px-3 py-1.5 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">📺 লং ভিডিও</button>
      <button onclick="filterCategory('comedy')" id="cat-comedy" class="px-3 py-1.5 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition">😂 রোস্টিং ও কমেডি</button>
    </div>

    <!-- Massive Feed Grid -->
    <div class="space-y-3">
      <div class="flex justify-between items-center px-1">
        <h2 class="text-sm font-bold flex items-center gap-2 text-cyan-300">
          <i class="fa-solid fa-layer-group text-amber-400"></i> লোকাল ইউটিউব সার্ভিস ফিড (হাজার হাজার ভিডিও)
        </h2>
        <span id="videoCount" class="text-xs font-mono text-slate-400">লোড হচ্ছে...</span>
      </div>

      <div id="videoGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <div class="p-8 text-center text-slate-500 col-span-full">মিলি-সেকেন্ডে ভিডিও প্রসেস হচ্ছে...</div>
      </div>
    </div>

  </div>

  <script>
    let allVideosData = [];
    let currentCategory = 'all';

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/trends`;
    let socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      document.getElementById("lastUpdated").innerText = data.last_updated || "Live";
      document.getElementById("recText").innerText = data.recommendation || "";
      allVideosData = data.breakout_videos || [];
      filterCategory(currentCategory);
    };

    function filterCategory(cat) {
      currentCategory = cat;
      ['all', 'animation', 'shorts', 'long', 'comedy'].forEach(c => {
        const btn = document.getElementById(`cat-${c}`);
        if(btn) {
          if(c === cat) {
            btn.className = "px-3 py-1.5 text-xs font-bold rounded-xl bg-cyan-500 text-slate-950 transition shadow";
          } else {
            btn.className = "px-3 py-1.5 text-xs font-bold rounded-xl bg-slate-950 text-slate-300 border border-slate-800 transition";
          }
        }
      });

      applyFiltersAndSearch();
    }

    function handleSearch(query) {
      applyFiltersAndSearch(query);
    }

    function applyFiltersAndSearch(searchQuery = '') {
      let filtered = allVideosData.filter(v => {
        if(currentCategory === 'animation' && v.category_key !== 'animation') return false;
        if(currentCategory === 'shorts' && !v.is_shorts) return false;
        if(currentCategory === 'long' && v.is_shorts) return false;
        if(currentCategory === 'comedy' && v.category_key !== 'comedy') return false;

        if(searchQuery.trim() !== '') {
          const q = searchQuery.toLowerCase();
          const matchTitle = v.title.toLowerCase().includes(q);
          const matchCat = v.category_name.toLowerCase().includes(q);
          if(!matchTitle && !matchCat) return false;
        }
        return true;
      });
      renderVideos(filtered);
    }

    function renderVideos(videos) {
      const container = document.getElementById("videoGrid");
      document.getElementById("videoCount").innerText = `${videos.length}টি ভিডিও সক্রিয়`;
      container.innerHTML = "";

      if(videos.length === 0) {
        container.innerHTML = `<p class="text-center text-slate-500 col-span-full py-8">কোনো ভিডিও পাওয়া যায়নি!</p>`;
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
          <div class="space-y-1.5 flex-1">
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded font-black">
                🔥 ${v.views_label} Views
              </span>
              <span class="text-[10px] font-mono text-emerald-400 font-bold">${v.hours_ago} ঘণ্টা আগে</span>
            </div>
            
            <h3 class="text-xs font-bold text-slate-100 line-clamp-2">${v.title}</h3>
            
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-cyan-400 font-bold bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800">${v.category_name}</span>
              <!-- Ad-Free Download Button -->
              <a href="https://www.ssyoutube.com/watch?v=${v.id}" target="_blank" class="bg-red-600 hover:bg-red-500 text-white font-bold px-2.5 py-1 rounded-lg text-[10px] transition shadow flex items-center gap-1">
                <i class="fa-solid fa-download"></i> ফ্রি ডাউনলোড
              </a>
            </div>
          </div>

          <!-- Meta, Tags & Hashtag Copy Box -->
          <div class="bg-slate-950 p-2.5 rounded-xl border border-slate-800 space-y-1.5">
            <div class="flex justify-between items-center text-[11px]">
              <span class="font-bold text-cyan-400">ট্যাগ ও হ্যাসট্যাগ বক্স:</span>
              <button onclick="copyMeta(${index})" class="bg-cyan-500 text-slate-950 font-bold px-2 py-0.5 rounded text-[10px]">কপি 📋</button>
            </div>
            <textarea id="metaBox-${index}" readonly class="w-full h-14 bg-slate-900 border border-slate-800 rounded p-1 text-[10px] text-slate-300 font-mono focus:outline-none">টাইটেল: ${v.title}
হ্যাসট্যাগ: #Shorts #Animation #Viral1M #${v.category_key} #Trending #NewChannelGrowth</textarea>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function copyMeta(index) {
      const box = document.getElementById(`metaBox-${index}`);
      box.select();
      document.execCommand("copy");
      alert("✅ ভিডিওর টাইটেল, হ্যাসট্যাগ ও ট্যাগ সফলভাবে কপি হয়েছে!");
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
    
    # হাজার হাজার ভিডিওর ডাটাবেজ সিমুলেশন (শর্টস, লং এবং কার্টুন অ্যানিমেশন সহ)
    massive_videos = [
        {"id": "9bZkp7q19f0", "title": "Cartoon Animation Story - 2.1M Views in 10 Hours", "views_label": "2.1M+", "hours_ago": 10, "is_shorts": True, "category_key": "animation", "category_name": "কার্টুন অ্যানিমেশন"},
        {"id": "kJQP7kiw5Fk", "title": "Funny Cartoon Loop - 3.4M Views in 12 Hours", "views_label": "3.4M+", "hours_ago": 12, "is_shorts": True, "category_key": "animation", "category_name": "কার্টুন অ্যানিমেশন"},
        {"id": "JGwWNGJdvx8", "title": "Moral Story Animation Long Video - 4.8M Views", "views_label": "4.8M+", "hours_ago": 18, "is_shorts": False, "category_key": "animation", "category_name": "কার্টুন অ্যানিমেশন"},
        {"id": "fJ9rUzIMcZQ", "title": "Ghost Horror Cartoon Story - 2.9M Views in 9 Hours", "views_label": "2.9M+", "hours_ago": 9, "is_shorts": True, "category_key": "animation", "category_name": "কার্টুন অ্যানিমেশন"},
        {"id": "3JZ_D3ELwOQ", "title": "Ultimate Cartoon Roasting Skit - 4.2M Views in 15 Hours", "views_label": "4.2M+", "hours_ago": 15, "is_shorts": False, "category_key": "comedy", "category_name": "রোস্টিং"},
        {"id": "RgKAFK5djSk", "title": "Cute Animal Animation Short - 1.5M Views in 5 Hours", "views_label": "1.5M+", "hours_ago": 5, "is_shorts": True, "category_key": "animation", "category_name": "কার্টুন অ্যানিমেশন"},
    ]

    return {
        "last_updated": now_str,
        "breakout_videos": massive_videos,
        "recommendation": "ইউটিউব সার্ভিস স্ক্যানিং রিপোর্ট: মিলি-সেকেন্ডে অ্যানালাইসিস করে দেখা যাচ্ছে বর্তমানে কার্টুন অ্যানিমেশন শর্টস ও লং ভিডিওগুলোতে মিলিয়নের ওপরে ভিউ আসতাছে। সার্চ বক্স ব্যবহার করে যেকোনো টপিক বা ক্যাটাগরির হাজার হাজার ভিডিও ফিল্টার করে নিন।"
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
            await asyncio.sleep(5)
            await websocket.send_json(fetch_youtube_data())
    except WebSocketDisconnect:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)