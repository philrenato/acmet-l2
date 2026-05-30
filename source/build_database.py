#!/usr/bin/env python3
"""
build_database.py — parse the recovered Academic Metals Directory raw mirror
into a relational SQLite DB (acmet.db) of people + programs, ready for the
fact-checking / updating project.

Reads the path-faithful HTML mirror under ARCHIVE_RAW (the frozen recovery).
Writes acmet.db + CSV/JSON exports under EXPORTS.

The directory's pages are structured FrontPage cards:
  * PERSON card  : <h1>NAME</h1>, "Date of Birth", "TEACHING EXPERIENCE"
                   ("Currently teaching at: <a>School</a> ... since YYYY"),
                   "UNDERGRADUATE/GRADUATE EDUCATION" (School/Years/Major/
                   Degree/Instructor, with <a> links to school + instructor
                   cards), and a "BIOGRAPHY" link to biographies/bNN.html.
  * SCHOOL page  : <h1>School</h1>, address, "program started in YYYY",
                   "FACULTY" (<a> links to person cards), "DEGREES".
  * BIO (bNN)    : <title>Biography: Name</title> + prose.

Nothing is invented; blank fields stay blank. Raw section text is preserved
in the DB for auditability.
"""

import csv
import json
import os
import re
import sqlite3
import sys
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_RAW = os.environ.get("ARCHIVE_RAW", os.path.join(HERE, "archive", "raw"))
# fall back to the in-place recovery layout when developing pre-move
if not os.path.isdir(ARCHIVE_RAW):
    alt = os.path.join(HERE, "amd-recovery", "raw")
    if os.path.isdir(alt):
        ARCHIVE_RAW = alt
DB = os.environ.get("ACMET_DB", os.path.join(HERE, "acmet.db"))
EXPORTS = os.path.join(HERE, "exports")

DIR_HOSTS_DIRS = ("metalsdirectorypage", os.path.join("public_html", "mjcc", "local", "history"))


# --- text helpers -----------------------------------------------------------
def squeeze(s):
    return re.sub(r"\s+", " ", s or "").strip()


def collapse_split_digits(s):
    # FrontPage split years like "19 74" / "200 2" across <span> tags
    return re.sub(r"(?<=\d)\s+(?=\d)", "", s or "")


def field(after_label, text):
    """Value following 'Label:' up to the next known label, section header, or EOL."""
    labels = r"(?:Date of Birth|Place of Birth|Currently teaching at|Taught at|School|Years|Major|Degree|Instructor|Type|Location)"
    headers = r"(?:TEACHING EXPERIENCE|UNDERGRADUATE EDUCATION|GRADUATE EDUCATION|OTHER EDUCATION|OTHER RELATED|Students of|BIOGRAPHY|FACULTY|DEGREES)"
    m = re.search(rf"{after_label}\s*:\s*(.*?)(?=\s*{labels}\s*:|\s*{headers}|$)", text, re.I)
    return squeeze(m.group(1)) if m else ""


# --- classification ---------------------------------------------------------
def page_kind(url, title, text, soup):
    u = url.lower()
    if "/biographies/" in u or title.lower().startswith("biography"):
        return "bio"
    has_faculty = "FACULTY" in text and ("DEGREES" in text or "program started" in text.lower())
    has_person = ("TEACHING EXPERIENCE" in text or "Date of Birth" in text
                  or "UNDERGRADUATE EDUCATION" in text)
    if has_faculty and not has_person:
        return "school"
    if has_person:
        return "person"
    # index / hub pages
    if u.rstrip("/").endswith(("hhome.html", "intro.html", "index.html")) or "indexpage" in u:
        return "index"
    return "other"


def link_map(soup, base_url):
    """anchor-text(lower) -> absolute url, and a list of (text, url)."""
    pairs = []
    for a in soup.find_all("a", href=True):
        txt = squeeze(a.get_text(" "))
        pairs.append((txt, urljoin(base_url, a["href"])))
    return pairs


def find_card_link(pairs, needle):
    """url of the first card-link (sNN/pNN/bNN) whose anchor contains needle."""
    for txt, url in pairs:
        if needle.lower() in txt.lower() and re.search(r"/[sbp]\d+\.html?$", url.lower()):
            return url
    return ""


# --- parsers ----------------------------------------------------------------
def parse_person(url, title, text, soup, pairs):
    name = squeeze(soup.h1.get_text(" ")) if soup.h1 else (title or "")
    work = ""
    h6 = soup.find("h6")
    if h6:
        work = squeeze(h6.get_text(" "))
    flat = collapse_split_digits(squeeze(text))
    dob = field("Date of Birth", flat)
    pob = field("Place of Birth", flat)

    # currently teaching
    cur_school = cur_role = cur_since = ""
    m = re.search(r"Currently teaching at\s*:\s*(.*?)(?:\bTaught at\b|UNDERGRADUATE|$)", flat, re.I)
    if m:
        seg = squeeze(m.group(1))
        sm = re.search(r"since\s*(\d{4})", seg, re.I)
        cur_since = sm.group(1) if sm else ""
        # role = text between school name and 'since'
        seg2 = re.sub(r"\s*since\s*\d{4}.*$", "", seg, flags=re.I)
        cur_school = squeeze(seg2)
    # school url for current school: first school-type link near 'Currently'
    cur_school_url = ""
    for txt, lu in pairs:
        if txt and txt.lower() in (cur_school or "").lower() and re.search(r"/s\d+\.html?$", lu.lower()):
            cur_school_url = lu
            break

    # education blocks — undergrad stops at the real GRADUATE section;
    # graduate uses a negative lookbehind so it doesn't match insideUNDERGRADUATE.
    edu = []
    sections = {
        "Undergraduate": r"UNDERGRADUATE EDUCATION(.*?)(?=(?<!UNDER)GRADUATE EDUCATION|OTHER EDUCATION|OTHER RELATED|Students of|BIOGRAPHY|$)",
        "Graduate":      r"(?<!UNDER)GRADUATE EDUCATION(.*?)(?=OTHER EDUCATION|OTHER RELATED|Students of|BIOGRAPHY|$)",
    }
    for level, pat in sections.items():
        seg = re.search(pat, flat, re.I | re.S)
        if not seg:
            continue
        section = collapse_split_digits(squeeze(seg.group(1)))
        # a level may list several schools; split at each 'School:' marker
        chunks = re.split(r"(?=School\s*:)", section)
        for s in chunks:
            school = field("School", s)
            if not school and not field("Degree", s) and not field("Major", s):
                continue
            edu.append({
                "level": level,
                "school": school,
                "years": field("Years", s),
                "major": field("Major", s),
                "degree": field("Degree", s),
                "instructor": field("Instructor", s),
            })

    bio_url = ""
    for txt, lu in pairs:
        if "/biographies/b" in lu.lower():
            bio_url = lu
            break

    return {
        "name": name, "work": work, "dob": dob, "birthplace": pob,
        "currently_at": cur_school, "currently_at_url": cur_school_url,
        "current_role": cur_role, "since_year": cur_since,
        "education": edu, "bio_url": bio_url,
    }


def parse_school(url, title, text, soup, pairs):
    name = squeeze(soup.h1.get_text(" ")) if soup.h1 else (title or "")
    flat = squeeze(text)
    started = ""
    m = re.search(r"program started in\s*(\d{4})", flat, re.I)
    if m:
        started = m.group(1)
    # address: lines in the first dl before 'program started'
    addr = ""
    am = re.search(r"</h1>(.*?)(?:Metals program|FACULTY)", str(soup), re.S | re.I)
    # faculty = card links after 'FACULTY'
    faculty = []
    seen = set()
    for txt, lu in pairs:
        if re.search(r"/[sp]\d+\.html?$", lu.lower()) and txt and lu != url:
            # heuristic: faculty links carry a name (+ maybe years)
            nm = squeeze(re.sub(r"\d{4}\s*-\s*(present|\d{4})?", "", txt, flags=re.I))
            if nm and lu not in seen and "school" not in txt.lower():
                seen.add(lu)
                faculty.append({"name": nm, "url": lu})
    degrees = []
    dm = re.search(r"DEGREES(.*?)(?:To the best of|$)", flat, re.S | re.I)
    if dm:
        for d in re.findall(r"\b(B\.?F\.?A\.?|M\.?F\.?A\.?|B\.?A\.?|M\.?A\.?|B\.?S\.?|M\.?S\.?|Ph\.?D\.?|Certificate|Diploma)\b", dm.group(1)):
            if d not in degrees:
                degrees.append(d)
    return {"name": name, "started": started, "faculty": faculty, "degrees": degrees}


# --- db ---------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
  id INTEGER PRIMARY KEY, slug TEXT UNIQUE, name TEXT, kind TEXT,
  work_title TEXT, dob TEXT, birthplace TEXT,
  currently_at TEXT, currently_at_url TEXT, current_role TEXT, since_year TEXT,
  bio_url TEXT, source_url TEXT, source_ts TEXT
);
CREATE TABLE IF NOT EXISTS education (
  person_id INTEGER, level TEXT, school TEXT, years TEXT, major TEXT,
  degree TEXT, instructor TEXT
);
CREATE TABLE IF NOT EXISTS programs (
  id INTEGER PRIMARY KEY, slug TEXT UNIQUE, name TEXT, program_started TEXT,
  degrees TEXT, source_url TEXT, source_ts TEXT
);
CREATE TABLE IF NOT EXISTS program_faculty (
  program_id INTEGER, name TEXT, person_url TEXT
);
-- fact-check workspace (filled in the research phase)
CREATE TABLE IF NOT EXISTS factcheck (
  id INTEGER PRIMARY KEY, entity_type TEXT, slug TEXT, name TEXT,
  question TEXT, finding TEXT, status TEXT, confidence TEXT,
  source_url TEXT, source_title TEXT, date_checked TEXT, notes TEXT
);
"""


def slug_of(url):
    return urlparse(url).path.lstrip("/")


def main():
    if not os.path.isdir(ARCHIVE_RAW):
        sys.exit(f"raw mirror not found: {ARCHIVE_RAW}")
    os.makedirs(EXPORTS, exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)

    files = []
    for root, _d, fns in os.walk(ARCHIVE_RAW):
        for fn in fns:
            if fn.lower().endswith((".html", ".htm")):
                files.append(os.path.join(root, fn))

    n_person = n_school = n_bio = 0
    for path in sorted(files):
        rel = os.path.relpath(path, ARCHIVE_RAW)
        # reconstruct original url (netloc/path)
        url = "http://" + rel.replace(os.sep, "/")
        raw = open(path, "rb").read()
        try:
            soup = BeautifulSoup(raw, "html.parser")
        except Exception:
            continue
        title = squeeze(soup.title.get_text()) if soup.title else ""
        text = soup.get_text(" ")
        pairs = link_map(soup, url)
        kind = page_kind(url, title, text, soup)

        if kind == "person":
            p = parse_person(url, title, text, soup, pairs)
            if not p["name"]:
                continue
            cur = con.execute(
                """INSERT OR IGNORE INTO people
                   (slug,name,kind,work_title,dob,birthplace,currently_at,currently_at_url,
                    current_role,since_year,bio_url,source_url,source_ts)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (slug_of(url), p["name"], "person", p["work"], p["dob"], p["birthplace"],
                 p["currently_at"], p["currently_at_url"], p["current_role"], p["since_year"],
                 p["bio_url"], url, ""))
            pid = cur.lastrowid
            for e in p["education"]:
                con.execute("INSERT INTO education VALUES (?,?,?,?,?,?,?)",
                            (pid, e["level"], e["school"], e["years"], e["major"], e["degree"], e["instructor"]))
            n_person += 1
        elif kind == "school":
            s = parse_school(url, title, text, soup, pairs)
            cur = con.execute(
                """INSERT OR IGNORE INTO programs (slug,name,program_started,degrees,source_url,source_ts)
                   VALUES (?,?,?,?,?,?)""",
                (slug_of(url), s["name"], s["started"], ", ".join(s["degrees"]), url, ""))
            pgid = cur.lastrowid
            for f in s["faculty"]:
                con.execute("INSERT INTO program_faculty VALUES (?,?,?)", (pgid, f["name"], f["url"]))
            n_school += 1
        elif kind == "bio":
            n_bio += 1
    con.commit()

    # exports
    def export(table, cols):
        rows = con.execute(f"SELECT {cols} FROM {table}").fetchall()
        names = [c[0] for c in con.execute(f"SELECT * FROM {table} LIMIT 0").description]
        with open(os.path.join(EXPORTS, f"{table}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(names)
            for r in rows: w.writerow(r)
        return len(rows)

    export("people", "*"); export("programs", "*")
    export("education", "*"); export("program_faculty", "*")

    print(f"people={n_person}  schools={n_school}  bios(prose)={n_bio}")
    print(f"DB: {DB}\nexports: {EXPORTS}")


if __name__ == "__main__":
    main()
