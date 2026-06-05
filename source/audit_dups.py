#!/usr/bin/env python3
"""audit_dups.py — find accidental duplicates among published programs and people.

Three detectors, all rename-aware:
  P1 programs: normalized-name collisions among fc_checked rows
  P2 programs: A's fc_current_name "covers" B's name (or vice versa) — the
     old-name row and the new-name row are the same school (Beaver/Arcadia,
     Glassboro/Rowan, Portland School of Art/MECA, UTPA/UTRGV…)
  P3 programs: two rows hit the same school_aliases.json key set
  H1 people: normalized full-name collisions among rows the site builds
  H2 people: clean(fc_current_name) of one row equals another row's name
     (the PHIL CARRIZZI→Phil Renato vs gap "Phillip Renato" case)
  H3 people: same first+last word pair (catches middle-initial variants)

Prints clusters for human judgment; changes nothing.
"""
import json, os, re, sqlite3, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); con.row_factory = sqlite3.Row

def norm(s):
    s = re.sub(r"[-–—/,.()&']", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()

def clean_name(n):  # strip parentheticals: "Phil Renato (Phillip Renato)" -> "Phil Renato"
    return re.sub(r"\s*\(.*?\)\s*", " ", n or "").strip()

STOP = {"the", "a", "an", "of", "at", "in"}
def sig(s):  # name signature: normalized, stop-words dropped, word-order kept
    return " ".join(w for w in norm(s).split() if w not in STOP)

# ---------------- programs ----------------
progs = [dict(r) for r in con.execute("SELECT * FROM programs WHERE fc_checked IS NOT NULL")]
print(f"published programs: {len(progs)}")

clusters = defaultdict(set)

# P1: same normalized name
by_sig = defaultdict(list)
for p in progs: by_sig[sig(p["name"])].append(p)
for k, v in by_sig.items():
    if len(v) > 1: clusters[("P1", k)] = {q["id"] for q in v}

# P2: one row's current name covers another row's archived name (and reverse).
# match on signature containment with a length guard so "university" noise
# doesn't cluster everything: the shorter sig must be >= 3 words or >= 18 chars.
def covered(a, b):  # does text a contain school-name b?
    sa, sb = " " + sig(a) + " ", sig(b)
    return sb and (len(sb.split()) >= 3 or len(sb) >= 18) and (" " + sb + " ") in sa
for p in progs:
    cur = clean_name(p["fc_current_name"] or "")
    if not cur: continue
    for q in progs:
        if q["id"] == p["id"]: continue
        if covered(cur, q["name"]) or (sig(cur) and covered(q["fc_current_name"] or "", p["name"])):
            clusters[("P2", min(p["id"], q["id"]))] |= {p["id"], q["id"]}

# P3: same alias-key footprint (only keys that are school-specific enough)
al = {k: v for k, v in json.load(open(os.path.join(HERE, "data", "school_aliases.json"))).items()
      if not k.startswith("_")}
hits = defaultdict(set)
for p in progs:
    hay = " " + norm(p["name"]) + " | " + norm(clean_name(p["fc_current_name"] or "")) + " "
    for k in al:
        if " " + k + " " in hay: hits[k].add(p["id"])
for k, ids in hits.items():
    if len(ids) > 1: clusters[("P3", k)] = ids

pid = {p["id"]: p for p in progs}
seen = set()
print("\n================ PROGRAM CLUSTERS ================")
merged = []
for key, ids in clusters.items():
    fro = frozenset(ids)
    if fro in seen: continue
    seen.add(fro); merged.append((key, sorted(ids)))
for key, ids in sorted(merged, key=lambda x: x[1]):
    print(f"\n[{key[0]}:{key[1]}]")
    for i in ids:
        p = pid[i]
        print(f"  id={i:4} slug={p['slug'][:46]:46} name={p['name'][:52]!r}")
        if p["fc_current_name"] and norm(p["fc_current_name"]) != norm(p["name"]):
            print(f"        now: {p['fc_current_name'][:100]!r}")

# ---------------- people ----------------
people = [dict(r) for r in con.execute("SELECT * FROM people WHERE fc_checked IS NOT NULL")]
print(f"\npeople rows: {len(people)}")

pc = defaultdict(set)
by_sig = defaultdict(list)
for r in people: by_sig[sig(clean_name(r["name"]))].append(r)
for k, v in by_sig.items():
    if len(v) > 1: pc[("H1", k)] = {q["id"] for q in v}

cur_of = {}
for r in people:
    if r["fc_current_name"]:
        cur_of[r["id"]] = sig(clean_name(r["fc_current_name"]))
by_name_sig = defaultdict(list)
for r in people: by_name_sig[sig(clean_name(r["name"]))].append(r["id"])
for i, cs in cur_of.items():
    for j in by_name_sig.get(cs, []):
        if j != i: pc[("H2", cs)] |= {i, j}
# H2b: two different rows whose CURRENT names collide
cur_groups = defaultdict(set)
for i, cs in cur_of.items():
    if cs: cur_groups[cs].add(i)
for cs, ids in cur_groups.items():
    if len(ids) > 1: pc[("H2", cs)] |= ids

# nickname-tolerant first names: Phil/Phillip, Tom/Thomas, Bob/Robert…
NICK = {"phil": "phillip", "philip": "phillip", "tom": "thomas", "tim": "timothy",
        "bob": "robert", "rob": "robert", "bill": "william", "will": "william",
        "dick": "richard", "rick": "richard", "rich": "richard", "jim": "james",
        "mike": "michael", "dave": "david", "dan": "daniel", "ed": "edward",
        "ted": "edward", "tony": "anthony", "steve": "steven", "stephen": "steven",
        "ken": "kenneth", "ron": "ronald", "don": "donald", "fred": "frederick",
        "greg": "gregory", "jeff": "jeffrey", "geoff": "jeffrey", "chris": "christopher",
        "kate": "katherine", "kathy": "katherine", "catherine": "katherine",
        "liz": "elizabeth", "beth": "elizabeth", "betty": "elizabeth",
        "peggy": "margaret", "meg": "margaret", "sue": "susan", "suzanne": "susan",
        "pam": "pamela", "pat": "patricia", "trish": "patricia", "deb": "deborah",
        "debbie": "deborah", "sandy": "sandra", "cindy": "cynthia", "vicki": "victoria",
        "nick": "nicholas", "alex": "alexander", "sam": "samuel", "andy": "andrew",
        "drew": "andrew", "matt": "matthew", "joe": "joseph", "lynda": "linda"}
def canon_first(w):
    w = NICK.get(w, w)
    return w[:4] if len(w) > 4 else w   # prefix-4 catches phillip/philip etc.
pairs = defaultdict(set)
for r in people:
    w = sig(clean_name(r["name"])).split()
    if len(w) >= 2: pairs[(canon_first(w[0]), w[-1])].add(r["id"])
    # also pair the current name's first/last so renames cross-match
    if r["fc_current_name"]:
        cw = sig(clean_name(r["fc_current_name"])).split()
        if len(cw) >= 2: pairs[(canon_first(cw[0]), cw[-1])].add(r["id"])
for k, ids in pairs.items():
    if len(ids) > 1: pc[("H3", " ".join(k))] = ids

rid = {r["id"]: r for r in people}
seen = set(); merged = []
for key, ids in pc.items():
    fro = frozenset(ids)
    if fro in seen: continue
    seen.add(fro); merged.append((key, sorted(ids)))
print(f"\n================ PEOPLE CLUSTERS ({len(merged)}) ================")
for key, ids in sorted(merged, key=lambda x: x[1]):
    print(f"\n[{key[0]}:{key[1]}]")
    for i in ids:
        r = rid[i]
        extra = f" now={r['fc_current_name']!r}" if r["fc_current_name"] and norm(clean_name(r["fc_current_name"])) != norm(clean_name(r["name"])) else ""
        print(f"  id={i:4} kind={r['kind'][:19]:19} fc={str(r['fc_checked'])[:10]:10} name={r['name'][:44]!r}{extra}")
