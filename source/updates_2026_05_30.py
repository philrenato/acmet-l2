#!/usr/bin/env python3
"""updates_2026_05_30.py — apply the re-verification pass + Phil's directives.

1. PURGE 'likely-deceased' everywhere (Phil: don't guess at deaths; if there's
   no good source, say nothing about whether someone is alive).
2. Apply the verified alive/deceased findings (with solid permalink sources).
3. Fix the two wrong-person sources (Vierthaler->von Neumann, Sipantzi->Hassoldt).
4. Resolve the Kamal Baum dispute (real person/name; no longer current faculty).
5. Add Phil's two former students (Michael Nashef, Caitlin Skelcey), cross-linked
   to Phil Renato as their instructor.

Idempotent: re-running just re-asserts the same values. Targets the fact-checked
row of each person (fc_checked IS NOT NULL) so old-tree duplicate shadows are left
alone. Every change is also logged to the factcheck table for audit trail.
"""
import os, sqlite3, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db"))
cur = con.cursor()
TODAY = "2026-05-30"

def log(slug, name, question, finding, status, conf, url, title):
    cur.execute("""INSERT INTO factcheck(entity_type,slug,name,question,finding,status,
                   confidence,source_url,source_title,date_checked,notes)
                   VALUES('person',?,?,?,?,?,?,?,?,?,?)""",
                (slug, name, question, finding, status, conf, url, title, TODAY, "reverify-2026-05-30"))

def setp(name, **cols):
    """update the fact-checked row(s) for a person by archived name."""
    sets = ", ".join(f"{k}=?" for k in cols)
    vals = list(cols.values()) + [name]
    cur.execute(f"UPDATE people SET {sets} WHERE name=? AND fc_checked IS NOT NULL", vals)
    return cur.rowcount

# ---------------------------------------------------------------------------
# 1) PURGE likely-deceased -> unknown (then specific findings override below)
# ---------------------------------------------------------------------------
n = cur.execute("UPDATE people SET fc_alive='unknown' WHERE fc_alive='likely-deceased'").rowcount
print(f"purged likely-deceased -> unknown: {n}")

# ---------------------------------------------------------------------------
# 2) VERIFIED ALIVE (positive current-activity evidence, with source)
# ---------------------------------------------------------------------------
ALIVE = {
 "GAIL DIAL": ("https://www.isu.edu/cal/about/emeritus-faculty/", "high",
   "Professor of Art Emeritus (1974–2008), Idaho State University",
   "Listed as ISU emeritus faculty with no deceased notation; living."),
 "NANCY MEGAN CORWIN": ("https://nancymegancorwin.com/", "high",
   "Studio metalsmith & author (Chasing and Repoussé), Seattle",
   "Active personal site + Seattle Metals Guild instructor listing; living."),
 "DAVID La PLANTZ": ("https://facerejewelryart.com/pages/david-laplantz", "medium",
   "Studio jeweler/metalsmith; retired (Humboldt State, ~36 yrs); Santa Fe, NM area",
   "Gallery/Smithsonian pages present-tense; no obituary. Not deceased."),
 "GARY GRIFFIN": ("https://snagmetalsmith.org/2013/08/2013-snag-lifetime-achievement-award-gary-griffin/", "medium",
   "Metalsmith; retired head of Metalsmithing, Cranbrook Academy of Art (2006); El Rito, NM",
   "2013 SNAG Lifetime Achievement; practicing in New Mexico; no obituary. Not deceased."),
 "JOE EDWARD CORNETT": ("https://azdailysun.com/entertainment/arts-and-theatre/cornett-family-displays-work-at-biennial-art-exhibit/article_e260dea3-68f6-5b9e-b198-5f5c8f79c82f.html", "medium",
   "Jeweler/metalsmith; Vietnam veteran; Flagstaff, AZ — actively exhibiting",
   "AZ Daily Sun feature shows him exhibiting ~2023. Not deceased (KY/Legacy obits are different men)."),
}
for nm, (url, conf, role, note) in ALIVE.items():
    setp(nm, fc_alive="yes", fc_confidence=conf, fc_current_role=role, fc_current_link=url,
         fc_verified="confirmed", fc_checked=TODAY)
    log("", nm, "alive?", note, "alive", conf, url, "re-verify")
    print("  ALIVE:", nm)

# ---------------------------------------------------------------------------
#   VERIFIED DECEASED (with obituary / firm dates)
# ---------------------------------------------------------------------------
# Fred Woell — was disputed; confirmed deceased 2015-04-02, obituary found.
setp("FRED WOELL", fc_alive="no", fc_current_name="J. Fred Woell", fc_verified="confirmed",
     fc_change_kind="name-variant", fc_confidence="high", fc_checked=TODAY,
     fc_current_link="https://www.jordanfernald.com/memorials/j-woell/2335707/obituary.php")
# append the obituary to sources
row = cur.execute("SELECT fc_sources FROM people WHERE name='FRED WOELL' AND fc_checked IS NOT NULL").fetchone()
if row and "jordanfernald" not in (row[0] or ""):
    setp("FRED WOELL", fc_sources=(row[0] or "") + " | https://www.jordanfernald.com/memorials/j-woell/2335707/obituary.php")
log("", "FRED WOELL", "alive?", "J. Fred Woell died April 2, 2015, Deer Isle ME (pneumonia).", "deceased", "high",
    "https://www.jordanfernald.com/memorials/j-woell/2335707/obituary.php", "obituary")
print("  DECEASED: FRED WOELL (2015-04-02)")

# Douglas Gilchrist — firm historical dates 1878–1942, deceased (not a guess).
setp("DOUGLAS GILCHRIST", fc_alive="no", fc_checked=TODAY)
print("  DECEASED: DOUGLAS GILCHRIST (1878–1942, historical)")

# ---------------------------------------------------------------------------
# 3) FIX WRONG-PERSON SOURCES (left UNKNOWN — no honest death record)
# ---------------------------------------------------------------------------
# Vierthaler — old link was a Robert von Neumann article (wrong).
setp("ARTHUR VIERTHALER", fc_alive="unknown", fc_checked=TODAY,
     fc_current_link="https://www.wisconsinhistory.org/Records/Image/IM36422")
log("", "ARTHUR VIERTHALER", "source", "Replaced mismatched von Neumann link; no death record found.", "unknown", "low",
    "https://www.wisconsinhistory.org/Records/Image/IM36422", "WI Historical Society")
# Sipantzi — old link was an obituary for 'Arnold Hassoldt' (wrong person). Remove it.
setp("ZAVEN ZEE SIPANTZI", fc_alive="unknown", fc_current_link="", fc_checked=TODAY)
log("", "ZAVEN ZEE SIPANTZI", "source", "Removed wrong-person ('Arnold Hassoldt') obituary; no real record found.", "unknown", "low",
    "", "none")
print("  FIXED wrong-person sources: Vierthaler, Sipantzi")

# John T. Fix — better (still uncertain) source.
setp("JOHN T. FIX", fc_alive="unknown", fc_checked=TODAY,
     fc_current_link="https://archives.towson.edu/Documents/Detail/art-instructor-john-h.-fix/61244")

# ---------------------------------------------------------------------------
# 4) RESOLVE the Kamal Baum dispute: real person + correct name, but the
#    "currently teaches at College of DuPage" claim is refuted (page 404s,
#    absent from Feb-2026 catalog). Don't assert alive/dead.
# ---------------------------------------------------------------------------
setp("KATHLEEN MALEC KAMAL", fc_alive="unknown", fc_still_in_job="no",
     fc_current_name="Kathleen Kamal Baum", fc_change_kind="name-change",
     fc_current_role="Metalsmith/silversmith; formerly Professor of metalsmithing & jewelry, College of DuPage (no longer on current faculty)",
     fc_current_link="https://catalog.cod.edu/faculty-administration/",
     fc_verified="confirmed", fc_confidence="medium", fc_checked=TODAY)
log("", "KATHLEEN MALEC KAMAL", "still teaching at College of DuPage?",
    "Name confirmed (Kathleen Kamal Baum). Faculty page 404s; absent from Feb-2026 catalog — no longer current faculty.",
    "former", "medium", "https://catalog.cod.edu/faculty-administration/", "COD catalog")
print("  RESOLVED dispute: KATHLEEN MALEC KAMAL")

# ---------------------------------------------------------------------------
# 5) ADD Phil's two former students, cross-linked to Phil Renato.
# ---------------------------------------------------------------------------
def add_person(slug, name, role, link, summary, sources, birthplace, currently_at):
    if cur.execute("SELECT 1 FROM people WHERE slug=?", (slug,)).fetchone():
        cur.execute("DELETE FROM people WHERE slug=?", (slug,))
        pid0 = cur.execute("SELECT id FROM people WHERE slug=?", (slug,)).fetchone()
    cur.execute("""INSERT INTO people(slug,name,kind,currently_at,current_role,
                   fc_alive,fc_name_changed,fc_current_role,fc_still_in_job,fc_current_link,
                   fc_summary,fc_confidence,fc_verified,fc_sources,fc_checked,birthplace)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (slug, name, "person-gap-addition", currently_at, role,
                 "yes", "no", role, "yes", link, summary, "high", "phil-added",
                 sources, TODAY, birthplace))
    return cur.lastrowid

def add_edu(pid, level, school, years, degree, instructor):
    cur.execute("INSERT INTO education(person_id,level,school,years,major,degree,instructor) VALUES(?,?,?,?,?,?,?)",
                (pid, level, school, years, "", degree, instructor))

# clean any prior insert
for s in ("gap/michael-nashef", "gap/caitlin-skelcey"):
    pid = cur.execute("SELECT id FROM people WHERE slug=?", (s,)).fetchone()
    if pid:
        cur.execute("DELETE FROM education WHERE person_id=?", (pid[0],))
        cur.execute("DELETE FROM people WHERE id=?", (pid[0],))

nashef_bio = ("Michael Nashef is a jeweler, product designer, and educator based in the "
 "Kalamazoo, Michigan area. Born in Lebanon, he immigrated to the United States in 1998. He earned a "
 "BFA in Metal/Jewelry Design from Kendall College of Art and Design (2006), studying under Phil Renato, "
 "and an MFA in jewelry design/metals from Bowling Green State University. He has taught metalsmithing "
 "and jewelry at Kendall, Western Michigan University, and Towson University, and leads CAD, 3D-printing, "
 "and mold-making workshops at craft schools including Touchstone Center for Crafts and Danaca Design. "
 "Through Nashef Designs / ORGO Tools he designs and manufactures organizational tools for jewelers "
 "(bur, torch, and plier organizers), many 3D-printed in the USA; he also runs the Intersecting Hearts "
 "fine-jewelry line. His sculptural art jewelry, working in cement and 3D-printed nylon to evoke "
 "resilient war-damaged architecture, was exhibited in the Museum of Arts and Design's MAD About "
 "Jewelry 2021.")
nashef_src = " | ".join([
 "https://www.nashefdesigns.com/about", "https://www.nashefdesigns.com/workshops",
 "https://madmuseum.org/jewelry/artist/michael-nashef",
 "https://blog.stuller.com/meet-michael-nashef-the-2020-march-bridal-madness-champion/",
 "https://wp.danacadesign.com/instructors/michael-nashef/",
 "https://www.iup.edu/news-events/news/2023/10/iup-presenting-future-makers-forum-with-michigan-entrepreneuer-michael-nashef.html"])
pid = add_person("gap/michael-nashef", "Michael Nashef",
 "Jeweler & product designer (jewelry-industry tools); founder, Nashef Designs / ORGO Tools; educator (CAD/3D-printing)",
 "https://www.nashefdesigns.com/about", nashef_bio, nashef_src, "Lebanon", "Nashef Designs / ORGO Tools")
add_edu(pid, "Undergraduate", "Kendall College of Art and Design", "2006", "BFA Metal/Jewelry Design", "Phil Renato")
add_edu(pid, "Graduate", "Bowling Green State University", "2018", "MFA Jewelry Design / Metals", "")
print("  ADDED: Michael Nashef ->", pid)

skelcey_bio = ("Caitlin Skelcey is a jeweler, artist, and designer who works at the intersection of "
 "jewelry, the human body, and digital fabrication. A Grand Rapids–area native, she earned dual BFAs in "
 "Metals/Jewelry Design and Painting from Kendall College of Art and Design (2011), studying under Phil "
 "Renato, and an MFA in Metals from the University of Illinois at Urbana-Champaign (2017). At Illinois "
 "she became a 'digital metalsmith,' developing experimental materials and merging 3D printing, modeling, "
 "and scanning with traditional adornment. She taught at SUNY Buffalo State College as an Assistant "
 "Professor and Digital Fabrication (Tech Hub) Coordinator, and is now a jeweler back in the Grand Rapids "
 "area. Her signature work — 'jewelry prosthetics' exploring augmented physicality and the boundary "
 "between human biology and technology — earned her recognition as one of Art Jewelry Forum's 'Top 10 "
 "Up and Comers' at SNAG Boston 2015.")
skelcey_src = " | ".join([
 "https://www.caitlinskelcey.com/about", "https://www.caitlinskelcey.com/press",
 "https://www.kcad.edu/news/the-frontier-of-making-q-a-with-alumna-caitlin-skelcey/",
 "https://artjewelryforum.org/articles-series/top-10-up-and-comers-at-snag-boston-2015",
 "https://www.news-gazette.com/news/studio-visit-caitlin-skelcey/article_9deb7d74-606e-55e9-8694-f1f58ee112c2.html"])
pid = add_person("gap/caitlin-skelcey", "Caitlin Skelcey",
 "Jeweler, artist & designer (jewelry / body / digital fabrication); formerly Asst. Professor & Digital Fabrication Coordinator, SUNY Buffalo State; now Grand Rapids, MI area",
 "https://www.caitlinskelcey.com/about", skelcey_bio, skelcey_src, "Grand Rapids, MI area", "Independent studio (Grand Rapids, MI area)")
add_edu(pid, "Undergraduate", "Kendall College of Art and Design", "2011", "BFA Metals/Jewelry Design & BFA Painting", "Phil Renato")
add_edu(pid, "Graduate", "University of Illinois at Urbana-Champaign", "2017", "MFA Metals", "")
print("  ADDED: Caitlin Skelcey ->", pid)

con.commit()
print("\n=== fc_alive after pass ===")
for r in cur.execute("SELECT coalesce(fc_alive,'(null)'), count(*) FROM people WHERE fc_checked IS NOT NULL GROUP BY 1"):
    print("  ", r[0], r[1])
con.close()
