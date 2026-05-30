#!/usr/bin/env python3
"""audit_coherence.py — additive coherence pass over acmet.db (2026-05-30).

Two safe, additive fixes (new columns only; never drops data):

1. people.fc_change_kind — separate the directory's most important signal
   (a genuine name change that would make someone un-findable) from archive
   OCR/spelling corrections that were mislabeled as "name changes".
     spelling-correction : archive typo fixed (Cirono->Cirino, Key->Ken Cory...)
     name-change         : genuine professional/legal name change (Carrizzi->Renato)
     name-variant        : added/dropped a maiden/married name but still findable
     (null)              : fc_name_changed != 'yes'

2. programs.school_type — classify the *kind* of institution (Phil: keep the
   non-university programs, just label them), so a private bench-jewelry school
   reads differently from a university art department.
"""
import os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db"))
cur = con.cursor()

def addcol(table, col, decl="TEXT"):
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info({table})")]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
        print(f"  + {table}.{col}")

addcol("people", "fc_change_kind")
addcol("programs", "school_type")

# ---------------------------------------------------------------------------
# 1) Name-change taxonomy. Keyed by the archived (original) name.
#    Hand-classified from the fc_summary evidence; the spelling-corrections are
#    self-evident from the name pair.
# ---------------------------------------------------------------------------
CHANGE_KIND = {
    # --- archive spelling / OCR fixes: NOT a life name change ---
    "ANTONIO CIRONO":        "spelling-correction",   # OCR: Cirono -> Cirino
    "CHARLOTTE NICHOLAS":    "spelling-correction",   # Nicholas -> Nichols (variant)
    "DAVID La PLANTZ":       "spelling-correction",   # spacing: La Plantz -> LaPlantz
    "HAROLD O'CONNER":       "spelling-correction",   # O'Conner -> O'Connor
    "JOSEFA FILOSKY":        "spelling-correction",   # Filosky -> Filkosky
    "KEY CORY":              "spelling-correction",   # OCR: Key -> Ken Cory
    "OLAF SKOOGFORS":        "spelling-correction",   # current==archived (was a bug)
    "RUTH PENNINGTON":       "spelling-correction",   # Pennington -> Penington
    # --- genuine name changes: would be MISSED under the new name ---
    "BARBARA NILAUSEN-K":    "name-change",           # -> Balpreet Kaur (conversion)
    "KATHLEEN MALEC KAMAL":  "name-change",           # -> Kathleen Kamal Baum (remarriage)
    "LYNDA WATSON-ABBOTT":   "name-change",           # dropped Abbott -> Lynda Watson
    "MICHELLE MILNER SCOTT": "name-change",           # dropped Scott -> Michelle Milner
    "PAMELA E. LINS":        "name-change",           # -> Pam Lins (professional)
    "PHIL CARRIZZI":         "name-change",           # -> Phil Renato (the marquee case)
    # --- name variants: maiden/married name added but still findable ---
    "DR. GERALDINE VELASQUEZ":"name-variant",          # + Khaner (middle)
    "HIROKO PIJANOWSKI":     "name-variant",           # + Sato (maiden)
    "JEFF GEORGANTES":       "name-variant",           # -> T Jeffrey (style)
    "MARY ANN SCHERR":       "name-variant",           # née Weckman (noted only)
    "MERRY RENK":            "name-variant",           # + Renk-Curtis (married)
    "SHARON CHURCH":         "name-variant",           # + McNabb (married; still Church pro)
}
n = 0
for name, kind in CHANGE_KIND.items():
    cur.execute("UPDATE people SET fc_change_kind=? WHERE name=? AND fc_name_changed='yes'", (kind, name))
    n += cur.rowcount
print(f"name-change kinds set: {n}")
# anything still flagged name_changed='yes' without a kind?
miss = cur.execute("SELECT name FROM people WHERE fc_name_changed='yes' AND fc_change_kind IS NULL").fetchall()
if miss: print("  UNCLASSIFIED name-change:", [m[0] for m in miss])

# ---------------------------------------------------------------------------
# 2) Institution-type classifier (keyword rules on the program name).
#    Order matters: most specific first.
# ---------------------------------------------------------------------------
def classify(nm):
    s = " " + (nm or "").lower() + " "
    # K-12 / day & prep schools (not post-secondary)
    if re.search(r"\b(country day|day school|prep school|preparatory|high school|academy)\b", s) \
       and not re.search(r"academy of art|revere academy", s):
        return "k12-school"
    # private / vocational bench-jewelry & gemology trade schools
    if re.search(r"\b(jewelry institute|jewelry school|school for jewelers|jewelers,? ltd|"
                 r"gemological|revere academy|new approach school|bench|gia\b|trade school|"
                 r"texas institute of jewelry|north bennet|workshop)\b", s):
        return "trade-school"
    # craft schools / centers (non-degree, immersive)
    if re.search(r"\b(penland|haystack|arrowmont|peters valley|pilchuck|touchstone|"
                 r"craft center|school of crafts|center for craft|center for the arts|"
                 r"center for the visual arts|center for visual art|school of arts? (and|&) crafts?|"
                 r"appalachian center|mendocino art center|art alliance|art workshop)\b", s) \
       and "college" not in s and "university" not in s:
        return "craft-school"
    # museum-affiliated art schools
    if re.search(r"\b(museum of fine arts|glassell|museum school|smithsonian)\b", s):
        return "museum-school"
    # art associations / leagues / guild schools
    if re.search(r"\b(art association|art league|arts league|art guild|guild|art alliance|art workshop)\b", s):
        return "art-association"
    # community / junior / technical colleges
    if re.search(r"\b(community college|junior college|technical college|technical institute|"
                 r"area technical|county college|city college|vocational)\b", s):
        return "community-college"
    # standalone art & design colleges (degree-granting, art-focused, not a university)
    if re.search(r"\b(school of art and design|institute of art|college of art|college of design|"
                 r"school of design|art institute|academy of art|maryland institute|"
                 r"rhode island school of design|risd|savannah college of art|scad|"
                 r"school of the art institute|center for creative studies|"
                 r"college for creative studies|kansas city art institute|"
                 r"cleveland institute|columbus college of art|moore college|"
                 r"massachusetts college of art|cooper union|parsons|pratt|otis|cranbrook|"
                 r"fashion institute|memphis college of art|minneapolis college of art|"
                 r"pacific northwest college|oregon college of art)\b", s):
        return "art-college"
    # universities / four-year colleges (the default for degree institutions)
    if re.search(r"\b(university|college|institute of technology|polytechnic|state\b|"
                 r"u\.? of |\bu[a-z]{1,3}\b)\b", s):
        return "university"
    return "unclassified"

# explicit overrides for names the keyword rules can't resolve cleanly
EXPLICIT = {
    "florida gulf coast art center": "craft-school",
    "institute of american indian arts": "art-college",   # IAIA: degree-granting
    "portland school of art": "art-college",               # now Maine College of Art
}
rows = cur.execute("SELECT id, name FROM programs").fetchall()
counts = {}
for pid, nm in rows:
    t = EXPLICIT.get((nm or "").lower().strip(), classify(nm))
    cur.execute("UPDATE programs SET school_type=? WHERE id=?", (t, pid))
    counts[t] = counts.get(t, 0) + 1
print("school_type counts:", dict(sorted(counts.items(), key=lambda x:-x[1])))

con.commit()
# show the non-university institutions for a human eyeball
print("\n--- non-university institutions (review) ---")
for t in ("trade-school","craft-school","museum-school","art-association","unclassified"):
    names = [r[0] for r in cur.execute("SELECT name FROM programs WHERE school_type=? ORDER BY name", (t,))]
    if names:
        print(f"\n[{t}] ({len(names)})")
        for x in names: print("   ", x)
con.close()
