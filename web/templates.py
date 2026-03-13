"""
HTML templates for the marshmallow toasting web interface.
"""


def get_index_html() -> str:
    """Get the main HTML interface."""
    return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Auto-Toast Marshmallow</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0c10;color:#d4d4d4;
     font-family:'Segoe UI',system-ui,sans-serif;
     display:flex;flex-direction:column;height:100vh;overflow:hidden}

/* header */
header{display:flex;align-items:center;justify-content:space-between;
       padding:10px 20px;flex-shrink:0;
       background:linear-gradient(90deg,#0f0f1a,#1a1a2e);
       border-bottom:1px solid #2a2a3a}
.logo{display:flex;align-items:center;gap:10px}
.logo-icon{font-size:1.6rem;filter:drop-shadow(0 0 8px #f7971e)}
.logo h1{font-size:1.15rem;font-weight:700;letter-spacing:2px;
          background:linear-gradient(90deg,#f7971e,#ffd200);
          -webkit-background-clip:text;-webkit-text-fill-color:transparent}

/* buttons */
.btn-row{display:flex;gap:10px}
.btn{padding:9px 28px;border:none;border-radius:8px;
     font-size:.95rem;font-weight:700;cursor:pointer;
     transition:transform .12s,box-shadow .12s,opacity .2s}
.btn:active{transform:scale(.95)}
#btn-start{background:linear-gradient(135deg,#f7971e,#ffd200);color:#111;
            box-shadow:0 0 20px #f7971e99}
#btn-start:disabled{background:#3a3a3a;color:#666;box-shadow:none;cursor:not-allowed}
#btn-stop{background:linear-gradient(135deg,#e84393,#ff4040);color:#fff;
           box-shadow:0 0 16px #e8439366;display:none}

/* layout */
.main{display:flex;flex:1;overflow:hidden}
.video-panel{flex:1;padding:12px;background:#06070b;overflow:auto}
.video-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;height:100%}
.feed-card{display:flex;flex-direction:column;min-height:280px;background:#11131b;
         border:1px solid #1f2430;border-radius:12px;overflow:hidden;
         box-shadow:0 16px 40px rgba(0,0,0,.22)}
.feed-card.wide{grid-column:1 / -1}
.feed-head{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;
         background:linear-gradient(90deg,#141826,#1a2030);border-bottom:1px solid #262d3c}
.feed-title{font-size:.8rem;letter-spacing:1.3px;color:#e6ecff;text-transform:uppercase}
.feed-sub{font-size:.72rem;color:#78829a}
.feed-body{position:relative;flex:1;background:#000;display:flex;align-items:center;justify-content:center}
.feed-body img{width:100%;height:100%;object-fit:contain;display:block;background:#000}

/* side panel */
.side{width:320px;display:flex;flex-direction:column;gap:10px;
      padding:12px;background:#0e0e16;border-left:1px solid #1e1e2e;
      overflow-y:auto;flex-shrink:0}

/* card */
.card{background:#13131f;border:1px solid #1f1f30;border-radius:10px;padding:14px}
.card-title{font-size:.72rem;color:#555;letter-spacing:1.5px;
            text-transform:uppercase;margin-bottom:10px}

/* phase badge */
.badge{display:inline-block;padding:4px 14px;border-radius:20px;
       font-size:.82rem;font-weight:700;letter-spacing:1px;transition:all .3s}
.ph-idle        {background:#1c1c1c;color:#666}
.ph-starting    {background:#1a1a3a;color:#6060ff}
.ph-positioning {background:#0f2740;color:#40b4ff}
.ph-calibrating {background:#2a2000;color:#ffd060}
.ph-toasting    {background:#2a1200;color:#ff9040}
.ph-done        {background:#002a08;color:#40ff70}
.ph-error       {background:#2a0000;color:#ff5050}

#msg{font-size:.82rem;color:#aaa;margin-top:8px;min-height:1.1em;line-height:1.4}

/* toast ring */
.ring-wrap{display:flex;justify-content:center;padding:6px 0}
.ring{position:relative;width:90px;height:90px}
.ring svg{transform:rotate(-90deg)}
.ring-bg{fill:none;stroke:#1e1e2e;stroke-width:8}
.ring-fill{fill:none;stroke-width:8;stroke-linecap:round;
           transition:stroke-dashoffset .5s ease,stroke .4s}
.ring-text{position:absolute;inset:0;display:flex;flex-direction:column;
           align-items:center;justify-content:center}
.ring-pct{font-size:1.3rem;font-weight:700;color:#ffd200}
.ring-lbl{font-size:.6rem;color:#666;letter-spacing:1px}

/* speed row */
.speed-row{display:flex;align-items:center;gap:8px;margin-top:8px}
.speed-label{font-size:.72rem;color:#555;width:40px}
.speed-track{flex:1;background:#1e1e2e;border-radius:4px;height:8px}
.speed-fill{height:100%;border-radius:4px;
            background:linear-gradient(90deg,#00c6ff,#0072ff);transition:width .3s}
.speed-val{font-size:.72rem;color:#aaa;width:24px;text-align:right}

/* detection stats */
.stats-row{display:flex;justify-content:space-between;margin-top:8px;padding:6px 0;
           border-top:1px solid #1f1f30;font-size:.7rem;color:#888}
.stats-item{text-align:center}
.stats-value{color:#ffd200;font-weight:700}

/* steps */
.steps{list-style:none;display:flex;flex-direction:column;gap:4px}
.steps li{padding:7px 10px;border-radius:6px;font-size:.8rem;
           color:#444;border-left:3px solid #1f1f30;transition:all .35s}
.steps li.s-active{color:#ffd060;border-color:#ffd060;background:#1e1800}
.steps li.s-done  {color:#60ff80;border-color:#4caf50;background:#001408}

/* log */
#log{font-size:.72rem;color:#5a8060;font-family:'Courier New',monospace;
     height:150px;overflow-y:auto;background:#08080e;border-radius:6px;
     padding:8px;display:flex;flex-direction:column-reverse;
     scrollbar-width:thin;scrollbar-color:#2a2a3a #0a0a12}
#log p{margin:1px 0;word-break:break-all;transition:color .6s}
#log p.new{color:#b8ffb8}

@media (max-width: 1200px){
    .main{flex-direction:column}
    .side{width:100%;border-left:none;border-top:1px solid #1e1e2e}
    .video-grid{grid-template-columns:1fr}
    .feed-card.wide{grid-column:auto}
}
</style>
</head>
<body>

<header>
  <div class="logo">
    <span class="logo-icon">🍡</span>
    <h1>AUTO-TOAST  MARSHMALLOW</h1>
  </div>
  <div class="btn-row">
    <button class="btn" id="btn-start" onclick="doStart()">▶ Start</button>
    <button class="btn" id="btn-stop"  onclick="doStop()">⏹ Stop</button>
  </div>
</header>

<div class="main">
  <div class="video-panel">
        <div class="video-grid">
            <section class="feed-card">
                <div class="feed-head">
                    <span class="feed-title">Raw Camera</span>
                    <span class="feed-sub">Original camera feed</span>
                </div>
                <div class="feed-body">
                    <img id="feed-raw" src="/stream/raw.mjpg" alt="raw camera feed">
                </div>
            </section>

            <section class="feed-card">
                <div class="feed-head">
                    <span class="feed-title">Heat Analysis</span>
                    <span class="feed-sub">Reference difference heatmap</span>
                </div>
                <div class="feed-body">
                    <img id="feed-processed" src="/stream/processed.mjpg" alt="processed camera feed">
                </div>
            </section>

            <section class="feed-card wide">
                <div class="feed-head">
                    <span class="feed-title">YOLO Detection</span>
                    <span class="feed-sub">Object detection with ROI analysis</span>
                </div>
                <div class="feed-body">
                    <img id="feed-yolo" src="/stream/yolo.mjpg" alt="yolo detection feed">
                </div>
            </section>
        </div>
  </div>

  <div class="side">

    <div class="card">
      <div class="card-title">系統狀態</div>
      <span class="badge ph-idle" id="badge">IDLE</span>
      <p id="msg">Ready. Press Start to begin.</p>
    </div>

    <div class="card">
      <div class="card-title">熟度 &amp; 轉速</div>
      <div class="ring-wrap">
        <div class="ring">
          <svg viewBox="0 0 90 90" width="90" height="90">
            <circle class="ring-bg"   cx="45" cy="45" r="36"/>
            <circle class="ring-fill" cx="45" cy="45" r="36"
                    id="ring-arc" stroke="#60ff60"
                    stroke-dasharray="226" stroke-dashoffset="226"/>
          </svg>
          <div class="ring-text">
            <span class="ring-pct" id="ring-pct">0%</span>
            <span class="ring-lbl">TOAST</span>
          </div>
        </div>
      </div>
      <div class="speed-row">
        <span class="speed-label">Speed</span>
        <div class="speed-track">
          <div class="speed-fill" id="spd-fill" style="width:0%"></div>
        </div>
        <span class="speed-val" id="spd-val">0</span>
      </div>
      <div class="stats-row">
        <div class="stats-item">
          <div class="stats-value" id="yolo-rate">0%</div>
          <div>YOLO</div>
        </div>
        <div class="stats-item">
          <div class="stats-value" id="roi-rate">0%</div>
          <div>ROI</div>
        </div>
        <div class="stats-item">
          <div class="stats-value" id="total-detections">0</div>
          <div>Total</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">執行步驟</div>
      <ul class="steps">
        <li id="s1">① 移動至火源位置 (180°)</li>
        <li id="s2">② 拍攝參考照片</li>
        <li id="s3">③ 開始 360° 旋轉</li>
        <li id="s4">④ 監控並自動調速</li>
        <li id="s5">⑤ 回到原位 — 完成！</li>
      </ul>
    </div>

    <div class="card" style="flex:1">
      <div class="card-title">系統日誌</div>
      <div id="log"></div>
    </div>

  </div>
</div>

<script>
const CIRC = 2 * Math.PI * 36;

const PHASE_STEPS = {
  positioning: {active:[1], done:[]},
  calibrating: {active:[2], done:[1]},
  toasting:    {active:[3,4], done:[1,2]},
  done:        {active:[], done:[1,2,3,4,5]},
};

function ringColor(p){
  if(p < 0.40) return '#60ff80';
  if(p < 0.75) return '#ffd200';
  return '#ff6030';
}

function applyStatus(s){
  const badge = document.getElementById('badge');
  badge.textContent = s.phase.toUpperCase();
  badge.className   = 'badge ph-' + s.phase;

  document.getElementById('msg').textContent = s.message || '';

  const pct = Math.min(s.toast_score / 100, 1.0);
  const arc = document.getElementById('ring-arc');
  arc.style.strokeDashoffset = (CIRC * (1 - pct)).toFixed(1);
  arc.style.stroke           = ringColor(pct);
  document.getElementById('ring-pct').textContent = s.toast_score.toFixed(0) + '%';

  document.getElementById('spd-fill').style.width = Math.min(s.speed,100) + '%';
  document.getElementById('spd-val').textContent  = s.speed;

  for(let i=1;i<=5;i++) document.getElementById('s'+i).className='';
  const ph = PHASE_STEPS[s.phase] || {active:[],done:[]};
  ph.done.forEach(n   => { document.getElementById('s'+n).className='s-done';   });
  ph.active.forEach(n => { document.getElementById('s'+n).className='s-active'; });

  const running = !['idle','done','error'].includes(s.phase);
  document.getElementById('btn-start').disabled      = running;
  document.getElementById('btn-stop').style.display  = running ? 'inline-block' : 'none';
  document.getElementById('btn-start').style.display = running ? 'none' : 'inline-block';
}

async function updateDetectionStats(){
  try{
    const resp = await fetch('/api/detection-stats');
    const stats = await resp.json();
    document.getElementById('yolo-rate').textContent = stats.yolo_success_rate?.toFixed(1) + '%' || '0%';
    document.getElementById('roi-rate').textContent = stats.roi_usage_rate?.toFixed(1) + '%' || '0%';
    document.getElementById('total-detections').textContent = stats.total_detections || '0';
  }catch(e){}
}

async function pollStatus(){
  try{ 
    applyStatus(await (await fetch('/status')).json()); 
    updateDetectionStats();
  }catch(e){}
  setTimeout(pollStatus, 500);
}

const logEl  = document.getElementById('log');
const evtSrc = new EventSource('/events');
evtSrc.onmessage = e => {
  if(e.data.startsWith(':')) return;
  const p = document.createElement('p');
  p.textContent = e.data;
  p.className   = 'new';
  logEl.prepend(p);
  setTimeout(() => p.classList.remove('new'), 800);
  while(logEl.children.length > 120) logEl.removeChild(logEl.lastChild);
};

async function doStart(){
  document.getElementById('btn-start').disabled = true;
  await fetch('/start', {method:'POST'});
}
async function doStop(){
  await fetch('/stop', {method:'POST'});
}

pollStatus();
</script>
</body>
</html>"""