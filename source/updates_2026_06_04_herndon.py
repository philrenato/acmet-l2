#!/usr/bin/env python3
"""
updates_2026_06_04_herndon.py — Mark Herndon, prompted by an editor tip (Phil,
2026-06-04). House rule applied: nothing goes in on the tip alone — claims were
re-verified against fetched URLs, then adversarially re-checked.

What the tip claimed vs what we publish:
  - "He taught at IAIA"
      -> VERIFIED: IAIA's own event page for "The Stories We Carry" lists him
         as "Mark Herndon, faculty '05–'15" (live page bot-blocked; text
         confirmed via the 2024 Wayback capture). Discipline jewelry/metals is
         SUPPORTED by his LinkedIn headline + an IAIA Chronicle article — so
         we state the ROLE ("taught jewelry and metals"), no rank.
  - "herndonforge.com is what he's up to now"
      -> VERIFIED (his own site): Herndon Forge, Santa Fe NM, run with his
         wife, designer Naomi Herndon.
  - LinkedIn education (MFA Metalsmithing & Jewelry, UNT 2001–2004; BFA
    Sculpture, Corcoran/GWU 1993–1997)
      -> SUPPORTED (LinkedIn only; no institutional page corroborates the
         exact years). Recorded with that caveat in factcheck.
  - "He studied with Harlan" (= Harlan Butt, UNT)
      -> INFERRED per the documented lineage rule (UNT metals MFA in Butt's
         era, Butt the program's longtime primary metals professor) + the
         editor's direct statement. No fetched page states it; noted as such.

Deliberately NOT claimed: any tribal affiliation — IAIA's artist list tags
Native artists with a tribe + grad year; Herndon is tagged only "faculty
'05–'15", so no ethnicity is stated or implied.

Cross-links this creates: Herndon -> IAIA (program 185, former faculty
2005–2015); Herndon -> UNT (program 109, alumni via education.school);
Herndon <-> Harlan Butt (person 115, teacher/student via education.instructor).
"""
import sqlite3

DB = "acmet.db"
TODAY = "2026-06-04"

con = sqlite3.connect(DB)
cur = con.cursor()

# ---------------------------------------------------------------- Mark Herndon (new person)
cur.execute("SELECT id FROM people WHERE slug='gap/mark-herndon'")
row = cur.fetchone()
if row:
    mark_id = row[0]
    print(f"Mark Herndon already present (id {mark_id}) — updating in place")
else:
    cur.execute("""INSERT INTO people
        (slug, name, kind, currently_at, current_role,
         fc_alive, fc_still_in_job, fc_current_role, fc_current_link,
         fc_summary, fc_confidence, fc_verified, fc_sources, fc_checked)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        "gap/mark-herndon", "Mark Herndon", "person-gap-addition",
        "Herndon Forge (Santa Fe, NM)",
        "Metalsmith; runs Herndon Forge with designer Naomi Herndon",
        "yes", "no",
        "Metalsmith; runs Herndon Forge with designer Naomi Herndon",
        "https://herndonforge.com",
        ("Mark Herndon is a metalsmith based in Santa Fe, New Mexico, where he "
         "and his wife, designer Naomi Herndon, run Herndon Forge, a studio "
         "making Southwestern jewelry in the foothills of the Sangre de Cristo "
         "mountains. He earned a BFA in Sculpture from the Corcoran School of "
         "the Arts and Design at The George Washington University (1997) and an "
         "MFA in Metalsmithing and Jewelry from the University of North Texas "
         "(2004), where he studied with Harlan Butt. From 2005 to 2015 he "
         "taught jewelry and metals at the Institute of American Indian Arts in "
         "Santa Fe; his work appears in “The Stories We Carry” "
         "(2022–2025), the IAIA Museum of Contemporary Native Arts "
         "exhibition of contemporary jewelry from its permanent collection. His "
         "metalwork also spans pattern-welded (damascus) steel and sculptural "
         "vessels."),
        "high", "phil-added",
        ("https://herndonforge.com | "
         "https://herndonforge.com/pages/about-us | "
         "https://iaia.edu/event/the-stories-we-carry/ | "
         "http://web.archive.org/web/20240526143938/https://iaia.edu/event/the-stories-we-carry/ | "
         "https://chronicle.iaia.edu/breaking-jewelry/ | "
         "https://www.linkedin.com/in/mark-herndon-35781236/"),
        TODAY))
    mark_id = cur.lastrowid
    print(f"added Mark Herndon (id {mark_id})")

cur.execute("DELETE FROM education WHERE person_id=?", (mark_id,))
cur.executemany("INSERT INTO education (person_id, level, school, years, major, degree, instructor) VALUES (?,?,?,?,?,?,?)", [
    (mark_id, "Undergraduate", "Corcoran School of the Arts and Design, The George Washington University",
     "1993 to 1997", "Sculpture", "BFA", ""),
    (mark_id, "Graduate", "University of North Texas",
     "2001 to 2004", "Metalsmithing/Jewelry", "MFA", "Harlan Butt"),
])
print("education rows written (Corcoran BFA; UNT MFA under Harlan Butt)")

# ---------------------------------------------------------------- program_faculty link (IAIA = 185)
cur.execute("SELECT 1 FROM program_faculty WHERE program_id=185 AND name='Mark Herndon'")
if not cur.fetchone():
    cur.execute("INSERT INTO program_faculty (program_id, name, person_url, status, years) VALUES (185,'Mark Herndon',NULL,'former','2005 to 2015')")
    print("linked Mark Herndon -> Institute of American Indian Arts (former, 2005 to 2015)")

# ---------------------------------------------------------------- factcheck audit rows
cur.executemany("""INSERT INTO factcheck
    (entity_type, slug, name, question, finding, status, confidence,
     source_url, source_title, date_checked, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", [
    ("person", "gap/mark-herndon", "Mark Herndon", "taught at IAIA?",
     "IAIA's own event page for “The Stories We Carry” lists “Mark Herndon, faculty '05–'15” among contributing artists — faculty 2005–2015 confirmed by the institution.",
     "confirmed", "high",
     "http://web.archive.org/web/20240526143938/https://iaia.edu/event/the-stories-we-carry/",
     "IAIA: The Stories We Carry (Wayback capture; live page bot-blocked)", TODAY,
     "discipline (jewelry/metals) supported by LinkedIn headline + IAIA Chronicle; role stated, no rank"),
    ("person", "gap/mark-herndon", "Mark Herndon", "current activity?",
     "Runs Herndon Forge in Santa Fe, NM with his wife, designer Naomi Herndon — his own studio site.",
     "confirmed", "high",
     "https://herndonforge.com/pages/about-us", "Herndon Forge — About", TODAY, ""),
    ("person", "gap/mark-herndon", "Mark Herndon", "education?",
     "MFA Metalsmithing & Jewelry, University of North Texas, 2001–2004; BFA Sculpture, Corcoran School of the Arts and Design (GWU), 1993–1997.",
     "supported", "medium",
     "https://www.linkedin.com/in/mark-herndon-35781236/", "LinkedIn (editor-relayed screenshot)", TODAY,
     "LinkedIn-only for the exact years; no institutional page found to corroborate"),
    ("person", "gap/mark-herndon", "Mark Herndon", "studied with Harlan Butt?",
     "Inferred per the lineage rule — UNT metals MFA 2001–2004, within Harlan Butt's tenure as the program's longtime primary metals professor — and stated directly by the editor (Phil Renato). No fetched page states it.",
     "inferred", "medium",
     "https://www.linkedin.com/in/mark-herndon-35781236/", "lineage inference + editor statement", TODAY,
     "a fetched page naming Butt as his teacher would harden this"),
])
print("factcheck audit rows appended (4)")

con.commit()

# ---------------------------------------------------------------- report
print("--- person ---")
for r in cur.execute("SELECT id,name,current_role,fc_confidence,fc_checked FROM people WHERE id=?", (mark_id,)):
    print(" | ".join(str(x) for x in r))
print("--- education ---")
for r in cur.execute("SELECT level,school,years,degree,instructor FROM education WHERE person_id=?", (mark_id,)):
    print(" | ".join(str(x) for x in r))
print("--- program link ---")
for r in cur.execute("SELECT program_id,name,status,years FROM program_faculty WHERE name='Mark Herndon'"):
    print(" | ".join(str(x) for x in r))
con.close()
print("done.")
