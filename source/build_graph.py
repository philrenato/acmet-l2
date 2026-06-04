#!/usr/bin/env python3
"""build_graph.py — export acmet.db as a connections graph with geography, the
backbone for the timeline/genealogy + US-map views.

Output: data/acmet-graph.json
  nodes[]  : people + programs, with date, status, location {state, lat, lng}, edges
  edges[]  : lineage + affiliation (studied-under / studied-at / taught-at / faculty)
  meta     : coverage stats
"""
import json, os, re, sqlite3, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()
TODAY_YEAR = datetime.date.today().year
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); con.row_factory = sqlite3.Row

# state name -> USPS, and USPS -> centroid (approx lat,lng)
STATES = {
 "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO",
 "Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID",
 "Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA",
 "Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
 "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ",
 "New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK",
 "Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD",
 "Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
 "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","District of Columbia":"DC",
}
CENTROID = {
 "AL":(32.8,-86.8),"AK":(64.0,-152.0),"AZ":(34.2,-111.7),"AR":(34.9,-92.4),"CA":(37.2,-119.7),
 "CO":(39.0,-105.5),"CT":(41.6,-72.7),"DE":(39.0,-75.5),"FL":(28.6,-82.4),"GA":(32.6,-83.4),
 "HI":(20.3,-156.4),"ID":(44.2,-114.5),"IL":(40.0,-89.2),"IN":(39.9,-86.3),"IA":(42.0,-93.5),
 "KS":(38.5,-98.4),"KY":(37.5,-85.3),"LA":(31.0,-92.0),"ME":(45.4,-69.2),"MD":(39.0,-76.7),
 "MA":(42.3,-71.8),"MI":(44.3,-85.4),"MN":(46.3,-94.3),"MS":(32.7,-89.7),"MO":(38.4,-92.5),
 "MT":(47.0,-109.6),"NE":(41.5,-99.8),"NV":(39.3,-116.6),"NH":(43.7,-71.6),"NJ":(40.2,-74.7),
 "NM":(34.4,-106.1),"NY":(42.9,-75.5),"NC":(35.5,-79.4),"ND":(47.4,-100.5),"OH":(40.3,-82.8),
 "OK":(35.6,-97.5),"OR":(43.9,-120.6),"PA":(40.9,-77.8),"RI":(41.7,-71.5),"SC":(33.9,-80.9),
 "SD":(44.4,-100.2),"TN":(35.9,-86.4),"TX":(31.5,-99.3),"UT":(39.3,-111.7),"VT":(44.1,-72.7),
 "VA":(37.5,-78.9),"WA":(47.4,-120.5),"WV":(38.6,-80.6),"WI":(44.6,-89.9),"WY":(43.0,-107.5),
 "DC":(38.9,-77.0),
}
# explicit overrides where the name/text doesn't reveal the state
OVERRIDE = {
 "kendall":"MI","cranbrook":"MI","tyler":"PA","temple":"PA","risd":"RI","rhode island school":"RI",
 "school of the art institute":"IL","saic":"IL","rochester institute":"NY","cooper union":"NY",
 "pratt":"NY","parsons":"NY","fashion institute":"NY","new paltz":"NY","alfred":"NY","skidmore":"NY",
 "savannah college":"GA","scad":"GA","lamar dodd":"GA","memphis college":"TN","appalachian center":"TN",
 "cleveland institute":"OH","columbus college":"OH","oberlin":"OH","bowling green":"OH","kent state":"OH",
 "haystack":"ME","penland":"NC","arrowmont":"TN","cranbrook academy":"MI","massachusetts college":"MA",
 "school for american craftsmen":"NY","nova scotia":"NS","emily carr":"BC",
 "edinboro":"PA","kutztown":"PA","indiana university of pennsylvania":"PA","moore college":"PA",
 "university of the arts":"PA","tyler school":"PA","carnegie":"PA","philadelphia college":"PA",
 "san diego state":"CA","long beach":"CA","oakland":"CA","california college":"CA","otis":"CA",
 "academy of art":"CA","san jose":"CA","fullerton":"CA","northridge":"CA","sonoma":"CA","mills":"CA",
 "eastern michigan":"MI","western michigan":"MI","northern michigan":"MI","wayne state":"MI",
 "grand valley":"MI","flint":"MI","interlochen":"MI","birmingham bloomfield":"MI",
 "miami university":"OH","miami jewelry":"FL","metairie":"LA","abilene":"TX","texas woman":"TX",
 "north texas":"TX","texas tech":"TX","southern methodist":"TX","san antonio":"TX",
 "boise":"ID","idaho state":"ID","montana":"MT","oregon school":"OR","oregon college":"OR",
 "pacific northwest college":"OR","marylhurst":"OR","lane community":"OR","mount hood":"OR",
 "washington university":"MO","kansas city art institute":"MO","missouri":"MO","webster":"MO","fontbonne":"MO",
 "southern illinois":"IL","illinois state":"IL","northern illinois":"IL","bradley":"IL","northwestern":"IL",
 "indiana university":"IN","ball state":"IN","notre dame":"IN","herron":"IN",
 "wisconsin":"WI","madison":"WI","milwaukee":"WI","oshkosh":"WI",
 "minneapolis":"MN","minnesota":"MN","st. cloud":"MN","hennepin":"MN",
 "kansas":"KS","emporia":"KS","pittsburg state":"KS","wichita":"KS",
 "syracuse":"NY","buffalo":"NY","brockport":"NY","stony brook":"NY",
 "towson":"MD","maryland institute":"MD","mica":"MD","baltimore":"MD",
 "virginia commonwealth":"VA","vcu":"VA","james madison":"VA","radford":"VA",
 "east carolina":"NC","ecu":"NC","western carolina":"NC","unc":"NC",
 "georgia state":"GA","valdosta":"GA","university of georgia":"GA",
 "arizona state":"AZ","northern arizona":"AZ","university of arizona":"AZ","tucson":"AZ",
 "colorado state":"CO","metropolitan state university of denver":"CO","denver":"CO","adams state":"CO",
 "university of washington":"WA","central washington":"WA","western washington":"WA",
 "university of wisconsin":"WI","kent":"OH","akron":"OH","oral roberts":"OK","oklahoma":"OK",
 "alaska":"AK","hawaii":"HI","new mexico":"NM","santa fe":"NM","utah":"UT","brigham young":"UT",
 "iowa":"IA","nebraska":"NE","tennessee":"TN","kentucky":"KY","louisiana":"LA","mississippi":"MS",
 "alabama":"AL","birmingham-southern":"AL","florida":"FL","miami":"FL","tampa":"FL",
}

def _scan(blob):
    if not blob: return None
    low = blob.lower()
    # 1) explicit overrides (longest key first, WORD-BOUNDED so "unc"!="function")
    for key in sorted(OVERRIDE, key=len, reverse=True):
        if re.search(r"\b" + re.escape(key) + r"\b", low):
            return OVERRIDE[key]
    # 2) full state name
    for name in sorted(STATES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(name) + r"\b", blob):
            return STATES[name]
    # 3) "City, ST" abbreviation
    m = re.search(r",\s*([A-Z]{2})\b", blob)
    if m and m.group(1) in CENTROID:
        return m.group(1)
    return None

def find_state(primary, *secondary):
    # the institution NAME is the most reliable signal; fall back to fc text
    return _scan(primary) or _scan(" ".join(t for t in secondary if t))

# --- city-level geocoding (much more accurate than state centroids) ---------
CITY = {  # city -> (lat, lng)
 "detroit":(42.33,-83.05),"bloomfield hills":(42.58,-83.25),"grand rapids":(42.96,-85.67),
 "ann arbor":(42.28,-83.74),"ypsilanti":(42.24,-83.62),"kalamazoo":(42.29,-85.59),"marquette":(46.55,-87.40),
 "flint":(43.01,-83.69),"east lansing":(42.74,-84.48),"mount pleasant":(43.60,-84.77),"interlochen":(44.63,-85.77),
 "birmingham mi":(42.55,-83.21),"allendale":(42.97,-85.95),
 "philadelphia":(39.95,-75.16),"pittsburgh":(40.44,-79.99),"edinboro":(41.87,-80.13),"kutztown":(40.52,-75.78),
 "indiana pa":(40.62,-79.15),"elkins park":(40.08,-75.13),"new york":(40.73,-73.99),"brooklyn":(40.68,-73.94),
 "rochester":(43.16,-77.61),"new paltz":(41.75,-74.09),"alfred":(42.25,-77.79),"buffalo":(42.89,-78.88),
 "syracuse":(43.05,-76.15),"brockport":(43.21,-77.94),"providence":(41.82,-71.41),"boston":(42.36,-71.06),
 "deer isle":(44.22,-68.68),"portland me":(43.66,-70.26),"cleveland":(41.50,-81.69),"cleveland heights":(41.52,-81.56),
 "columbus":(39.96,-82.99),"bowling green":(41.37,-83.65),"kent":(41.15,-81.36),"oxford oh":(39.51,-84.74),
 "akron":(41.08,-81.52),"chicago":(41.88,-87.63),"carbondale":(37.73,-89.22),"edwardsville":(38.81,-89.95),
 "normal":(40.51,-88.99),"dekalb":(41.93,-88.75),"madison":(43.07,-89.40),"milwaukee":(43.04,-87.91),
 "oshkosh":(44.02,-88.55),"minneapolis":(44.98,-93.27),"bloomington in":(39.17,-86.52),"muncie":(40.19,-85.39),
 "seattle":(47.61,-122.33),"ellensburg":(46.99,-120.55),"bellingham":(48.75,-122.48),"san diego":(32.72,-117.16),
 "long beach":(33.77,-118.19),"oakland":(37.80,-122.27),"san jose":(37.34,-121.89),"northridge":(34.24,-118.53),
 "fullerton":(33.87,-117.92),"sacramento":(38.58,-121.49),"san francisco":(37.77,-122.42),"los angeles":(34.05,-118.24),
 "pasadena":(34.15,-118.14),"denver":(39.74,-104.99),"boulder":(40.01,-105.27),"fort collins":(40.59,-105.08),
 "alamosa":(37.47,-105.87),"kansas city":(39.10,-94.58),"st. louis":(38.63,-90.20),"saint louis":(38.63,-90.20),
 "columbia mo":(38.95,-92.33),"maryville":(40.35,-94.87),"lawrence":(38.97,-95.24),"wichita":(37.69,-97.34),
 "pittsburg ks":(37.41,-94.70),"emporia":(38.40,-96.18),"greenville nc":(35.61,-77.37),"cullowhee":(35.31,-83.18),
 "boone":(36.22,-81.67),"penland":(35.93,-82.10),"asheville":(35.60,-82.55),"athens ga":(33.96,-83.38),
 "atlanta":(33.75,-84.39),"savannah":(32.08,-81.09),"valdosta":(30.83,-83.28),"memphis":(35.15,-90.05),
 "knoxville":(35.96,-83.92),"smithville":(35.96,-85.81),"gatlinburg":(35.71,-83.51),"denton":(33.21,-97.13),
 "commerce tx":(33.25,-95.90),"lubbock":(33.58,-101.85),"san antonio":(29.42,-98.49),"abilene":(32.45,-99.73),
 "tempe":(33.43,-111.94),"flagstaff":(35.20,-111.65),"tucson":(32.22,-110.97),"albuquerque":(35.08,-106.65),
 "santa fe":(35.69,-105.94),"boise":(43.62,-116.20),"pocatello":(42.87,-112.45),"portland or":(45.52,-122.68),
 "eugene":(44.05,-123.09),"honolulu":(21.31,-157.86),"fairbanks":(64.84,-147.72),"baltimore":(39.29,-76.61),
 "towson":(39.40,-76.60),"richmond va":(37.54,-77.44),"harrisonburg":(38.45,-78.87),"tuscaloosa":(33.21,-87.57),
 "birmingham al":(33.52,-86.81),"miami":(25.76,-80.19),"new orleans":(29.95,-90.07),"metairie":(29.98,-90.15),
 "iowa city":(41.66,-91.53),"cedar falls":(42.52,-92.45),"lincoln ne":(40.81,-96.70),"kearney":(40.70,-99.08),
 "salt lake city":(40.76,-111.89),"logan ut":(41.74,-111.83),"newark de":(39.68,-75.75),"storrs":(41.81,-72.25),
 "grand forks":(47.92,-97.03),"sarasota":(27.34,-82.53),"valencia ca":(34.44,-118.61),
}
INST_CITY = {  # institution-name fragment -> city key (for names that don't reveal the city)
 "cranbrook":"bloomfield hills","wayne state":"detroit","creative studies":"detroit","center for creative":"detroit",
 "college for creative":"detroit","interlochen":"interlochen","kendall":"grand rapids","eastern michigan":"ypsilanti",
 "western michigan":"kalamazoo","northern michigan":"marquette","grand valley":"allendale","flint":"flint",
 "michigan state":"east lansing","central michigan":"mount pleasant","birmingham bloomfield":"birmingham mi",
 "tyler":"philadelphia","temple":"philadelphia","university of the arts":"philadelphia","moore college":"philadelphia",
 "philadelphia college":"philadelphia","carnegie":"pittsburgh","edinboro":"edinboro","kutztown":"kutztown",
 "indiana university of pennsylvania":"indiana pa","risd":"providence","rhode island school":"providence",
 "saic":"chicago","school of the art institute":"chicago","art institute of chicago":"chicago","cooper union":"new york",
 "pratt":"brooklyn","parsons":"new york","fashion institute":"new york","new paltz":"new paltz","alfred":"alfred",
 "buffalo":"buffalo","brockport":"brockport","syracuse":"syracuse","rochester institute":"rochester",
 "cleveland institute":"cleveland","kansas city art institute":"kansas city","penland":"penland","haystack":"deer isle",
 "arrowmont":"gatlinburg","massachusetts college":"boston","massart":"boston","savannah college":"savannah",
 "scad":"savannah","lamar dodd":"athens ga","university of georgia":"athens ga","maryland institute":"baltimore",
 "mica":"baltimore","towson":"towson","east carolina":"greenville nc","western carolina":"cullowhee",
 "appalachian":"boone","bowling green":"bowling green","kent state":"kent","miami university":"oxford oh",
 "akron":"akron","columbus college":"columbus","southern illinois carbondale":"carbondale",
 "southern illinois edwardsville":"edwardsville","illinois state":"normal","northern illinois":"dekalb",
 "wisconsin":"madison","milwaukee":"milwaukee","oshkosh":"oshkosh","indiana university":"bloomington in",
 "ball state":"muncie","university of washington":"seattle","central washington":"ellensburg",
 "western washington":"bellingham","san diego state":"san diego","long beach":"long beach",
 "california college":"oakland","san jose":"san jose","northridge":"northridge","fullerton":"fullerton",
 "sacramento":"sacramento","otis":"los angeles","colorado state":"fort collins","metropolitan state university of denver":"denver",
 "adams state":"alamosa","washington university":"st. louis","fontbonne":"st. louis","webster":"st. louis",
 "northwest missouri":"maryville","columbia":"columbia mo","kansas":"lawrence","pittsburg state":"pittsburg ks",
 "emporia":"emporia","texas woman":"denton","north texas":"denton","texas a&m-commerce":"commerce tx",
 "east texas a&m":"commerce tx","texas tech":"lubbock","arizona state":"tempe","northern arizona":"flagstaff",
 "santa fe":"santa fe","boise":"boise","idaho state":"pocatello","oregon school":"portland or",
 "oregon college":"portland or","pacific northwest college":"portland or","marylhurst":"portland or",
 "university of alaska fairbanks":"fairbanks","james madison":"harrisonburg","virginia commonwealth":"richmond va",
 "vcu":"richmond va","metairie":"metairie","miami jewelry":"miami","abilene":"abilene","texas christian":"fort collins",
 "iowa":"iowa city","northern iowa":"cedar falls","nebraska":"lincoln ne","birmingham-southern":"birmingham al",
 "sierra nevada":"reno","tennessee tech":"smithville","appalachian center":"smithville","north dakota":"grand forks",
 "ringling":"sarasota","valencia":"valencia ca",
}

def find_latlng(name, *secondary):
    low = (name or "").lower()
    # 1) institution -> known city
    for frag in sorted(INST_CITY, key=len, reverse=True):
        if re.search(r"\b"+re.escape(frag)+r"\b", low):
            c = INST_CITY[frag]
            if c in CITY: return CITY[c], "city"
    # 2) a known city named in the institution name itself
    for c in sorted(CITY, key=len, reverse=True):
        cc = c.split()[0]  # match the city word (skip the state-disambiguator)
        if re.search(r"\b"+re.escape(cc)+r"\b", low) and len(cc) > 4:
            return CITY[c], "city"
    # 3) "City, ST" in the fc text -> if that city is known
    blob = " ".join(t for t in secondary if t)
    m = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?),\s*[A-Z]{2}\b", blob)
    if m and m.group(1).lower() in CITY: return CITY[m.group(1).lower()], "city"
    return None, None

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

# built profile pages (slug -> page file)
BUILT = {p["slug"]: p["fn"] for p in [
    {"slug":"crafts/metalsdirectorypage/s272.html","fn":"phil-renato.html"},
    {"slug":"crafts/metalsdirectorypage/p82.html","fn":"mary-lee-hu.html"},
    {"slug":"crafts/metalsdirectorypage/p97.html","fn":"stanley-lechtzin.html"},
    {"slug":"crafts/metalsdirectorypage/p88.html","fn":"daniella-kerner.html"},
    {"slug":"crafts/metalsdirectorypage/p170.html","fn":"vickie-sedman.html"},
    {"slug":"gap/rebecca-strzelec","fn":"rebecca-strzelec.html"},
    {"slug":"gap/skip-hunter","fn":"skip-hunter.html"},
]}

def yr(s):
    m = re.search(r"(18|19|20)\d\d", s or "")
    return int(m.group()) if m else None

def earliest_year(s, floor=1880):
    """smallest 4-digit year >= floor anywhere in a string (e.g. '2002-2004',
    '1970 to 1975', 'circa 2005', '2010, 2018'). None if no plausible year."""
    best = None
    for m in re.findall(r"(?:18|19|20)\d\d", s or ""):
        y = int(m)
        if y >= floor and (best is None or y < best):
            best = y
    return best

# program directory pages are named after the program (build_site.slugify);
# only link the map dot when that page actually exists in site/.
def page_slug(name):
    sl = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    if sl and os.path.exists(os.path.join(HERE, "site", sl + ".html")):
        return sl
    return None

# person pages are named after the DISPLAY name (the changed name wins,
# parentheticals stripped) — mirror build_site's choice and existence-check it,
# so every node with a built profile links to it (BUILT covers curated names).
def person_page(r):
    cands = []
    if r["fc_name_changed"] == "yes" and r["fc_current_name"]:
        cands.append(r["fc_current_name"])
    cands.append(r["name"])
    for c in cands:
        c = re.sub(r"\s*\(.*?\)\s*", " ", c or "")
        sl = re.sub(r"[^a-z0-9]+", "-", c.lower()).strip("-")
        if sl and os.path.exists(os.path.join(HERE, "site", sl + ".html")):
            return sl + ".html"
    return None

# ---- people ----
people = {r["slug"]: r for r in con.execute("SELECT * FROM people WHERE fc_checked IS NOT NULL")}
# index for instructor-name resolution
name2slug = {}
for s, r in people.items():
    name2slug.setdefault(re.sub(r"\s+", " ", (r["name"] or "").lower().strip()), s)

def resolve_person(nm):
    k = re.sub(r"\s+", " ", (nm or "").lower().strip())
    if k in name2slug: return name2slug[k]
    # loose: last name + first initial
    for full, sl in name2slug.items():
        if k and full.split()[-1] == k.split()[-1] and full[0] == k[0]:
            return sl
    return None

programs = {r["slug"]: r for r in con.execute("SELECT * FROM programs WHERE fc_checked IS NOT NULL")}
prog_name2slug = {re.sub(r"\s+"," ",(r['name'] or '').lower().strip()): s for s, r in programs.items()}

def resolve_prog(nm):
    k = re.sub(r"\s+"," ",(nm or '').lower().strip())
    if k in prog_name2slug: return prog_name2slug[k]
    for full, sl in prog_name2slug.items():
        if k and (k in full or full in k) and len(k) > 6:
            return sl
    return None

nodes, edges = [], []
placed = 0

for slug, r in programs.items():
    st = find_state(r["name"], r["fc_what_happened"], r["fc_current_chair"])
    ll, prec = find_latlng(r["name"], r["fc_what_happened"], r["fc_current_chair"])
    loc = None
    if ll:
        loc = {"state": st, "lat": ll[0], "lng": ll[1], "precision": "city"}; placed += 1
    elif st and st in CENTROID:
        loc = {"state": st, "lat": CENTROID[st][0], "lng": CENTROID[st][1], "precision": "state"}; placed += 1
    status = {"yes":"active","no":"closed","merged-renamed":"merged","unknown":"unknown"}.get(r["fc_still_exists"], "unknown")
    date = yr(r["program_started"]); yinferred = False
    if not date:
        # infer from the earliest year mentioned in any faculty 'years' string
        cand = None
        for f in con.execute("SELECT years FROM program_faculty WHERE program_id=?", (r["id"],)):
            y = earliest_year(f["years"])
            if y and (cand is None or y < cand): cand = y
        if cand: date, yinferred = cand, True
    nodes.append({"id": slug, "kind": "program", "name": re.sub(r"\s+"," ",r["name"]).strip(),
                  "date": date, "yinferred": yinferred, "status": status, "location": loc,
                  "summary": (r["fc_what_happened"] or "")[:240],
                  "page": None, "pageslug": page_slug(r["name"])})

for slug, r in people.items():
    nm = re.sub(r"\s+"," ",(r["name"] or "")).strip()
    # a genuine name change displays under the CURRENT name (Carrizzi -> Renato)
    if r["fc_name_changed"] == "yes" and r["fc_current_name"]:
        nm = re.sub(r"\s*\(.*?\)\s*", " ", r["fc_current_name"]).strip() or nm
    status = {"yes":"alive","no":"deceased","likely-deceased":"deceased","unknown":"unknown"}.get(r["fc_alive"], "unknown")
    if r["fc_still_in_job"] == "retired-emeritus": status = "retired"
    # person located at their (current/archived) institution
    st = find_state(r["currently_at"], r["fc_current_role"], r["fc_summary"])
    ll, prec = find_latlng(r["currently_at"] or "", r["fc_current_role"], r["fc_summary"])
    if ll:
        loc = {"state": st, "lat": ll[0], "lng": ll[1], "precision": "city"}
    elif st and st in CENTROID:
        loc = {"state": st, "lat": CENTROID[st][0], "lng": CENTROID[st][1], "precision": "state"}
    else:
        loc = None
    date = yr(r["dob"]); yinferred = False
    if not date:
        # infer from the earliest year named in any education 'years' string.
        # (no current-year fallback: anchoring every undated current teacher at
        # TODAY piles hundreds of nodes into one column — a wall, not a timeline.
        # truly year-less people stay undated; the lineage legend discloses them.)
        cand = None
        for e in con.execute("SELECT years FROM education WHERE person_id=?", (r["id"],)):
            y = earliest_year(e["years"])
            if y and (cand is None or y < cand): cand = y
        if cand: date, yinferred = cand, True
    nodes.append({"id": slug, "kind": "person", "name": nm, "date": date,
                  "yinferred": yinferred, "status": status,
                  "location": loc, "summary": (r["fc_summary"] or r["fc_current_role"] or "")[:240],
                  "page": BUILT.get(slug) or person_page(r)})
    # edges from education: studied-under (instructor) + studied-at (school)
    for e in con.execute("SELECT school,instructor,degree,years FROM education WHERE person_id=?", (r["id"],)):
        if e["instructor"]:
            for part in re.split(r"[/,&]| and ", e["instructor"]):
                tgt = resolve_person(part)
                if tgt and tgt != slug:
                    edges.append({"from": slug, "to": tgt, "type": "studied-under", "label": (e["degree"] or "")})
        if e["school"]:
            tgt = resolve_prog(e["school"])
            if tgt:
                edges.append({"from": slug, "to": tgt, "type": "studied-at", "label": (e["degree"] or "")})
    # taught-at (current institution)
    if r["currently_at"]:
        tgt = resolve_prog(r["currently_at"])
        if tgt: edges.append({"from": slug, "to": tgt, "type": "taught-at", "label": ""})

# program -> faculty edges
for slug, r in programs.items():
    for f in con.execute("SELECT name,person_url FROM program_faculty WHERE program_id=?", (r["id"],)):
        tgt = resolve_person(re.sub(r"\d{4}.*$","",f["name"] or ""))
        if tgt: edges.append({"from": tgt, "to": slug, "type": "faculty-of", "label": ""})

# de-dupe edges
seen = set(); uniq = []
for e in edges:
    k = (e["from"], e["to"], e["type"])
    if k not in seen: seen.add(k); uniq.append(e)

out = {
  "_generated": TODAY, "_source": "acmet.db",
  "stats": {"nodes": len(nodes), "people": sum(1 for n in nodes if n["kind"]=="person"),
            "programs": sum(1 for n in nodes if n["kind"]=="program"),
            "programs_placed": placed, "edges": len(uniq),
            "yinferred": sum(1 for n in nodes if n.get("yinferred")),
            "undated": sum(1 for n in nodes if not n.get("date"))},
  "nodes": nodes, "edges": uniq,
}
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "data", "acmet-graph.json"), "w"), indent=1)
print(json.dumps(out["stats"], indent=1))
