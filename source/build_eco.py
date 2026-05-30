#!/usr/bin/env python3
"""build_eco.py — adapt Phil's /ecosystem/ genealogy+timeline to the metals data.
Reshapes data/acmet-graph.json into the apps.json model the ecosystem page expects,
then forks ecosystem/index.html with the data inlined + links repointed to our flat
profile pages. Output: site/lineage.html"""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ECO = os.path.expanduser("~/Documents/claude/philrenato-web/ecosystem/index.html")
G = json.load(open(os.path.join(HERE, "data", "acmet-graph.json")))

BUILT = {  # node-id -> profile page basename (slug must match the file so links work)
 "crafts/metalsdirectorypage/s272.html":"phil-renato","crafts/metalsdirectorypage/p82.html":"mary-lee-hu",
 "crafts/metalsdirectorypage/p97.html":"stanley-lechtzin","crafts/metalsdirectorypage/p88.html":"daniella-kerner",
 "crafts/metalsdirectorypage/p170.html":"vickie-sedman","gap/rebecca-strzelec":"rebecca-strzelec",
 "gap/skip-hunter":"skip-hunter",
}

# unique clean slug per node
used = set(); slug = {}
def mk(idd, name):
    if idd in BUILT:
        s = BUILT[idd]
    else:
        s = re.sub(r"[^a-z0-9]+","-",(name or idd).lower()).strip("-") or "node"
    base = s; i = 2
    while s in used: s = f"{base}-{i}"; i += 1
    used.add(s); slug[idd] = s; return s

nodes = {n["id"]: n for n in G["nodes"]}
for n in G["nodes"]:
    mk(n["id"], n["name"])

# adjacency
out_edges = collections.defaultdict(list); in_edges = collections.defaultdict(list)
for e in G["edges"]:
    out_edges[e["from"]].append(e); in_edges[e["to"]].append(e)

def yr_date(y, fallback):
    return (f"{y}-01-01", False) if y else (f"{fallback}-01-01", True)

apps = []
for n in G["nodes"]:
    nid = n["id"]; isprog = n["kind"] == "program"
    fb = 1965 if isprog else 1945
    ds, uncertain = yr_date(n.get("date"), fb)
    # ancestors = teachers + schools you studied at (true lineage, points back in time)
    anc = []
    for e in out_edges[nid]:
        if e["type"] in ("studied-under","studied-at") and e["to"] in slug:
            anc.append({"ref": slug[e["to"]], "type":"app", "relationship": e["type"].replace("-"," ")})
    # descendants = students (who studied under you) + your program's faculty/alumni
    desc = []
    for e in in_edges[nid]:
        if e["type"] == "studied-under" and e["from"] in slug:
            desc.append({"ref": slug[e["from"]], "type":"app", "relationship":"taught"})
        if isprog and e["type"] in ("studied-at","faculty-of","taught-at") and e["from"] in slug:
            desc.append({"ref": slug[e["from"]], "type":"app", "relationship": e["type"].replace("-"," ")})
    apps.append({
        "slug": slug[nid], "name": n["name"],
        "genre": n["kind"], "state": n["status"], "role": n["kind"],
        "dateStarted": ds, "dateFirstShipped": ds, "uncertainDates": uncertain,
        "private": nid not in BUILT,   # only built pages get a clickable link
        "tagline": (n.get("summary") or "")[:160],
        "conceptualAncestors": anc, "conceptualDescendants": desc,
    })

DATA = {"_generated":"2026-05-30","_note":"Academic Metals Directory lineage",
        "apps": apps, "ancestors": []}
print(f"eco apps: {len(apps)}  (linked edges in/out remapped)")

# ---- fork the ecosystem page ----
html = open(ECO).read()
reps = [
 ("const res = await fetch('/data/apps.json', { cache: 'no-store' });",
  "const res = {ok:true, json: async()=>(__ACMET_DATA__)};"),
 ("const res = await fetch('/data/energy.json', { cache: 'no-store' });",
  "const res = {ok:false};"),
 ("`/${esc(a.slug)}/`", "`${esc(a.slug)}.html`"),
 ("/${esc(app.slug)}/", "${esc(app.slug)}.html"),
 ("/${esc(focal.slug)}/", "${esc(focal.slug)}.html"),
 ("`/${a.slug}/`", "`${a.slug}.html`"),
 ("let gnZoomYears = 30;", "let gnZoomYears = 100;"),
 ("let gnCenterYear = 2020;", "let gnCenterYear = 1978;"),
 ("<title>graphing connections — renato.design</title>",
  "<title>Academic Metals Directory — lineage & timeline</title>"),
 ("Apps in various views, situated in historical and speculative contexts.",
  "The metals lineage — people and programs across a century: who taught whom, who came from where."),
 ("apps · positioned by date started", "people & programs · positioned by year"),
]
missing = [a for a, _ in reps if a not in html]
if missing:
    print("WARN: patterns not found:", len(missing))
    for m in missing: print("   -", m[:60])
for a, b in reps:
    html = html.replace(a, b)
html = html.replace("__ACMET_DATA__", json.dumps(DATA))
# a small back-link to the directory
html = html.replace("<body>", '<body><a href="./" style="position:fixed;top:14px;right:16px;z-index:99;'
                    'color:#8a8678;text-decoration:none;font:12px sans-serif">← directory</a>', 1)
open(os.path.join(HERE, "site", "lineage.html"), "w").write(html)
print("wrote site/lineage.html", len(html), "bytes")
