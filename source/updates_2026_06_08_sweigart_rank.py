#!/usr/bin/env python3
"""
updates_2026_06_08_sweigart_rank.py — fact-check pass (2026-06-08).

Donna Sweigart's entry led with the rank "Professor of Art & Design," while its
own footnote conceded that Rowan's department faculty page AND her own CV list
her as Associate Professor (tenured) and Chair. A fresh fetch of the school's
current page (rowan.edu/.../sweigart.html) reads "Associate Professor of Art &
Design"; her CV (donnamasonsweigart.com/cv) reads "Associate Professor of Art
(tenured), Chair of the Department of Art, 2020-present."

Phil's standing rank rule: rank comes from the SCHOOL'S OWN current/recent page
(people and self-bios say "professor" colloquially); conflicting evidence is
published at the best-evidenced value plus a footnote. The school's own page and
her CV both say Associate Professor, so the published rank is corrected to that;
the footnote is kept (now noting the research-profile/bio say Professor).

No other claim moved: education (Beaver/Arcadia BFA 1996 -> Tyler MFA 2004),
chair role, area headship, employment history, and honors all re-verified and
unchanged. Rerunnable. Sources unchanged in fc_sources.
"""
import sqlite3, shutil, os

BK = "acmet.db.bak-sweigart-rank-060800"
if not os.path.exists(BK):
    shutil.copy("acmet.db", BK)

con = sqlite3.connect("acmet.db")
cur = con.cursor()

NEW_ROLE = ("Associate Professor of Art & Design; chairs the Department of Art "
            "and heads the Metals/Jewelry/CAD area")

OLD_OPEN = "Donna Mason Sweigart is Professor of Art & Design at Rowan University"
NEW_OPEN = "Donna Mason Sweigart is Associate Professor of Art & Design at Rowan University"

OLD_FOOT = ("*Rank: Professor per Rowan's research profile, her own bio, and "
            "correspondence; the department's faculty page (its February 2023 "
            "archived roster included) and her own CV list Associate Professor "
            "and Chair of the Department of Art.*")
NEW_FOOT = ("*Rank: Rowan's faculty page and her CV list Associate Professor "
            "(tenured) and Chair of the Department of Art; a university research "
            "profile and her bio say Professor.*")

cur.execute("SELECT id, fc_summary FROM people WHERE name='Donna Sweigart'")
pid, summ = cur.fetchone()
summ2 = summ.replace(OLD_OPEN, NEW_OPEN).replace(OLD_FOOT, NEW_FOOT)
assert NEW_OPEN in summ2 and NEW_FOOT in summ2, "expected substrings not found — record changed?"

cur.execute("UPDATE people SET fc_current_role=?, fc_summary=?, "
            "fc_verified='reverified-2026-06-08' WHERE id=?",
            (NEW_ROLE, summ2, pid))

cur.execute("""INSERT INTO factcheck (entity_type, slug, name, question, finding,
    status, confidence, source_url, source_title, date_checked, notes)
    VALUES ('person','donna-sweigart','Donna Sweigart','current academic rank',
    'School faculty page (rowan.edu/.../sweigart.html) and her own CV both list Associate Professor (tenured) and Chair of the Department of Art; a research profile and self-bio say Professor. Published rank corrected to Associate Professor per the school-page-wins rank rule; footnote retained.',
    'corrected','high',
    'https://www.rowan.edu/arts/departments/art/facultystaff/sweigart.html | https://donnamasonsweigart.com/cv/',
    'Rowan faculty page; Sweigart CV','2026-06-08',
    'Rank rule: school own page is authoritative; conflicts footnoted')""")

con.commit()
print(f"updated person {pid}: rank -> Associate Professor; footnote rewritten")
con.close()
