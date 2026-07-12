#!/usr/bin/env python3
"""Add Jim Binnion (mokume-gane artist, JBMA). Rerunnable — checks slug before inserting."""
import sqlite3

conn = sqlite3.connect("acmet.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

SLUG = "gap/jim-binnion"
existing = c.execute("SELECT id FROM people WHERE slug=?", (SLUG,)).fetchone()
if existing:
    print(f"already present as person_id {existing['id']}, skipping insert")
    person_id = existing["id"]
else:
    c.execute("""
        INSERT INTO people (slug, name, kind, currently_at, currently_at_url,
            current_role, since_year, fc_alive, fc_still_in_job, fc_current_role,
            fc_current_link, fc_summary, fc_confidence, fc_verified, fc_sources, fc_checked)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        SLUG, "Jim Binnion", "person-gap-addition",
        "James Binnion Metal Arts (JBMA)", "https://mokume-gane.com",
        "Founder and principal, James Binnion Metal Arts; mokume-gane artist and jewelry-metals instructor",
        "1991", "yes", "yes",
        "Founder and principal, James Binnion Metal Arts; mokume-gane artist and jewelry-metals instructor",
        "https://mokume-gane.com/jbma-mokume-studio/jim-binnion/",
        'Jim Binnion (James Binnion) is a mokume-gane artist and metalsmith based in Bellingham, WA. '
        'After nine years as a U.S. Navy submarine electronics technician and thirteen years as a '
        'Silicon Valley electronics/research engineer, he took evening and weekend jewelry classes at '
        'the Revere Academy of Jewelry Arts in San Francisco under Alan Revere and George McLean, '
        'teaching his first mokume-gane workshop there in 1984. In 1991 he founded James Binnion Metal '
        'Arts (JBMA), pioneering electric-kiln firing for mokume-gane, and became a full-time jewelry '
        'maker in 1999. He has presented research on mokume and jewelry metallurgy at the Santa Fe '
        'Symposium (20+ years, with multiple awards), the Jewelry Technology Forum, and the Jewellery '
        'Materials Congress, and taught mokume workshops with Chris Ploof at Rio Grande (2017-2018). He '
        'is the author of "Jewelry Metals: A Guide to Working with Common Alloys" (2015), a contributor '
        'to "Mokume Gane: A Comprehensive Study," and a board member of The Jewelry Symposium.',
        "high", "phil-added",
        "https://mokume-gane.com/jbma-mokume-studio/jim-binnion/ | https://mokume-gane.com | "
        "https://www.thejewelrysymposium.com/team-bio/jim-binnion",
        "2026-07-12",
    ))
    person_id = c.lastrowid
    print(f"inserted person_id {person_id}")

# education: sourced directly ("studied under Alan Revere, George McLean, and others")
edu_exists = c.execute(
    "SELECT 1 FROM education WHERE person_id=? AND school=?",
    (person_id, "Revere Academy of Jewelry Arts")).fetchone()
if not edu_exists:
    c.execute("""
        INSERT INTO education (person_id, level, school, years, major, degree, instructor)
        VALUES (?,?,?,?,?,?,?)
    """, (person_id, "Other", "Revere Academy of Jewelry Arts", "early 1980s", "",
          "Evening/weekend jewelry classes", "Alan Revere, George McLean"))
    print("inserted education row: Revere Academy")
else:
    print("education row already present, skipping")

# program_faculty: canonical program ids only (deduped programs keep id=46 for Revere,
# the other Revere row id=253 is an old-tree shadow build_site.py drops)
FACULTY = [
    (46, "1984-present"),    # Revere Academy of Jewelry Arts (workshops since first 1984 class)
    (583, "2017-2018"),      # Rio Grande (mokume workshops taught with Chris Ploof)
]
for prog_id, years in FACULTY:
    dup = c.execute(
        "SELECT 1 FROM program_faculty WHERE program_id=? AND name=?",
        (prog_id, "Jim Binnion")).fetchone()
    if dup:
        print(f"program_faculty row for program_id {prog_id} already present, skipping")
        continue
    c.execute("""
        INSERT INTO program_faculty (program_id, name, person_url, status, years)
        VALUES (?,?,?,?,?)
    """, (prog_id, "Jim Binnion", "", "workshop", years))
    print(f"inserted program_faculty row: program_id {prog_id}, years {years}")

conn.commit()
conn.close()
print("done")
