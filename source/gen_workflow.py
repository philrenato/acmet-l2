#!/usr/bin/env python3
"""Generate factcheck_workflow.js with the deduplicated roster baked in as
literals (workflow scripts have no filesystem access, and ~400 entities is too
large to pass inline as args). Dedupe people + programs by normalized name,
preferring the newer metalsdirectorypage entry over the older history tree."""
import json, re, sqlite3, os

HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); con.row_factory = sqlite3.Row

def norm(n): return re.sub(r"\s+", " ", (n or "").strip().upper())
def newer(slug): return 0 if "metalsdirectorypage" in (slug or "") else 1  # prefer 0

# --- people ---
people = {}
for r in con.execute("SELECT * FROM people"):
    name = r["name"]
    if not name or len(name) < 3 or not re.search(r"[A-Za-z]", name):
        continue
    k = norm(name)
    edu = [{"level": e["level"], "school": e["school"], "degree": e["degree"]}
           for e in con.execute("SELECT * FROM education WHERE person_id=?", (r["id"],))
           if e["school"]]
    rec = {"slug": r["slug"], "name": re.sub(r"\s+", " ", name.strip()).title(),
           "dob": r["dob"], "currently_at": r["currently_at"], "since_year": r["since_year"],
           "education": edu}
    if k not in people or newer(rec["slug"]) < newer(people[k]["slug"]):
        # keep preferred; merge education if other had more
        if k in people and len(people[k]["education"]) > len(rec["education"]):
            rec["education"] = people[k]["education"]
        people[k] = rec
people = list(people.values())

# --- programs ---
progs = {}
for r in con.execute("SELECT * FROM programs"):
    name = r["name"]
    if not name or len(name) < 3:
        continue
    k = norm(name)
    fac = [f["name"] for f in con.execute("SELECT name FROM program_faculty WHERE program_id=?", (r["id"],)) if f["name"]]
    rec = {"slug": r["slug"], "name": re.sub(r"\s+", " ", name.strip()),
           "started": r["program_started"], "faculty": fac}
    if k not in progs or newer(rec["slug"]) < newer(progs[k]["slug"]):
        progs[k] = rec
progs = list(progs.values())

print(f"unique people: {len(people)} | unique programs: {len(progs)}")
born = [int(re.search(r'(18|19|20)\d\d', p['dob']).group()) for p in people if p['dob'] and re.search(r'(18|19|20)\d\d', p['dob'])]
print(f"with DOB: {len(born)} | born<1930: {sum(1 for y in born if y<1930)} | born>=1940: {sum(1 for y in born if y>=1940)}")

template = open(os.path.join(HERE, "factcheck_workflow.template.js")).read()
out = (template
       .replace("/*__PEOPLE__*/[]", json.dumps(people, ensure_ascii=False))
       .replace("/*__PROGRAMS__*/[]", json.dumps(progs, ensure_ascii=False)))
with open(os.path.join(HERE, "factcheck_workflow.js"), "w") as f:
    f.write(out)
print("wrote factcheck_workflow.js")
