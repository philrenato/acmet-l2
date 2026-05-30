#!/usr/bin/env python3
"""Load faculty-succession re-scan results into acmet.db.

Input JSON {"programs":[{slug,institution,program_status,current_faculty,new_people,...}]}
(default succession_results.json; or set FC_RESULTS).

  * adds discovered successors (new_people) to people as gap-additions
  * updates each program's current-faculty note + a succession status column
  * writes SUCCESSION.md (the payoff: new people to add + programs that lost metals)
"""
import json, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "acmet.db")
RESULTS = os.environ.get("FC_RESULTS", os.path.join(HERE, "succession_results.json"))
DATE = "2026-05-30"


def addcol(con, table, col):
    cols = [c[1] for c in con.execute(f"PRAGMA table_info({table})")]
    if col not in cols:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")


def srcs(arr):
    return " | ".join(s.get("url", "") for s in (arr or []) if isinstance(s, dict) and s.get("url"))


def slugify(name):
    return "gap/" + re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def main():
    data = json.load(open(RESULTS))
    progs = data.get("programs", data) if isinstance(data, dict) else data
    con = sqlite3.connect(DB)
    addcol(con, "programs", "fc_succession_status")
    addcol(con, "programs", "fc_current_faculty")

    new_people, lapsed, active = [], [], []
    added = 0
    for p in progs:
        if not isinstance(p, dict):
            continue
        slug = p.get("slug", "")
        inst = p.get("institution", "")
        status = p.get("program_status", "")
        cur = p.get("current_faculty", []) or []
        curtxt = "; ".join(f"{c.get('name','')} ({c.get('title','')})".strip() for c in cur if c.get("name"))
        con.execute("UPDATE programs SET fc_succession_status=?, fc_current_faculty=? WHERE slug=?",
                    (status, curtxt, slug))
        if status in ("lapsed-or-closed", "active-no-dedicated-metals-faculty"):
            lapsed.append((inst, status, p.get("note", "")))
        elif status == "active-with-dedicated-faculty":
            active.append(inst)

        for np in (p.get("new_people") or []):
            nm = (np.get("name") or "").strip()
            if not nm:
                continue
            sl = slugify(nm)
            exists = con.execute("SELECT 1 FROM people WHERE slug=? OR name=?", (sl, nm)).fetchone()
            if exists:
                continue
            con.execute("""INSERT INTO people (slug,name,kind,currently_at,source_url,
                fc_alive,fc_still_in_job,fc_current_role,fc_current_link,fc_confidence,fc_verified,fc_sources,fc_checked)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (sl, nm, "person-gap-addition", inst, f"succession re-scan: {inst}",
                 "yes", "yes", np.get("title", ""), np.get("link", ""), p.get("confidence", "medium"),
                 "succession-scan", srcs(p.get("sources")), DATE))
            con.execute("""INSERT INTO factcheck (entity_type,slug,name,question,finding,status,confidence,source_url,source_title,date_checked,notes)
                VALUES ('person',?,?,?,?,?,?,?,?,?,?)""",
                (sl, nm, "current metals faculty (successor, not in archive)",
                 f"{np.get('title','')} at {inst}", "new-add", p.get("confidence", "medium"),
                 np.get("link", ""), inst, DATE, "Discovered by faculty-succession re-scan."))
            new_people.append((nm, np.get("title", ""), inst))
            added += 1
    con.commit()

    with open(os.path.join(HERE, "SUCCESSION.md"), "w") as f:
        f.write("# Faculty-succession re-scan (2026-05-30)\n\n")
        f.write(f"Re-scanned {len(progs)} surviving programs for their CURRENT metals/jewelry faculty.\n\n")
        f.write(f"## NEW people to add ({len(new_people)}) — successors not in the archived directory\n\n")
        for nm, ti, inst in sorted(new_people, key=lambda x: x[2]):
            f.write(f"- **{nm}** — {ti} · {inst}\n")
        f.write(f"\n## Programs that LOST dedicated metals faculty / lapsed ({len(lapsed)})\n\n")
        for inst, st, note in sorted(lapsed):
            f.write(f"- **{inst}** — {st}\n  - {note[:160]}\n")
        f.write(f"\n## Still active with dedicated metals faculty ({len(active)})\n\n")
        f.write(", ".join(sorted(active)) + "\n")

    print(f"added {added} successor people; lapsed/no-faculty: {len(lapsed)}; active: {len(active)}")
    print("-> SUCCESSION.md")


if __name__ == "__main__":
    main()
