#!/usr/bin/env python3
"""
load_factcheck.py — ingest fact-check workflow results into acmet.db.

Input: a JSON file {"people":[...], "programs":[...]} (the workflow's return).
If that file is missing, falls back to scraping the per-agent StructuredOutput
results out of the workflow transcript dir (agent-*.jsonl), so a truncated
inline return never loses data.

Writes:
  * adds fc_* columns to people/programs with the current findings
  * fills the factcheck table (one row per entity, with sources + verify verdict)
  * regenerates exports/ CSVs and writes CHANGES.md (notable updates only)
"""
import csv, glob, json, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "acmet.db")
EXPORTS = os.path.join(HERE, "exports")
RESULTS = os.environ.get("FC_RESULTS", os.path.join(HERE, "factcheck_results.json"))
TRANSCRIPT = os.environ.get("FC_TRANSCRIPT", "")  # workflow transcript dir (fallback)


def from_transcripts(tdir):
    """Recover structured findings from agent-*.jsonl StructuredOutput calls."""
    people, programs = [], []
    for fn in glob.glob(os.path.join(tdir, "**", "agent-*.jsonl"), recursive=True):
        try:
            obj = None
            for line in open(fn, encoding="utf-8", errors="replace"):
                line = line.strip()
                if not line:
                    continue
                # find a StructuredOutput tool input or a final json object
                for m in re.finditer(r'\{.*\}', line):
                    try:
                        cand = json.loads(m.group())
                    except Exception:
                        continue
                    blob = json.dumps(cand)
                    if '"still_in_archived_job"' in blob:
                        obj = cand
                    elif '"still_exists"' in blob:
                        obj = cand
            if obj is not None:
                ('still_exists' in obj and programs or people).append(obj)
        except Exception:
            continue
    # dedupe by slug
    def dd(lst):
        seen = {}
        for o in lst:
            seen[o.get("slug") or o.get("name")] = o
        return list(seen.values())
    return dd(people), dd(programs)


def addcol(con, table, col, decl="TEXT"):
    cols = [c[1] for c in con.execute(f"PRAGMA table_info({table})")]
    if col not in cols:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def src_join(sources):
    out = []
    for s in (sources or []):
        if isinstance(s, dict):
            out.append(s.get("url", ""))
        elif isinstance(s, str):
            out.append(s)
    return " | ".join([u for u in out if u])


def main():
    if os.path.exists(RESULTS):
        data = json.load(open(RESULTS))
        people, programs = data.get("people", []), data.get("programs", [])
        print(f"loaded results json: {len(people)} people, {len(programs)} programs")
    elif TRANSCRIPT and os.path.isdir(TRANSCRIPT):
        people, programs = from_transcripts(TRANSCRIPT)
        print(f"recovered from transcripts: {len(people)} people, {len(programs)} programs")
    else:
        sys.exit(f"no results: set FC_RESULTS to the json, or FC_TRANSCRIPT to the workflow dir")

    con = sqlite3.connect(DB)
    for c in ("fc_alive", "fc_name_changed", "fc_current_name", "fc_current_role",
              "fc_still_in_job", "fc_current_link", "fc_summary", "fc_confidence",
              "fc_verified", "fc_sources", "fc_checked"):
        addcol(con, "people", c)
    for c in ("fc_still_exists", "fc_current_name", "fc_current_chair", "fc_current_status",
              "fc_what_happened", "fc_current_link", "fc_confidence", "fc_verified",
              "fc_sources", "fc_checked"):
        addcol(con, "programs", c)
    con.execute("DELETE FROM factcheck")

    DATE = "2026-05-29"
    changes = []

    for p in people:
        slug = p.get("slug", "")
        nm = p.get("name", "")
        con.execute("""UPDATE people SET fc_alive=?, fc_name_changed=?, fc_current_name=?,
                       fc_current_role=?, fc_still_in_job=?, fc_current_link=?, fc_summary=?,
                       fc_confidence=?, fc_verified=?, fc_sources=?, fc_checked=? WHERE slug=?""",
                    (p.get("alive"), "yes" if p.get("name_changed") else "no", p.get("current_name", ""),
                     p.get("current_role", ""), p.get("still_in_archived_job"), p.get("current_link", ""),
                     p.get("summary", ""), p.get("confidence"), p.get("verified", ""),
                     src_join(p.get("sources")), DATE, slug))
        con.execute("""INSERT INTO factcheck (entity_type,slug,name,question,finding,status,confidence,
                       source_url,source_title,date_checked,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    ("person", slug, nm, "alive/job/name-change", p.get("summary", "") or p.get("current_role", ""),
                     p.get("still_in_archived_job", ""), p.get("confidence", ""),
                     src_join(p.get("sources")), "", DATE,
                     f"verified={p.get('verified','')}; {p.get('notes','')}"))
        if p.get("name_changed"):
            changes.append(f"NAME CHANGE  {nm} -> {p.get('current_name','?')}  [{p.get('confidence')}]")
        if p.get("alive") in ("no", "likely-deceased"):
            changes.append(f"DECEASED?    {nm}  ({p.get('death_info','')})  [{p.get('confidence')}]")

    for pg in programs:
        slug = pg.get("slug", "")
        nm = pg.get("name", "")
        con.execute("""UPDATE programs SET fc_still_exists=?, fc_current_name=?, fc_current_chair=?,
                       fc_current_status=?, fc_what_happened=?, fc_current_link=?, fc_confidence=?,
                       fc_verified=?, fc_sources=?, fc_checked=? WHERE slug=?""",
                    (pg.get("still_exists"), pg.get("current_name", ""), pg.get("current_chair", ""),
                     pg.get("current_status", ""), pg.get("what_happened", ""), pg.get("current_link", ""),
                     pg.get("confidence"), pg.get("verified", ""), src_join(pg.get("sources")), DATE, slug))
        con.execute("""INSERT INTO factcheck (entity_type,slug,name,question,finding,status,confidence,
                       source_url,source_title,date_checked,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    ("program", slug, nm, "program still exists / chair", pg.get("what_happened", ""),
                     pg.get("still_exists", ""), pg.get("confidence", ""), src_join(pg.get("sources")), "",
                     DATE, f"verified={pg.get('verified','')}; chair={pg.get('current_chair','')}"))
        if pg.get("still_exists") in ("no", "merged-renamed"):
            changes.append(f"PROGRAM {pg.get('still_exists','').upper()}  {nm}  ({pg.get('what_happened','')[:120]})  [{pg.get('confidence')}]")
    con.commit()

    # exports
    os.makedirs(EXPORTS, exist_ok=True)
    for table in ("people", "programs", "factcheck"):
        rows = con.execute(f"SELECT * FROM {table}").fetchall()
        names = [c[0] for c in con.execute(f"SELECT * FROM {table} LIMIT 0").description]
        with open(os.path.join(EXPORTS, f"{table}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(names); w.writerows(rows)

    with open(os.path.join(HERE, "CHANGES.md"), "w") as f:
        f.write("# Notable updates found by the fact-check pass (2026-05-29)\n\n")
        f.write(f"{len(changes)} flagged changes (name changes, deaths, program closures/merges):\n\n")
        for c in sorted(set(changes)):
            f.write(f"- {c}\n")

    print(f"loaded. flagged changes: {len(set(changes))}  ->  CHANGES.md")
    print(f"people checked: {sum(1 for _ in people)}  programs checked: {sum(1 for _ in programs)}")


if __name__ == "__main__":
    main()
