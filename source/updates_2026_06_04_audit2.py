#!/usr/bin/env python3
"""
updates_2026_06_04_audit2.py — apply the 2026-06-04 second-audit findings:

(1) THE FABRICATED-EDUCATION PURGE. A targeted audit of every workflow-added
    education row carrying a named instructor (45 people, 90 rows) found a
    SYSTEMATIC fabrication across the succession-scan cohort: the scan agent
    attached invented mid-century American educations under marquee teacher
    names (Fisch, Ebendorf, Carlyle Smith, Pine, Lechtzin, Mary Lee Hu...) to
    contemporary faculty — the tell is impossible dates (1950s-70s degrees for
    people born in the 1980s). 67/90 rows FABRICATED, 15 SUSPECT, 4 plausible
    inferences, 4 confirmed. Caballero-Perez was the tip of the iceberg.
    Actions: fabricated rows are DELETED and replaced with the REAL education
    from each person's own bio / official directory (fetched + cited);
    suspect rows (no source at all, internally impossible) are DELETED —
    a claim with no source doesn't get published; plausible/confirmed kept.

(2) DISPUTED / LOW-CONFIDENCE RE-VERIFICATION (24 people, two agent batches,
    adversarially checked). 3 RESOLVED + 6 IMPROVED with real sources →
    promoted to medium confidence, fc_verified='reverified-2026-06-04'
    (build_site now surfaces sourced medium re-verifications); 15 honestly
    UNFINDABLE stay held back. Wrong-person sources caught and dropped:
    Nacke (German porcelain artist), van Duinwyk (legal directories),
    Duncan (a Free Methodist pastor's obituary), Sholtis (a horn professor).
    House rule held: no death asserted anywhere; 'likely' alive clamped to
    'unknown' (the bio states the dated activity instead).

Inputs: /tmp/acmet_edu_audit.json, /tmp/acmet_disputed_A.json, /tmp/acmet_disputed_B.json
"""
import json, sqlite3

DB = "acmet.db"
TODAY = "2026-06-04"

con = sqlite3.connect(DB)
cur = con.cursor()


def fclog(slug, name, question, finding, status, conf, url, title, notes=""):
    cur.execute(
        """INSERT INTO factcheck (entity_type, slug, name, question, finding,
           status, confidence, source_url, source_title, date_checked, notes)
           VALUES ('person',?,?,?,?,?,?,?,?,?,?)""",
        (slug, name, question, finding, status, conf, url, title, TODAY, notes))


# ---------------------------------------------------------------- (1) education purge
edu = json.load(open("/tmp/acmet_edu_audit.json"))["rows"]
slug_of = {r[0]: r[1] for r in cur.execute("SELECT id, slug FROM people")}

by_person = {}
for r in edu:
    by_person.setdefault(r["person_id"], []).append(r)

deleted = inserted = cleared = 0
for pid, rows in sorted(by_person.items()):
    name = rows[0]["name"]
    fab = [r for r in rows if r["suggested_action"] == "replace-education"]
    sus = [r for r in rows if r["suggested_action"] == "clear-instructor"]
    inf = [r for r in rows if r["suggested_action"] == "keep-note-inferred"]

    # fabricated: delete the audited rows, insert the real education (deduped)
    if fab:
        for r in fab:
            cur.execute("DELETE FROM education WHERE rowid=?", (r["edu_rowid"],))
            deleted += 1
        seen, reps = set(), []
        for r in fab:
            rep = r.get("replacement")
            if not rep:
                continue
            for one in (rep.get("rows") if isinstance(rep, dict) and rep.get("rows") else [rep]):
                key = (one.get("school", ""), one.get("degree", ""))
                if key in seen or not one.get("school"):
                    continue
                seen.add(key)
                reps.append(one)
        for one in reps:
            cur.execute(
                "INSERT INTO education (person_id, level, school, years, major, degree, instructor) VALUES (?,?,?,?,?,?,?)",
                (pid, one.get("level", ""), one.get("school", ""), one.get("years", ""),
                 "", one.get("degree", ""), one.get("instructor", "")))
            inserted += 1
        ev = fab[0]
        fclog(slug_of.get(pid, ""), name, "education (workflow-added) genuine?",
              f"FABRICATED by the succession-scan agent — {len(fab)} invented row(s) deleted; "
              f"real education from the cited source inserted ({len(reps)} row(s)). " + ev["evidence_note"][:300],
              "corrected", "high", ev.get("evidence_url", ""), "education-fabrication audit",
              "systematic fabrication; see RESEARCH_LOG 2026-06-04")
        # the person's page should cite the bio that settled it
        if ev.get("evidence_url"):
            row = cur.execute("SELECT fc_sources FROM people WHERE id=?", (pid,)).fetchone()
            srcs = (row[0] or "") if row else ""
            if ev["evidence_url"] not in srcs:
                cur.execute("UPDATE people SET fc_sources=? WHERE id=?",
                            ((srcs + " | " if srcs else "") + ev["evidence_url"], pid))

    # suspect (no source, internally impossible): a claim with no source doesn't ship
    if sus:
        for r in sus:
            cur.execute("DELETE FROM education WHERE rowid=?", (r["edu_rowid"],))
            deleted += 1
            cleared += 1
        ev = sus[0]
        fclog(slug_of.get(pid, ""), name, "education (workflow-added) genuine?",
              f"SUSPECT — {len(sus)} unsupported row(s) deleted (no source states this education; "
              f"record internally impossible or contradicts the person's own stated path). " + ev["evidence_note"][:300],
              "removed-unsupported", "medium", ev.get("evidence_url", ""), "education-fabrication audit", "")

    # plausible inference: kept, but the inference is logged
    if inf:
        ev = inf[0]
        fclog(slug_of.get(pid, ""), name, "studied-with inference",
              "Instructor kept as a documented lineage inference (school confirmed; the named teacher "
              "was the program's primary metals instructor in the right era). " + ev["evidence_note"][:300],
              "inferred", "medium", ev.get("evidence_url", ""), "education-fabrication audit", "")

print(f"education purge: {deleted} rows deleted ({cleared} of them suspect-unsupported), {inserted} real rows inserted")

# ---------------------------------------------------------------- (2) disputed / low re-verification
resolved = improved = unfindable = 0
for path in ("/tmp/acmet_disputed_A.json", "/tmp/acmet_disputed_B.json"):
    batch = json.load(open(path))
    for p in batch["people"]:
        pid, verdict = p["id"], p["verdict"].upper()
        slug = slug_of.get(pid, "")
        alive = p.get("fc_alive") or "unknown"
        if alive not in ("yes", "no", "unknown"):
            alive = "unknown"          # never 'likely' anything
        if verdict in ("RESOLVED", "IMPROVED"):
            sets, vals = ["fc_alive=?", "fc_confidence=?", "fc_verified=?", "fc_checked=?"], [
                alive, p.get("fc_confidence") or "medium", "reverified-2026-06-04", TODAY]
            for col in ("fc_current_role", "fc_summary", "fc_sources"):
                if p.get(col):
                    sets.append(f"{col}=?"); vals.append(p[col])
            vals.append(pid)
            cur.execute(f"UPDATE people SET {', '.join(sets)} WHERE id=?", vals)
            fclog(slug, p["name"], "disputed/low re-verification",
                  (p.get("notes") or "")[:400] or verdict.lower(),
                  "confirmed" if verdict == "RESOLVED" else "improved",
                  p.get("fc_confidence") or "medium",
                  (p.get("fc_sources") or "").split(" | ")[0], "re-verification batch", p.get("evidence_check", "")[:200])
            resolved += verdict == "RESOLVED"
            improved += verdict == "IMPROVED"
        else:
            cur.execute("UPDATE people SET fc_checked=? WHERE id=?", (TODAY, pid))
            fclog(slug, p["name"], "disputed/low re-verification",
                  "Re-searched 2026-06-04; still unfindable — left held back. " + (p.get("notes") or "")[:300],
                  "unverifiable", "low", "", "re-verification batch", "")
            unfindable += 1

print(f"disputed pass: {resolved} resolved, {improved} improved, {unfindable} unfindable (left held back)")
con.commit()

# ---------------------------------------------------------------- report
print("--- reverified people now buildable ---")
for r in cur.execute("SELECT id,name,fc_confidence FROM people WHERE fc_verified='reverified-2026-06-04'"):
    print(" | ".join(str(x) for x in r))
print("--- education rows remaining with instructor (workflow cohort) ---")
for r in cur.execute("""SELECT p.name, e.school, e.instructor FROM education e JOIN people p ON p.id=e.person_id
        WHERE e.instructor!='' AND (p.kind='person-gap-addition' OR p.fc_verified IN ('snag-gap-2026','succession-scan'))"""):
    print(" | ".join(str(x) for x in r))
con.close()
print("done.")
