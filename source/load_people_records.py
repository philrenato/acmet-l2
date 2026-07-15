#!/usr/bin/env python3
"""load_people_records.py <result.json> — apply the people-records-verify run.

Updates existing directory people / inserts new ones with verified current role,
institution, status, education, and a permalink source. Special handling:
  * Jill Baker Gower -> College of DuPage (manual correction); merge the stray
    Glassboro/Rowan duplicate row into one canonical record.
"""
import os, re, sys, json, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); con.row_factory = sqlite3.Row; cur = con.cursor()
TODAY = "2026-05-30"

raw = json.load(open(sys.argv[1]))
recs = raw.get("result", raw)
if isinstance(recs, str): recs = json.loads(recs)
recs = recs.get("records", recs)
print("records:", len(recs))

def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", (s or "").lower())).strip()
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

# build a name->id index over checked people (and a loose last-name index)
people = [dict(r) for r in con.execute("SELECT id,name,slug FROM people WHERE fc_checked IS NOT NULL")]
exact = {}; bylast = {}
for p in people:
    exact.setdefault(norm(p["name"]), p)
    parts = norm(p["name"]).split()
    if parts: bylast.setdefault(parts[-1], []).append(p)

def find_person(name):
    n = norm(name)
    if n in exact: return exact[n]
    # match on last name + first initial when unique
    parts = n.split()
    if len(parts) >= 2:
        cands = [p for p in bylast.get(parts[-1], []) if norm(p["name"]).split()[0][:1] == parts[0][:1]]
        # also allow contained (Ana Lopez vs Ana M. Lopez)
        cands += [p for p in bylast.get(parts[-1], []) if parts[0] in norm(p["name"])]
        cands = list({p["id"]: p for p in cands}.values())
        if len(cands) == 1: return cands[0]
    return None

LEVEL = {"bfa":"Undergraduate","ba":"Undergraduate","bs":"Undergraduate","bdes":"Undergraduate",
         "mfa":"Graduate","ma":"Graduate","ms":"Graduate","phd":"Graduate","undergraduate":"Undergraduate","graduate":"Graduate"}
def lvl(x):
    return LEVEL.get((x or "").strip().lower(), (x or "").strip().title() or "Other")

def set_education(pid, edu):
    cur.execute("DELETE FROM education WHERE person_id=?", (pid,))
    for e in edu or []:
        sch = e.get("school", "")
        if not sch: continue
        cur.execute("INSERT INTO education(person_id,level,school,years,major,degree,instructor) VALUES(?,?,?,?,?,?,?)",
                    (pid, lvl(e.get("level")), sch, e.get("year",""), "", e.get("degree",""), ""))

def alive_of(status):
    return {"deceased":"no","active":"yes","retired":"yes","relocated":"yes"}.get(status, "unknown")

updated = inserted = 0
for v in recs:
    name = v["name"].strip()
    role = v.get("currentRole","")
    inst = v.get("currentInstitution","")
    status = v.get("status","unknown")
    url = v.get("bestUrl","")
    src = " | ".join(u for u in (v.get("sources") or []) if u.startswith("http")) or url
    loc = v.get("location","")
    edu = v.get("education", [])
    summary = f"{role}." + (f" Based in {loc}." if loc else "")
    conf = v.get("confidence","medium")
    still = "retired-emeritus" if status == "retired" else "yes"

    # ---- Jill Baker Gower: manual correction overrides the agent ----
    if "gower" in norm(name):
        inst = "College of DuPage"
        role = "Professor of Metalsmithing & Jewelry, College of DuPage"
        summary = "Metalsmith/jeweler; Professor of Metalsmithing & Jewelry at College of DuPage (Glen Ellyn, IL); previously taught at Rowan University (formerly Glassboro State)."
        status = "active"; still = "yes"; conf = "high"
        url = "https://www.cod.edu/academics/programs/arts/index.aspx"
        # merge: delete the stray Glassboro/Rowan duplicate, keep the DuPage row
        dupes = [p for p in people if "gower" in norm(p["name"])]
        keep = next((p for p in dupes if "dupage" in (p["slug"] or "").lower() or "Jill Gower" in p["name"]), dupes[0] if dupes else None)
        for p in dupes:
            if keep and p["id"] != keep["id"]:
                cur.execute("DELETE FROM education WHERE person_id=?", (p["id"],))
                cur.execute("DELETE FROM people WHERE id=?", (p["id"],))
        if keep:
            cur.execute("""UPDATE people SET name='Jill Baker Gower', currently_at=?, current_role=?, fc_alive='yes',
                fc_still_in_job='yes', fc_current_role=?, fc_current_link=?, fc_summary=?, fc_confidence='high',
                fc_verified='confirmed', fc_sources=?, fc_checked=? WHERE id=?""",
                (inst, role, role, url, summary, src or url, TODAY, keep["id"]))
            updated += 1
        continue

    p = find_person(name)
    if p:
        cur.execute("""UPDATE people SET currently_at=?, current_role=?, fc_alive=?, fc_still_in_job=?,
            fc_current_role=?, fc_current_link=?, fc_summary=?, fc_confidence=?, fc_verified='confirmed',
            fc_sources=?, fc_checked=? WHERE id=?""",
            (inst, role, alive_of(status), still, role, url, summary, conf, src, TODAY, p["id"]))
        set_education(p["id"], edu)
        updated += 1
        print(f"  upd  {name} -> {inst} [{status}]")
    else:
        slug = "gap/" + slugify(name)
        if cur.execute("SELECT 1 FROM people WHERE slug=?", (slug,)).fetchone():
            slug += "-2"
        cur.execute("""INSERT INTO people(slug,name,kind,currently_at,current_role,fc_alive,fc_name_changed,
            fc_current_role,fc_still_in_job,fc_current_link,fc_summary,fc_confidence,fc_verified,fc_sources,fc_checked)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (slug, name, "person-gap-addition", inst, role, alive_of(status), "no", role, still, url,
             summary, conf, "phil-added", src, TODAY))
        set_education(cur.lastrowid, edu)
        inserted += 1
        print(f"  NEW  {name} -> {inst}")

con.commit()
print(f"\nupdated {updated}, inserted {inserted}")
con.close()
