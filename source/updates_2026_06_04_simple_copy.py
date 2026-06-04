#!/usr/bin/env python3
"""
updates_2026_06_04_simple_copy.py — the "write simple" pass (Phil, 2026-06-04,
prompted by the Rio Grande page): public copy never narrates the research
process or editorial rules. 163 texts (130 program fields + 33 people
summaries) carried scan-agent reasoning ("Belongs in directory", "per the
no-invent rule", "confirmed via…", "no obituary could be located", "the
archived record carried no…"). Each was rewritten by deletion/condensation
only — no facts added; pure we-found-nothing rows became "Unknown." Inputs:
/tmp/acmet_copy_sweep.json (originals) + /tmp/acmet_copy_rewrites.json.
Rule recorded in HANDOFF.md + memory (feedback_no_process_exposition_in_copy).
"""
import json, sqlite3

con = sqlite3.connect("acmet.db")
cur = con.cursor()
rew = json.load(open("/tmp/acmet_copy_rewrites.json"))

np = ns = 0
for r in rew["programs"]:
    if r["new"]:
        assert r["field"] in ("fc_what_happened", "fc_current_status")
        cur.execute(f"UPDATE programs SET {r['field']}=? WHERE id=?", (r["new"], r["id"]))
        np += 1
for r in rew["people"]:
    if r["new"]:
        assert r["field"] == "fc_summary"
        cur.execute("UPDATE people SET fc_summary=? WHERE id=?", (r["new"], r["id"]))
        ns += 1

cur.execute("""INSERT INTO factcheck (entity_type, slug, name, question, finding,
    status, confidence, source_url, source_title, date_checked, notes)
    VALUES ('editorial','','(batch)','copy style',
    'Simple-copy pass: 163 public texts rewritten to remove research-process narration (deletion/condensation only; unknowns now read \"Unknown.\"). No factual content added.',
    'applied','high','','simple-copy pass','2026-06-04','Phil: say unknown and leave it at that')""")
con.commit()
print(f"applied: {np} program fields, {ns} people summaries")
con.close()
