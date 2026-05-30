#!/usr/bin/env python3
"""load_gaps.py <result.json> — ingest the snag-gap-verify workflow output.

Adds the verified, currently-operating, metals/jewelry institutions as programs
(typed + sourced) and their current faculty as people (cross-linked as faculty of
the program). Idempotent by slug; skips faculty whose name already exists in the
directory. Run build_site.py + build_graph.py afterward to publish.
"""
import os, re, sys, json, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); cur = con.cursor()
TODAY = "2026-05-30"

res = json.load(open(sys.argv[1]))
# unwrap if wrapped under result/return
if "addWorthy" not in res:
    for k in ("result", "return", "value", "output"):
        if isinstance(res.get(k), dict) and "addWorthy" in res[k]:
            res = res[k]; break
addw = res.get("addWorthy", [])
print(f"add-worthy institutions: {len(addw)}")

def slugify(s): return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
def norm(s): return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", (s or "").lower())).strip()

existing_prog = {norm(r[0]): r[1] for r in cur.execute("SELECT name, slug FROM programs")}
existing_people = {norm(r[0]) for r in cur.execute("SELECT name FROM people WHERE fc_checked IS NOT NULL")}

prog_added = prog_updated = fac_added = fac_skipped = 0
for v in addw:
    name = v["name"].strip()
    stype = v.get("schoolType", "other")
    url = v.get("bestUrl") or (v.get("_input", {}) or {}).get("url", "")
    note = v.get("note", "")
    conf = v.get("confidence", "medium")
    src = " | ".join([u for u in [url] if u])
    nslug = norm(name)
    if nslug in existing_prog:
        slug = existing_prog[nslug]; prog_updated += 1
    else:
        slug = "snag-gap/" + slugify(name)
        cur.execute("""INSERT OR IGNORE INTO programs(slug,name,degrees,source_url,
            fc_still_exists,fc_current_name,fc_current_status,fc_what_happened,fc_current_link,
            fc_confidence,fc_verified,fc_sources,fc_checked,school_type,fc_succession_status)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (slug, name, "", url, "yes", name, "active", note, url, conf,
             "snag-gap-2026", src, TODAY, stype, "active-with-dedicated-faculty"))
        prog_added += 1
    pid_prog = cur.execute("SELECT id FROM programs WHERE slug=?", (slug,)).fetchone()
    pid_prog = pid_prog[0] if pid_prog else None
    # faculty -> people + program_faculty
    for f in (v.get("faculty") or [])[:6]:
        fname = (f.get("name") or "").strip()
        if not fname or len(fname) < 4: continue
        if norm(fname) in existing_people:
            fac_skipped += 1
            # still link them as faculty of this program if not already
            if pid_prog:
                cur.execute("INSERT INTO program_faculty(program_id,name,person_url) VALUES(?,?,?)",
                            (pid_prog, fname, f.get("url","")))
            continue
        title = f.get("title", ""); furl = f.get("url", "")
        pslug = "snag-gap/" + slugify(fname)
        if cur.execute("SELECT 1 FROM people WHERE slug=?", (pslug,)).fetchone(): continue
        summary = f"{title}, {name}." if title else f"Metals/jewelry faculty, {name}."
        cur.execute("""INSERT INTO people(slug,name,kind,currently_at,current_role,
            fc_alive,fc_name_changed,fc_current_role,fc_still_in_job,fc_current_link,
            fc_summary,fc_confidence,fc_verified,fc_sources,fc_checked)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (pslug, fname, "person-gap-addition", name, title, "yes", "no", title, "yes",
             furl or url, summary, "medium", "snag-gap-2026", (furl or url), TODAY))
        existing_people.add(norm(fname))
        fac_added += 1
        npid = cur.lastrowid
        if pid_prog:
            cur.execute("INSERT INTO program_faculty(program_id,name,person_url) VALUES(?,?,?)",
                        (pid_prog, fname, furl))

con.commit()
print(f"programs: +{prog_added} new, {prog_updated} matched-existing")
print(f"faculty:  +{fac_added} new people, {fac_skipped} already in directory (linked)")
con.close()
