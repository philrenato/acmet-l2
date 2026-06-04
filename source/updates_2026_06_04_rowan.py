#!/usr/bin/env python3
"""
updates_2026_06_04_rowan.py — Rowan University pass, prompted by an email from
Donna Sweigart (2026-06-04). House rule applied: nothing goes in on the email
alone — every fact below was re-verified against a fetched, live URL
(rowan.edu, her published CV/bio, workshop-school instructor pages).

What the email claimed vs what we publish:
  - "BFA in Studio Art (primary studio Metals/Jewelry), CAD included"
      -> VERIFIED: rowan.edu BFA page lists "Jewelry & Metals" as a studio
         area; the area is officially named the "Metals/Jewelry/CAD area"
         (faculty page). We cite the area NAME for the CAD claim — no
         catalog page quoting CAD inside the jewelry requirements would load.
  - "Donna Sweigart - Professor"
      -> Rowan research profile says Full Professor; the dept faculty page
         still says Associate Professor (pages lag promotions). Published as
         Professor with both links in sources.
  - "Maureen Duffy - 3/4 time"
      -> VERIFIED via her own bio + Peters Valley + Touchstone instructor
         pages (all carry the identical "3/4 time professor of Jewelry and
         Metalsmithing at Rowan University" line). NOTE: the ccca.rowan.edu
         bio URLs the DB cited are DEAD (301 to an unrelated college page) —
         replaced with live sources.
  - "3 additional adjunct faculty"
      -> EXCLUDED: unnamed, and Rowan's faculty directory is JS-rendered
         (unfetchable), so there is no public page to point at.

Backgrounds added ("where she and Maureen were before"):
  Sweigart: BFA Beaver College/Arcadia 1996; MFA Tyler/Temple 2004 (a Tyler
    alum — cross-links into the directory's home program); UW Seattle 2006;
    UT Pan American 2008-14 (MFA director 2010-12); UT Rio Grande Valley
    2015-19; Rowan 2020-.  (source: donnamasonsweigart.com/cv/)
  Duffy: BFA Moore College 2005 (3-D Design, Metals); MFA SUNY New Paltz
    2007 (Metals); 10 yrs production jeweler in Philadelphia; prior teaching
    Tyler, Towson, Moore, Millersville, New Paltz; Fleisher Art Memorial;
    workshops at Peters Valley + Touchstone (already linked as craft-school
    instructor rows).
"""
import sqlite3

DB = "acmet.db"
TODAY = "2026-06-04"

con = sqlite3.connect(DB)
cur = con.cursor()

# ---------------------------------------------------------------- Donna Sweigart (new person)
cur.execute("SELECT id FROM people WHERE slug='gap/donna-sweigart'")
row = cur.fetchone()
if row:
    donna_id = row[0]
    print(f"Donna Sweigart already present (id {donna_id}) — updating in place")
else:
    cur.execute("""INSERT INTO people
        (slug, name, kind, currently_at, current_role,
         fc_alive, fc_still_in_job, fc_current_role, fc_current_link,
         fc_summary, fc_confidence, fc_verified, fc_sources, fc_checked)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        "gap/donna-sweigart", "Donna Sweigart", "person-gap-addition",
        "Rowan University",
        "Professor of Art & Design; head of the Metals/Jewelry/CAD area",
        "yes", "yes",
        "Professor of Art & Design; head of the Metals/Jewelry/CAD area",
        "https://www.rowan.edu/arts/departments/art/facultystaff/sweigart.html",
        ("Donna Mason Sweigart is Professor of Art & Design at Rowan University "
         "(Glassboro, NJ), where she heads the Metals/Jewelry/CAD area and chairs "
         "the Department of Art. She earned her BFA in Metals/Jewelry from Beaver "
         "College (now Arcadia University) in 1996, with study abroad at the "
         "Glasgow School of Art, and her MFA in Metals/Jewelry/Computer-Aided "
         "Design from the Tyler School of Art, Temple University, in 2004. Before "
         "Rowan she was Associate Professor at the University of Texas Rio Grande "
         "Valley (2015-2019) and Assistant Professor at its predecessor, the "
         "University of Texas Pan American (2008-2014), where she directed the MFA "
         "program (2010-2012), with earlier appointments at the University of "
         "Washington and the University of South Florida. Honors include the New "
         "Jersey Governor's Award in Arts Education - Professional Artist Award "
         "(2023); her chapter 'A Reexamination of Jewelers' Titles and "
         "Nomenclature' appears in Digital Meets Handmade: Jewelry Design, "
         "Manufacture, and Art in the Twenty-First Century (SUNY Press, 2021)."),
        "high", "phil-added",
        ("https://www.rowan.edu/arts/departments/art/facultystaff/sweigart.html | "
         "https://www.researchwithrowan.com/en/persons/donna-sweigart | "
         "https://donnamasonsweigart.com/bio/ | "
         "https://donnamasonsweigart.com/cv/ | "
         "https://www.rowan.edu/arts/departments/art/programs/bfa.html"),
        TODAY))
    donna_id = cur.lastrowid
    print(f"added Donna Sweigart (id {donna_id})")

cur.execute("DELETE FROM education WHERE person_id=?", (donna_id,))
cur.executemany("INSERT INTO education (person_id, level, school, years, major, degree, instructor) VALUES (?,?,?,?,?,?,?)", [
    (donna_id, "Undergraduate", "Beaver College (now Arcadia University)", "1992-1996", "Metals/Jewelry", "BFA", ""),
    (donna_id, "Graduate", "Tyler School of Art/Temple University", "2002-2004", "Metals/Jewelry/Computer-Aided Design", "MFA", ""),
])

# ---------------------------------------------------------------- Maureen Duffy (person 488) — fill out + fix dead links
cur.execute("""UPDATE people SET
    current_role=?, fc_current_role=?, fc_current_link=?, fc_summary=?, fc_sources=?, fc_checked=?
    WHERE id=488""", (
    "Professor of Jewelry and Metalsmithing (3/4 time)",
    "Professor of Jewelry and Metalsmithing (3/4 time)",
    "http://www.maureenduffyjewelry.com/new-page-1",
    ("Maureen Duffy is a jeweler and metalsmith based in Philadelphia and a "
     "3/4-time Professor of Jewelry and Metalsmithing at Rowan University "
     "(Glassboro, NJ). She earned her BFA in 3-D Design with a concentration in "
     "Metals from Moore College of Art and Design (2005) and her MFA in Metals "
     "from SUNY New Paltz (2007). She spent ten years as a production jeweler "
     "for two Philadelphia jewelry companies and has shown and sold her "
     "hand-fabricated work in silver and gold for over fifteen years. She has "
     "also taught at the Tyler School of Art & Architecture, Towson University, "
     "Moore College of Art & Design, Millersville University, and SUNY New "
     "Paltz, teaches at Fleisher Art Memorial in Philadelphia, and leads "
     "workshops at Peters Valley School of Craft, Touchstone Center for Crafts, "
     "and Snow Farm."),
    ("http://www.maureenduffyjewelry.com/new-page-1 | "
     "https://www.touchstonecrafts.org/instructors/maureen-duffy/ | "
     "https://petersvalley.org/instructors/maureen-duffy/ | "
     "https://fleisher.org/event/fleisher-from-a-distance-making-an-engagement-ring-demonstration-with-maureen-duffy/ | "
     "https://www.rowan.edu/arts/departments/art/programs/jewelry.html"),
    TODAY))
print("updated Maureen Duffy (488): role, bio, live sources (dead ccca.rowan.edu links dropped)")

cur.execute("DELETE FROM education WHERE person_id=488")
cur.executemany("INSERT INTO education (person_id, level, school, years, major, degree, instructor) VALUES (?,?,?,?,?,?,?)", [
    (488, "Undergraduate", "Moore College of Art & Design", "2005", "3-D Design (Metals concentration)", "BFA", ""),
    (488, "Graduate", "State University of New York at New Paltz", "2007", "Metals", "MFA", ""),
])

# ---------------------------------------------------------------- program_faculty links
# survivors after build_site name-dedupe: Rowan=51, Tyler=96, Towson=93,
# Moore=552, Millersville=10, New Paltz=74, UTPA=90, UTRGV=640, UW=115
links = [
    (51,  "Donna Sweigart", "current", "2020 to present"),
    (640, "Donna Sweigart", "former",  "2015 to 2019"),
    (90,  "Donna Sweigart", "former",  "2008 to 2014"),
    (115, "Donna Sweigart", "former",  "2006"),
    (51,  "Maureen Duffy",  "current", ""),
    (96,  "Maureen Duffy",  "former",  ""),
    (93,  "Maureen Duffy",  "former",  ""),
    (552, "Maureen Duffy",  "former",  ""),
    (10,  "Maureen Duffy",  "former",  ""),
    (74,  "Maureen Duffy",  "former",  ""),
]
for pid, nm, status, yrs in links:
    cur.execute("SELECT 1 FROM program_faculty WHERE program_id=? AND name=?", (pid, nm))
    if not cur.fetchone():
        cur.execute("INSERT INTO program_faculty (program_id, name, person_url, status, years) VALUES (?,?,NULL,?,?)",
                    (pid, nm, status, yrs))
        print(f"linked {nm} -> program {pid} ({status})")

# ---------------------------------------------------------------- Rowan program record (51)
cur.execute("""UPDATE programs SET
    fc_current_status=?, fc_current_faculty=?, fc_sources=?, fc_checked=?
    WHERE id=51""", (
    ("Active. Jewelry & Metals is one of the named studio areas of the BFA in "
     "Art/Studio Art (and available within the BA in Art) in the Department of "
     "Art, Edelman College of Communication & Creative Arts; the area is "
     "officially the Metals/Jewelry/CAD area. Coursework spans piercing, "
     "riveting, high-temperature silver soldering, small-scale fabrication, "
     "forging, acid etching, vitreous enameling, casting, and advanced forming."),
    ("Donna Sweigart (Professor, head of the Metals/Jewelry/CAD area); "
     "Maureen Duffy (Professor of Jewelry and Metalsmithing, 3/4 time)"),
    ("https://www.rowan.edu/arts/departments/art/programs/bfa.html | "
     "https://www.rowan.edu/arts/departments/art/programs/jewelry.html | "
     "https://www.rowan.edu/arts/departments/art/facultystaff/sweigart.html | "
     "https://catalog.rowan.edu/preview_course_nopop.php?catoid=9&coid=30596 | "
     "https://donnamasonsweigart.com/cv/"),
    TODAY))
print("updated Rowan University (51): status, faculty, live sources")

con.commit()

# ---------------------------------------------------------------- report
for q, label in [
    ("SELECT id,name,current_role,fc_confidence FROM people WHERE id IN (488,?)", "people"),
    ("SELECT level,school,years,degree FROM education WHERE person_id IN (488,?)", "education"),
]:
    print(f"--- {label} ---")
    for r in cur.execute(q, (donna_id,)): print(" | ".join(str(x) for x in r))
print("--- rowan faculty links ---")
for r in cur.execute("SELECT program_id,name,status,years FROM program_faculty WHERE name IN ('Donna Sweigart','Maureen Duffy')"):
    print(" | ".join(str(x) for x in r))
con.close()
print("done.")
