#!/usr/bin/env python3
"""updates_2026_06_05_dedup.py — the duplicate/realness pass (Phil, 2026-06-05).

What the audit (audit_dups.py) found and this script fixes:

1) STALE-ID program_faculty rows: 158 rows with temple.edu person URLs sit on
   gap/snag-gap programs they never belonged to (Fuller Craft Museum carrying
   the Cleveland Institute of Art roster, Brookline Arts Center carrying
   Kansas's, McMurry carrying Kent State's…). Every one is an exact twin of a
   row on its correct archive program (proven before deletion) — leftovers of
   an old DB renumbering. Deleted.

2) STALE-ID education rows: same disease on people — gap-addition people
   carrying an archive person's education verbatim (Rachel Shimpock with Pam
   Lins's schooling, "Jim Charles" with Charles Loloma's). Deleted only when
   the row is an exact twin of an archive person's row AND has the archive
   signature (no degree/major of its own).

3) DUPLICATE PROGRAMS (same school, two published pages): the gap loaders
   missed existing archive rows when the name had changed (Beaver/Arcadia,
   UTPA/UTRGV, Academy of Art College/University, SUNY old/new styles,
   TTU Appalachian, Nebraska Wesleyan OCR garble) or SNAG listed a school
   twice (Ox-Bow, Craft Alliance, Glassell, Front Range). Keep the archive row
   (or the better-named snag row), move unique current-faculty links over,
   delete the dup.

4) DUPLICATE PEOPLE: Phil Renato (the archive's PHIL CARRIZZI, name-change)
   vs gap "Phillip Renato"; Bill/William R. Derrevere; Andy/Andrew Lowrie;
   Kristi/Kristina Glick (same person — her own bio: goes by Kristi, MFA East
   Carolina, now heads ISU metals); Caryn (L.) Hetherston. Merge into one.

5) Shadow-tree rows that got fact-checked by mistake (and therefore publish
   second pages): program 203 "Southern Illinois University" (history tree,
   = 65 Carbondale), person 224 "CARLYLE SMITH" (history tree, = 90
   CARLYLE H. SMITH). fc_checked -> NULL, the shadow-row convention.

6) Name fix: program 22 "Nebraska Wesl e yan University" (archive OCR garble)
   -> "Nebraska Wesleyan University".

Backs up the DB first. Rerunnable (every step is idempotent).
"""
import os, re, shutil, sqlite3, time

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "acmet.db")
bak = DB + ".bak-dedup-" + time.strftime("%H%M%S")
shutil.copy2(DB, bak)
print(f"backup: {bak}")

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
cur = con.cursor()
nrm = lambda s: re.sub(r"\s+", " ", (s or "").replace(":80", "").strip().lower())

# ---- 1) stale program_faculty rows on gap programs (temple.edu URLs) --------
stale = list(cur.execute("""SELECT pf.rowid, pf.name, pf.person_url FROM program_faculty pf
    JOIN programs p ON p.id=pf.program_id
    WHERE p.slug LIKE '%gap%' AND pf.person_url LIKE '%temple.edu%'"""))
arch = {(nrm(r["name"]), nrm(r["person_url"])) for r in cur.execute(
    """SELECT pf.name, pf.person_url FROM program_faculty pf
       JOIN programs p ON p.id=pf.program_id WHERE p.slug NOT LIKE '%gap%'""")}
doomed = [r["rowid"] for r in stale if (nrm(r["name"]), nrm(r["person_url"])) in arch]
no_twin = [r for r in stale if (nrm(r["name"]), nrm(r["person_url"])) not in arch]
assert not no_twin, f"stale pf rows without archive twin — refuse to guess: {no_twin}"
cur.executemany("DELETE FROM program_faculty WHERE rowid=?", [(i,) for i in doomed])
print(f"stale program_faculty rows deleted: {len(doomed)}")
# and the fully orphaned ones (program_id with no program at all — same era)
cur.execute("""DELETE FROM program_faculty WHERE program_id NOT IN (SELECT id FROM programs)""")
print(f"orphaned program_faculty rows deleted: {cur.rowcount}")

# ---- 2) stale education rows on gap people ----------------------------------
ekey = lambda r: tuple(nrm(r[k]) for k in ("school", "years", "major", "degree", "instructor", "level"))
arch_edu = {ekey(r) for r in cur.execute(
    """SELECT e.* FROM education e JOIN people pe ON pe.id=e.person_id WHERE pe.kind='person'""")}
gap_edu = list(cur.execute(
    """SELECT e.rowid, e.* FROM education e JOIN people pe ON pe.id=e.person_id
       WHERE pe.kind='person-gap-addition'"""))
doomed = [r["rowid"] for r in gap_edu if ekey(r) in arch_edu]
cur.executemany("DELETE FROM education WHERE rowid=?", [(i,) for i in doomed])
print(f"stale education rows deleted: {len(doomed)}")

# ---- 3) duplicate programs: move unique faculty links, delete the dup -------
PROG_DUPS = {  # dead id -> kept id
    559: 22,    # Nebraska Wesleyan (snag) -> archive row
    586: 71,    # SUNY Buffalo State (snag) -> State University College at Buffalo
    587: 74,    # SUNY New Paltz (snag) -> State University of New York at New Paltz
    405: 83,    # Academy of Art University (snag) -> Academy of Art College
    640: 90,    # UTRGV (snag) -> The University of Texas Pan American
    614: 155,   # Tennessee Tech / Appalachian (snag) -> Appalachian Center for Crafts, T.T.U.
    418: 192,   # Arcadia University (snag) -> Beaver College
    570: 569,   # Ox-Bow School of Art -> Ox-Bow School of Art & Artists' Residency
    486: 487,   # Front Range CC (generic) -> Larimer Campus (where the metals sequence is)
    456: 457,   # Craft Alliance -> Craft Alliance Center of Art and Design
    496: 173,   # Glassell Studio School (snag) -> Glassell School of Art / The MFA
    585: 72,    # SUNY College at Brockport (snag) -> State University of New York at Brockport
}
for dead, keep in PROG_DUPS.items():
    if not cur.execute("SELECT 1 FROM programs WHERE id=?", (dead,)).fetchone(): continue
    have = {nrm(r["name"]) for r in cur.execute(
        "SELECT name FROM program_faculty WHERE program_id=?", (keep,))}
    moved = 0
    # fetchall first — mutating while iterating the same cursor skips rows
    for r in cur.execute("SELECT rowid, name FROM program_faculty WHERE program_id=?", (dead,)).fetchall():
        if nrm(r["name"]) in have:
            cur.execute("DELETE FROM program_faculty WHERE rowid=?", (r["rowid"],))
        else:
            cur.execute("UPDATE program_faculty SET program_id=? WHERE rowid=?", (keep, r["rowid"]))
            moved += 1
    cur.execute("DELETE FROM programs WHERE id=?", (dead,))
    print(f"program dup {dead} -> kept {keep} (+{moved} faculty links moved)")

# ---- 4) duplicate people -----------------------------------------------------
# Phil Renato: archive 217 (PHIL CARRIZZI -> Phil Renato) is the record; gap 591 dies.
# Derrevere: archive 154 (fc already covers the Ghost Ranch teaching); gap 802 dies,
#   the Ghost Ranch faculty link takes his listed name.
# Lowrie: keep gap 552, rename to the name he goes by (page andy-lowrie.html);
#   snag 933 (Peters Valley) dies.
# Glick: keep 629 Kristina Glick (heads ISU metals); snag 806 (Goshen) dies —
#   the Goshen link becomes former-faculty under her listed name.
# Hetherston: keep 760, take the fuller listed name; snag 937 (Peters Valley) dies.
PEOPLE_DUPS = {591: 217, 802: 154, 933: 552, 806: 629, 937: 760}
for dead in PEOPLE_DUPS:
    cur.execute("DELETE FROM education WHERE person_id=?", (dead,))
    cur.execute("DELETE FROM people WHERE id=?", (dead,))
print(f"duplicate people removed: {len(PEOPLE_DUPS)}")

cur.execute("UPDATE people SET name='Andy Lowrie' WHERE id=552")
cur.execute("""UPDATE people SET name='Caryn L. Hetherston',
    current_role='Metalsmithing/Jewelry Instructor (also teaches Fine Metals workshops at Peters Valley School of Craft)',
    fc_summary='Metalsmithing/Jewelry Instructor (40 yrs craft, ~10 yrs teaching at the Museum), Delaware Art Museum; also teaches Fine Metals workshops at Peters Valley School of Craft.',
    fc_sources=fc_sources || ' | https://petersvalley.org/instructors/caryn-l-hetherston/'
    WHERE id=760""")
# faculty links point at the kept person's listed name (so the index doesn't
# grow a mention-only twin)
cur.execute("UPDATE program_faculty SET name='William R. Derrevere' WHERE name='Bill Derrevere'")
cur.execute("UPDATE program_faculty SET name='Andy Lowrie' WHERE name LIKE 'Andrew%Lowrie%'")
cur.execute("UPDATE program_faculty SET name='Caryn L. Hetherston' WHERE name='Caryn Hetherston'")
cur.execute("UPDATE program_faculty SET name='Kristina Glick', status='former' WHERE name='Kristi Glick'")

# ---- 5) shadow-tree rows that publish second pages ---------------------------
cur.execute("UPDATE programs SET fc_checked=NULL WHERE id=203")   # SIU (history tree) = 65
cur.execute("UPDATE people  SET fc_checked=NULL WHERE id=224")    # CARLYLE SMITH (history tree) = 90

# ---- 6) the OCR garble -------------------------------------------------------
cur.execute("UPDATE programs SET name='Nebraska Wesleyan University' WHERE id=22")

con.commit()
# quick post-checks
n = cur.execute("""SELECT COUNT(*) FROM program_faculty pf JOIN programs p ON p.id=pf.program_id
    WHERE p.slug LIKE '%gap%' AND pf.person_url LIKE '%temple.edu%'""").fetchone()[0]
print(f"post: stale pf rows remaining = {n}")
print("post: published programs =",
      cur.execute("SELECT COUNT(*) FROM programs WHERE fc_checked IS NOT NULL").fetchone()[0])
print("post: published-eligible people =",
      cur.execute("SELECT COUNT(*) FROM people WHERE fc_checked IS NOT NULL").fetchone()[0])
con.close()
print("done — now rebuild (build_site, build_graph, build_map, build_lineage) and write redirect stubs.")
