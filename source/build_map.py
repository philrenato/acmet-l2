#!/usr/bin/env python3
"""build_map.py — a 'hot' US map of the directory from data/acmet-graph.json.
Self-contained (data embedded); D3 + us-atlas from CDN for the geography.
Programs glow by state; size = how connected; color = status. Lineage-migration
arcs trace where people studied -> where they went on to teach.
Output: site/map/index.html"""
import json, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "data", "acmet-graph.json")))
nodes = {n["id"]: n for n in G["nodes"]}
deg = collections.Counter()
for e in G["edges"]:
    deg[e["from"]] += 1; deg[e["to"]] += 1

# placed program points
pts = []
for n in G["nodes"]:
    if n["kind"] == "program" and n["location"]:
        pts.append({"name": n["name"], "status": n["status"], "state": n["location"]["state"],
                    "lat": n["location"]["lat"], "lng": n["location"]["lng"],
                    "prec": n["location"].get("precision", "state"),
                    "w": deg[n["id"]], "summary": n["summary"],
                    "slug": n.get("pageslug")})

# lineage-migration flows: person's studied-at state -> taught-at state
prog_state = {n["id"]: n["location"]["state"] for n in G["nodes"]
              if n["kind"] == "program" and n["location"]}
studied = collections.defaultdict(set); taught = collections.defaultdict(set)
for e in G["edges"]:
    if e["type"] == "studied-at" and e["to"] in prog_state: studied[e["from"]].add(prog_state[e["to"]])
    if e["type"] == "taught-at" and e["to"] in prog_state: taught[e["from"]].add(prog_state[e["to"]])
flow = collections.Counter()
for pid in set(studied) | set(taught):
    for a in studied.get(pid, ()):
        for b in taught.get(pid, ()):
            if a != b: flow[(a, b)] += 1
CENT = {p["state"]: (p["lat"], p["lng"]) for p in pts}
flows = [{"from": a, "to": b, "n": n, "a": CENT[a], "b": CENT[b]}
         for (a, b), n in flow.items() if a in CENT and b in CENT]

state_counts = collections.Counter(p["state"] for p in pts)

# the projection is Albers-USA: points outside the US (Canada/Mexico/UK/AU
# schools the directory listed) can't render on it — count them for disclosure.
# The geocode overlay flags non-US institutions explicitly (a bare bounding box
# misses Toronto / Mexico City, which sit inside US lat/lng ranges).
_ov_path = os.path.join(HERE, "data", "geocode_cities.json")
NONUS = set()
if os.path.exists(_ov_path):
    NONUS = {r["name"].strip().lower() for r in json.load(open(_ov_path))["resolved"] if r.get("non_us")}

def in_us(p):
    return (p["name"].strip().lower() not in NONUS
            and 18 < p["lat"] < 72 and -170 < p["lng"] < -65)

n_outside = sum(1 for p in pts if not in_us(p))
DATA = {"points": pts, "flows": flows, "stateCounts": dict(state_counts),
        "n_programs": sum(1 for n in G["nodes"] if n["kind"] == "program"),
        "n_placed": len(pts) - n_outside,
        "n_people": sum(1 for n in G["nodes"] if n["kind"] == "person"),
        "n_state": sum(1 for p in pts if p["prec"] != "city" and in_us(p)),
        "n_outside": n_outside}

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Academic Metals Directory — the map</title>
<style>
  html,body{margin:0;height:100%;background:#07070b;color:#e8e6df;
    font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
  #map{display:block;width:100vw;height:100vh;touch-action:none;cursor:grab}
  #map:active{cursor:grabbing}
  .hint{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:5;
    font-size:11px;color:#7a776c;pointer-events:none;text-align:center;white-space:nowrap}
  @media (max-width:600px){
    .hdr h1{font-size:19px} .hdr .sub{font-size:11px;max-width:64vw}
    .legend{font-size:10.5px;bottom:34px} .legend span{margin-right:9px}
    .ctl{bottom:34px} .hint{bottom:6px}
  }
  .hdr{position:fixed;top:20px;left:24px;z-index:5;pointer-events:none}
  .hdr .k{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#8a8678}
  .hdr h1{margin:4px 0 2px;font-size:26px;font-weight:600;letter-spacing:-.01em;
    text-shadow:0 0 24px rgba(255,140,40,.25)}
  .hdr .sub{font-size:12.5px;color:#a8a499;max-width:430px}
  .legend{position:fixed;bottom:18px;left:24px;z-index:5;font-size:12px;color:#b6b2a6;max-width:520px}
  .legend span{display:inline-flex;align-items:center;margin-right:14px}
  .legend .note{margin-top:5px;font-size:10.5px;color:#7a776c;max-width:460px}
  .dot{width:10px;height:10px;border-radius:50%;margin-right:6px;display:inline-block}
  .dot.ring{width:9px;height:9px}
  .ctl{position:fixed;bottom:18px;right:24px;z-index:5;font-size:12px;color:#b6b2a6}
  .ctl label{cursor:pointer;-webkit-user-select:none;user-select:none}
  .tip{position:fixed;z-index:9;pointer-events:none;background:rgba(14,14,20,.96);
    border:1px solid #33323e;border-radius:8px;padding:8px 11px;max-width:280px;
    font-size:12.5px;color:#e8e6df;opacity:0;transition:opacity .1s;box-shadow:0 8px 30px rgba(0,0,0,.6)}
  .tip b{color:#ffb968}
  .tip a{color:#9ad0ff;text-decoration:none;pointer-events:auto} .tip a:hover{text-decoration:underline}
  .tip{pointer-events:auto}
  a.back{position:fixed;top:20px;right:24px;z-index:5;color:#8a8678;text-decoration:none;font-size:12px}
  a.back:hover{color:#e8e6df}
  .foot{position:fixed;bottom:3px;left:50%;transform:translateX(-50%);z-index:4;
    font-size:10px;color:#5d5a52;text-align:center;max-width:96vw;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .foot a{color:#7a776c;text-decoration:none} .foot a:hover{color:#a8a499}
  @media (max-width:600px){ .foot{display:none} .legend{max-width:86vw} .legend .note{max-width:80vw} }
</style></head><body>
<div class="hdr">
  <div class="k">Academic Metals Directory</div>
  <h1>where the craft is taught</h1>
  <div class="sub">__N_PLACED__ of __N_PROGRAMS__ US jewelry / metals / CAD-CAM programs, glowing by how
  connected they are. Arcs trace lineage migration — where people studied, then went on to teach.</div>
</div>
<a class="back" href="../">← the directory</a>
<svg id="map"></svg>
<div class="legend">
  <span><i class="dot" style="background:#ffd27a;box-shadow:0 0 8px #ffb24a"></i>active</span>
  <span><i class="dot" style="background:#e08b4a;box-shadow:0 0 8px #c0682a"></i>merged / renamed</span>
  <span><i class="dot" style="background:#8a4a4a;box-shadow:0 0 6px #6a2a2a"></i>closed</span>
  <span><i class="dot ring" style="background:transparent;border:1px dashed #b6b2a6;box-shadow:none"></i>location approximate (state-level)</span>
  <div class="note">bigger / brighter glow = more connected · arcs trace where people studied → went on to teach ·
  __N_STATE__ of __N_PLACED__ dots are placed at the state center, not the exact city ·
  __N_OUTSIDE__ schools outside the US are in the directory but not on this US map.</div>
</div>
<div class="ctl"><label><input type="checkbox" id="arcs" checked> lineage arcs</label></div>
<div class="hint">pinch or scroll to zoom · drag to pan · tap a dot</div>
<div class="foot">data from the recovered Tyler / Temple <a href="../">“Academic Metals Directory”</a>
  (Wayback), brought current in 2026 · generated __TODAY__ ·
  <a href="https://github.com/philrenato/acmet-l2">github.com/philrenato/acmet-l2</a></div>
<div class="tip" id="tip"></div>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
<script>
const DATA = __DATA__;
const svg = d3.select("#map"), tip = d3.select("#tip");
let W = innerWidth, H = innerHeight;
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0)/4294967295}
const COLOR = {active:"#ffd27a", merged:"#e08b4a", closed:"#8a4a4a", unknown:"#6f6f80"};
const GLOW  = {active:"#ffb24a", merged:"#c0682a", closed:"#6a2a2a", unknown:"#44444f"};

d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json").then(us=>{
  draw(us);
  addEventListener("resize", ()=>{W=innerWidth;H=innerHeight;svg.selectAll("*").remove();draw(us);});
});

function draw(us){
  svg.attr("width",W).attr("height",H);
  const states = topojson.feature(us, us.objects.states);
  const proj = d3.geoAlbersUsa().fitExtent([[40,90],[W-40,H-40]], states);
  const path = d3.geoPath(proj);
  const maxCount = Math.max(...Object.values(DATA.stateCounts));

  // a single zoomable/pannable viewport group holds everything (pinch on touch, wheel on desktop)
  const vp = svg.append("g").attr("class","vp");

  // heat: tint each state by program density
  const heat = d3.scaleSequential(t=>d3.interpolateRgb("#101018","#3a241a")(t)).domain([0,maxCount]);
  const byId = {}; // FIPS not needed; tint by centroid->state match is hard, so flat dark + per-state glow blobs
  vp.append("g").selectAll("path").data(states.features).join("path")
     .attr("d",path).attr("fill","#0e0e16").attr("stroke","#23232e").attr("stroke-width",.7);

  // city-accurate dots barely jitter (just to unstack); state-only dots spread to fill the state
  const P = p => { const j = p.prec==="city" ? .28 : 1.1;
    return proj([p.lng + (hash(p.name)-.5)*j*1.4, p.lat + (hash(p.name+"y")-.5)*j]); };

  // lineage-migration arcs
  const arcG = vp.append("g").attr("opacity",.5);
  const maxF = Math.max(1,...DATA.flows.map(f=>f.n));
  arcG.selectAll("path").data(DATA.flows).join("path").attr("d",f=>{
      const a=proj([f.a[1],f.a[0]]), b=proj([f.b[1],f.b[0]]); if(!a||!b)return null;
      const dx=b[0]-a[0],dy=b[1]-a[1],dr=Math.hypot(dx,dy)*1.3;
      return `M${a[0]},${a[1]}A${dr},${dr} 0 0,1 ${b[0]},${b[1]}`;
    }).attr("fill","none").attr("stroke","#ff9a3c")
      .attr("stroke-width",f=>.4+f.n/maxF*1.6).attr("stroke-opacity",f=>.12+f.n/maxF*.35)
      .attr("stroke-linecap","round");
  d3.select("#arcs").on("change",function(){arcG.attr("display",this.checked?null:"none")});

  // tooltip body — discloses approximate (state-level) placement + a link through
  // to the program's directory page (only when that page exists). Link is in the
  // tooltip so a first tap shows it without navigating away.
  function tipHTML(p){
    const approx = p.prec!=="city" ? `<br><span style="color:#8a8678">· location approximate (state-level)</span>` : "";
    const link = p.slug ? `<br><a href="../${p.slug}.html">open program page →</a>` : "";
    return `<b>${p.name}</b><br>${p.status} · ${p.state} · ${p.w} connections${approx}`+
           `<br><span style="color:#9a968a">${p.summary||""}</span>${link}`;
  }
  function showTip(ev,p){ tip.style("opacity",1)
      .style("left",Math.min(ev.clientX+14,innerWidth-240)+"px").style("top",(ev.clientY+12)+"px").html(tipHTML(p)); }

  // program glow dots — state-level dots render hollow/dashed + dimmer so the eye
  // knows they sit at the state center, not the exact city.
  const r = d3.scaleSqrt().domain([1, Math.max(2,d3.max(DATA.points,p=>p.w))]).range([3.5,16]);
  const g = vp.append("g");
  const dots = g.selectAll("circle").data(DATA.points.filter(p=>proj([p.lng,p.lat]))).join("circle")
    .attr("cx",p=>(P(p)||[-99,-99])[0]).attr("cy",p=>(P(p)||[-99,-99])[1])
    .attr("r",p=>r(p.w))
    .attr("fill",p=>p.prec==="city" ? (COLOR[p.status]||COLOR.unknown) : "transparent")
    .attr("fill-opacity",p=>p.prec==="city"?.85:0)
    .style("filter",p=>p.prec==="city"?`drop-shadow(0 0 ${r(p.w)*.9}px ${GLOW[p.status]||GLOW.unknown})`:"none")
    .attr("stroke",p=>p.prec==="city"?"rgba(255,255,255,.25)":(COLOR[p.status]||COLOR.unknown))
    .attr("stroke-opacity",p=>p.prec==="city"?1:.65)
    .attr("stroke-width",p=>p.prec==="city"?.5:1.1)
    .attr("stroke-dasharray",p=>p.prec==="city"?null:"3,2")
    .on("mousemove",(ev,p)=>showTip(ev,p))
    .on("mouseleave",()=>tip.style("opacity",0))
    .on("click",(ev,p)=>{ev.stopPropagation();showTip(ev,p);});

  // pinch (touch) + wheel (desktop) zoom, drag to pan
  const zoom = d3.zoom().scaleExtent([0.8,9]).on("zoom",ev=>vp.attr("transform",ev.transform));
  svg.call(zoom).on("dblclick.zoom",null);
  svg.on("click",()=>tip.style("opacity",0));  // tap empty space to dismiss tip

  // ?focus=<program slug> deep-link: pan/zoom to the dot + open its tooltip
  function readFocus(){ const m=/[?&]focus=([^&#]+)/.exec(location.search)||/#focus=([^&]+)/.exec(location.hash);
    return m?decodeURIComponent(m[1]).toLowerCase():null; }
  const fslug = readFocus();
  if(fslug){
    const p = DATA.points.find(d=>d.slug===fslug);
    if(p){
      const xy = proj([p.lng,p.lat]);
      if(xy){ const k=3.2, t=d3.zoomIdentity.translate(W/2-k*xy[0],H/2-k*xy[1]).scale(k);
        svg.transition().duration(650).call(zoom.transform,t)
           .on("end",()=>{ const c=P(p)||xy; const sx=W/2,sy=H/2;
             tip.style("opacity",1).style("left",Math.min(sx+14,innerWidth-240)+"px")
                .style("top",(sy+12)+"px").html(tipHTML(p)); });
      }
    }
  }
}
</script></body></html>"""

import datetime
out = (HTML.replace("__DATA__", json.dumps(DATA))
           .replace("__N_PLACED__", str(DATA["n_placed"]))
           .replace("__N_PROGRAMS__", str(DATA["n_programs"]))
           .replace("__N_STATE__", str(DATA["n_state"]))
           .replace("__N_OUTSIDE__", str(DATA["n_outside"]))
           .replace("__TODAY__", datetime.date.today().isoformat()))
os.makedirs(os.path.join(HERE, "site", "map"), exist_ok=True)
open(os.path.join(HERE, "site", "map", "index.html"), "w").write(out)
print(f"wrote site/map/index.html  ({DATA['n_placed']} dots, {len(DATA['flows'])} flows)")
