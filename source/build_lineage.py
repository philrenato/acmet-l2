#!/usr/bin/env python3
"""build_lineage.py — native lineage + timeline view for acmet-l2, cohered with
the directory pages and the map (dark, warm-glow). Ports the SYSTEM from Phil's
/ecosystem/ (timeline axis + genealogy connections + focal) but built fresh in
this project's design. Self-contained; D3 from CDN. Output: site/lineage.html"""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "data", "acmet-graph.json")))

BUILT = {
 "crafts/metalsdirectorypage/s272.html":"phil-renato.html","crafts/metalsdirectorypage/p82.html":"mary-lee-hu.html",
 "crafts/metalsdirectorypage/p97.html":"stanley-lechtzin.html","crafts/metalsdirectorypage/p88.html":"daniella-kerner.html",
 "crafts/metalsdirectorypage/p170.html":"vickie-sedman.html","gap/rebecca-strzelec":"rebecca-strzelec.html",
 "gap/skip-hunter":"skip-hunter.html",
}
deg = collections.Counter()
for e in G["edges"]:
    deg[e["from"]] += 1; deg[e["to"]] += 1

idx = {n["id"]: i for i, n in enumerate(G["nodes"])}
TYPES = {"studied-under":0, "studied-at":1, "taught-at":2, "faculty-of":3}
nodes = [{
    "n": n["name"], "y": n.get("date"),
    "k": 0 if n["kind"] == "person" else 1,
    "st": n["status"], "d": deg[n["id"]],
    "p": BUILT.get(n["id"]), "sum": (n.get("summary") or "")[:170],
} for n in G["nodes"]]
edges = [{"a": idx[e["from"]], "b": idx[e["to"]], "t": TYPES.get(e["type"], 1)}
         for e in G["edges"] if e["from"] in idx and e["to"] in idx]

# clamp junk years (a stray far-future/past date was stretching the axis)
for nd in nodes:
    if nd["y"] and not (1850 <= nd["y"] <= 2035):
        nd["y"] = None
dated = [n for n in nodes if n["y"]]
DATA = {"nodes": nodes, "edges": edges,
        "minY": min(n["y"] for n in dated), "maxY": max(n["y"] for n in dated),
        "undated": sum(1 for n in nodes if not n["y"])}

HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Academic Metals Directory — the lineage</title>
<style>
  :root{ --gold:#ffd27a; --gold-glow:#ffb24a; --prog:#7fb2e6; --prog-glow:#4a86c8;
         --dim:#6e6456; --ink:#e8e6df; --soft:#8a8678; }
  html,body{margin:0;height:100%;background:#07070b;color:var(--ink);overflow:hidden;
    font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
  svg{display:block;width:100vw;height:100vh;cursor:grab;touch-action:none}
  svg.drag{cursor:grabbing}
  .hint{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:5;
    font-size:11px;color:#7a776c;pointer-events:none;text-align:center}
  @media (max-width:600px){
    .hdr{max-width:62vw} .hdr h1{font-size:19px} .hdr .sub{font-size:11px}
    .legend{font-size:10px;bottom:30px} .panel{max-width:78vw;left:12px;bottom:34px} .hint{bottom:4px}
  }
  .hdr{position:fixed;top:20px;left:24px;z-index:5;pointer-events:none;max-width:46%}
  .hdr .k{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--soft)}
  .hdr h1{margin:4px 0 2px;font-size:26px;font-weight:600;letter-spacing:-.01em;
    text-shadow:0 0 24px rgba(255,140,40,.25)}
  .hdr .sub{font-size:12.5px;color:#a8a499}
  .bar{position:fixed;top:22px;right:24px;z-index:6;display:flex;gap:6px;align-items:center}
  .bar button{background:#15151c;color:#b6b2a6;border:1px solid #2a2a35;border-radius:7px;
    padding:6px 11px;font-size:12.5px;cursor:pointer;font-family:inherit}
  .bar button.on{background:#241a12;color:var(--gold);border-color:#4a3520;box-shadow:0 0 14px rgba(255,150,60,.2)}
  .bar a{color:var(--soft);text-decoration:none;font-size:12px;margin-left:8px}
  .bar a:hover{color:var(--ink)}
  .axis text{fill:#6b6760;font-size:11px}
  .axis line{stroke:#1c1c26}
  .tip{position:fixed;z-index:9;pointer-events:none;background:rgba(14,14,20,.97);
    border:1px solid #33323e;border-radius:8px;padding:8px 11px;max-width:280px;font-size:12.5px;
    opacity:0;transition:opacity .1s;box-shadow:0 8px 30px rgba(0,0,0,.6)}
  .tip b{color:var(--gold)} .tip .meta{color:#9a968a;font-size:11.5px}
  .panel{position:fixed;left:24px;bottom:22px;z-index:7;max-width:330px;background:rgba(14,14,20,.95);
    border:1px solid #2a2a35;border-radius:10px;padding:14px 16px;opacity:0;transition:opacity .15s;pointer-events:none}
  .panel.show{opacity:1;pointer-events:auto}
  .panel h3{margin:0 0 4px;font-size:17px;color:var(--ink)} .panel .r{font-size:12.5px;color:#b6b2a6}
  .panel a{color:var(--gold);font-size:12.5px;text-decoration:none} .panel .x{float:right;color:var(--soft);cursor:pointer}
  .legend{position:fixed;bottom:18px;right:24px;z-index:5;font-size:11.5px;color:#b6b2a6;text-align:right}
  .legend i{width:9px;height:9px;border-radius:50%;display:inline-block;margin:0 5px 0 12px;vertical-align:middle}
</style></head><body>
<div class="hdr"><div class="k">Academic Metals Directory</div><h1>the lineage</h1>
  <div class="sub">Every teacher and program across a century, placed by year. Hover for a name,
  zoom in to read them all, click anyone to trace their line.</div></div>
<div class="bar">
  <button id="b-time" class="on">timeline</button>
  <button id="b-line">lineage</button>
  <button id="b-all">all connections</button>
  <a href="./">← directory</a> <a href="map/">map →</a>
</div>
<div class="legend"><span><i style="background:#ffd27a;box-shadow:0 0 7px #ffb24a"></i>person</span>
  <span><i style="background:#7fb2e6;box-shadow:0 0 7px #4a86c8"></i>program</span>
  <span><i style="background:#6e6456"></i>deceased / closed</span></div>
<svg id="svg"></svg><div class="tip" id="tip"></div>
<div class="hint">pinch or scroll to zoom · drag to pan · tap a name</div>
<div class="panel" id="panel"></div>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>
const D = __DATA__, N = D.nodes, E = D.edges;
const svg = d3.select("#svg"), tip = d3.select("#tip"), panel = d3.select("#panel");
let W = innerWidth, H = innerHeight, mode = "time", focus = null, curK = 1;
let focusSet = null, showAllState = false;

const adj = N.map(()=>[]);
E.forEach((e,i)=>{ adj[e.a].push({o:e.b,e:i,dir:"out"}); adj[e.b].push({o:e.a,e:i,dir:"in"}); });

// landmark labels: the most-connected nodes, DECLUTTERED so they never overlap.
// (computed after layout, since it needs node positions.) Everyone else: hover, or zoom in.
let labelShow = new Set();
function computeLabels(){
  labelShow = new Set(); const placed=[];
  N.map((n,i)=>i).filter(i=>N[i]._set).sort((a,b)=>N[b].d-N[a].d).forEach(i=>{
    if(labelShow.size>=16) return;
    const x=N[i]._x, y=N[i]._y;
    if(placed.some(p=>Math.abs(p.x-x)<170 && Math.abs(p.y-y)<24)) return;
    placed.push({x,y}); labelShow.add(i);
  });
}

const x = d3.scaleLinear().domain([D.minY-3, D.maxY+3]);
const PAD=90, R=n=>Math.min(9, 3.6+Math.sqrt(n.d)*1.2);  // capped so dots don't bloat
const LANE=26;                                            // fixed: > max dot diameter, no overlap
let lanes=1, contentH=0;
function layout(){
  x.range([PAD, Math.max(1000,W)-PAD]);   // fit the screen width
  const dated = N.map((n,i)=>({n,i})).filter(d=>d.n.y).sort((a,b)=>a.n.y-b.n.y);
  const laneEnd=[];
  dated.forEach(d=>{ const px=x(d.n.y), r=R(d.n);
    let L=0; for(;L<laneEnd.length;L++){ if(px-r > laneEnd[L]) break; }
    if(L===laneEnd.length) laneEnd.push(0);
    laneEnd[L]=px+r*2+10; d.n._x=px; d.n._lane=L; d.n._set=true; });   // +10 = horizontal air
  lanes=Math.max(1,laneEnd.length); contentH=lanes*LANE;
  N.forEach(n=>{ if(n._set){ n._y = (n._lane - (lanes-1)/2)*LANE; } });
}
layout(); computeLabels();

const axisG = svg.append("g").attr("class","axis");
const root = svg.append("g");
const edgeG = root.append("g");
const nodeG = root.append("g");

function color(n, on=true){
  if(!on) return "#26262e";
  if(n.k===1) return (n.st==="active")?"#7fb2e6":(n.st==="closed")?"#4a5566":"#5f86a8";
  if(n.st==="deceased") return "#6e6456";
  if(n.st==="retired") return "#d9a24a";
  return "#ffd27a";
}
function glow(n){ return n.k===1 ? "#4a86c8" : "#ffb24a"; }

const link = edgeG.selectAll("path").data(E).join("path")
  .attr("fill","none").attr("stroke-linecap","round");
function edgePath(e){
  const a=N[e.a], b=N[e.b]; if(a._x==null||b._x==null) return null;
  const mx=(a._x+b._x)/2, my=(a._y+b._y)/2 - Math.min(90,Math.abs(a._x-b._x)*.18+24);
  return `M${a._x},${a._y} Q${mx},${my} ${b._x},${b._y}`;
}
link.attr("d", edgePath);

const node = nodeG.selectAll("g").data(N.map((n,i)=>({n,i})).filter(d=>d.n._set)).join("g")
  .attr("transform",d=>`translate(${d.n._x},${d.n._y})`).style("cursor","pointer");
node.append(d=>document.createElementNS("http://www.w3.org/2000/svg", d.n.k===1?"rect":"circle"));
node.select("circle").attr("r",d=>R(d.n));
node.select("rect").attr("width",d=>R(d.n)*1.7).attr("height",d=>R(d.n)*1.7)
  .attr("x",d=>-R(d.n)*.85).attr("y",d=>-R(d.n)*.85).attr("transform","rotate(45)").attr("rx",1);
node.selectAll("circle,rect").attr("fill",d=>color(d.n))
  .attr("stroke","rgba(255,255,255,.22)").attr("stroke-width",.5);
// labels
const label = node.append("text").text(d=>d.n.n)
  .attr("x",d=>R(d.n)+4).attr("y",3.5).attr("font-size",11.5).attr("fill","#d8d2c6")
  .attr("paint-order","stroke").attr("stroke","#07070b").attr("stroke-width",3).attr("stroke-linejoin","round")
  .style("pointer-events","none")
  .attr("display",d=>labelShow.has(d.i)?null:"none");
function relabel(){
  const showAll = curK > 1.9;
  label.attr("display",d=>{
      if(focus!=null) return (focusSet && focusSet.has(d.i))?null:"none";
      return (showAll||labelShow.has(d.i))?null:"none"; });
}

node.on("mousemove",(ev,d)=>{ tip.style("opacity",1).style("left",(ev.clientX+14)+"px").style("top",(ev.clientY+12)+"px")
    .html(`<b>${d.n.n}</b><br><span class="meta">${d.n.k===1?"program":"person"} · ${d.n.st}${d.n.y?" · "+d.n.y:""} · ${d.n.d} links</span>`); })
  .on("mouseleave",()=>tip.style("opacity",0))
  .on("click",(ev,d)=>{ ev.stopPropagation(); setFocus(d.i); });
svg.on("click",()=>setFocus(null));

function renderEdges(){
  const showAll = (mode==="all");
  const showLine = (mode!=="time") || focus!=null;
  let inFocus = new Set(), fEdges = new Set();
  if(focus!=null){ inFocus.add(focus); adj[focus].forEach(a=>{ inFocus.add(a.o); fEdges.add(a.e); }); }
  focusSet = focus!=null ? inFocus : null;
  link.attr("display",(e,i)=>{                 // index, not O(n) indexOf — was a perf trap
      if(focus!=null) return fEdges.has(i)?null:"none";
      if(showAll) return null;
      if(showLine) return e.t===0?null:"none";  // lineage view: teacher→student only
      return "none";
    })
    .attr("stroke",e=> e.t===0 ? "#ff9a3c" : "#5a8ac0")
    .attr("stroke-width",focus!=null?1.4:.6)
    .attr("stroke-opacity",focus!=null?.85:(showAll?.1:.28));
  node.selectAll("circle,rect")
    .attr("fill",d=> focus==null||inFocus.has(d.i) ? color(d.n) : color(d.n,false))
    .attr("fill-opacity",d=> focus==null||inFocus.has(d.i) ? .92 : .28)
    // glow only on the focused handful — not all 639 nodes (that was the real crash)
    .style("filter",d=> focus!=null && inFocus.has(d.i) ? `drop-shadow(0 0 6px ${glow(d.n)})` : null);
  relabel();
}
function setFocus(i){
  focus=i; renderEdges();
  if(i==null){ panel.classed("show",false); return; }
  const n=N[i];
  const teachers=adj[i].filter(a=>a.dir==="out"&&E[a.e].t===0).map(a=>N[a.o].n);
  const students=adj[i].filter(a=>a.dir==="in"&&E[a.e].t===0).map(a=>N[a.o].n);
  panel.classed("show",true).html(
    `<span class="x" onclick="event.stopPropagation();document.getElementById('svg').dispatchEvent(new Event('click'))">✕</span>`+
    `<h3>${n.n}</h3><div class="r">${n.k===1?"program":"person"} · ${n.st}${n.y?" · b. "+n.y:""}</div>`+
    (n.sum?`<div class="r" style="margin-top:6px">${n.sum}</div>`:"")+
    (teachers.length?`<div class="r" style="margin-top:6px"><b style="color:#ffb968">taught by:</b> ${teachers.join(", ")}</div>`:"")+
    (students.length?`<div class="r"><b style="color:#ffb968">students:</b> ${students.slice(0,12).join(", ")}${students.length>12?"…":""}</div>`:"")+
    (n.p?`<div style="margin-top:8px"><a href="${n.p}">open profile →</a></div>`:"")
  );
}

// year axis — screen space, from the current zoom transform
function drawAxis(t){
  const xs = t.rescaleX(x);
  const sel = axisG.selectAll("g").data(xs.ticks(12), d=>d);
  const g = sel.enter().append("g"); g.append("line"); g.append("text");
  sel.exit().remove();
  axisG.selectAll("g").attr("transform",d=>`translate(${xs(d)},0)`);
  axisG.selectAll("g").select("line").attr("y1",58).attr("y2",H).attr("stroke","#15151d");
  axisG.selectAll("g").select("text").attr("y",46).attr("text-anchor","middle").text(d=>d);
}

const zoom = d3.zoom().scaleExtent([0.4,16]).on("zoom",ev=>{
  curK = ev.transform.k; root.attr("transform",ev.transform); drawAxis(ev.transform);
  const sa = curK > 1.9;                       // only relabel when crossing the threshold (cheap)
  if(sa !== showAllState){ showAllState = sa; relabel(); }
});
svg.attr("width",W).attr("height",H).call(zoom)
  .on("mousedown.cur",()=>svg.classed("drag",true)).on("mouseup.cur",()=>svg.classed("drag",false));

// initial: scale so the whole cascade fits on screen, centered
function fit(){
  const k = Math.min(1, (H-150)/Math.max(1,contentH));
  svg.call(zoom.transform, d3.zoomIdentity.translate(0, H/2).scale(k));
}
fit(); renderEdges();

function setMode(m){ mode=m; ["time","line","all"].forEach(x=>d3.select("#b-"+x).classed("on",x===m));
  if(focus!=null) setFocus(null); renderEdges(); }
d3.select("#b-time").on("click",()=>setMode("time"));
d3.select("#b-line").on("click",()=>setMode("line"));
d3.select("#b-all").on("click",()=>setMode("all"));
addEventListener("resize",()=>{ W=innerWidth;H=innerHeight;svg.attr("width",W).attr("height",H);
  layout(); computeLabels(); node.attr("transform",d=>`translate(${d.n._x},${d.n._y})`);
  link.attr("d",edgePath); fit(); relabel(); });
</script></body></html>"""

out = HTML.replace("__DATA__", json.dumps(DATA, separators=(",",":")))
open(os.path.join(HERE, "site", "lineage.html"), "w").write(out)
print(f"wrote site/lineage.html  nodes={len(nodes)} edges={len(edges)} undated={DATA['undated']}")
