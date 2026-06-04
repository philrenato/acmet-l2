#!/usr/bin/env python3
"""Generate the directory index + profile pages from acmet.db.

2026-05-30 rebuild:
  * builds out EVERY high-confidence, non-disputed person (not just 7)
  * bidirectional teacher<->student cross-links (click an instructor on a
    student's page -> their page; a teacher's page lists the students they
    taught) — Phil's request
  * institution-type labels (university / art-college / craft-school /
    trade-school / community-college / museum-school ...) from school_type
  * name wording driven by fc_change_kind (genuine change vs archive misspelling)

Each profile still pulls its narrative bio live from GitHub (wiki -> repo file
-> embedded fallback); the embedded fallback is the hand-written wiki bio when
one exists, otherwise the sourced fc_summary."""
import os, re, sqlite3, html, json

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
WIKI_DIR = os.path.join(SITE, "wiki")
os.makedirs(WIKI_DIR, exist_ok=True)
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); con.row_factory = sqlite3.Row

OWNER, REPO = "philrenato", "acmet-l2"

# curated pages keep their stable filenames (existing links + memory rely on these)
CURATED = {
    "crafts/metalsdirectorypage/s272.html": ("phil-renato.html",      "Phil-Renato"),
    "crafts/metalsdirectorypage/p82.html":  ("mary-lee-hu.html",      "Mary-Lee-Hu"),
    "crafts/metalsdirectorypage/p97.html":  ("stanley-lechtzin.html", "Stanley-Lechtzin"),
    "crafts/metalsdirectorypage/p88.html":  ("daniella-kerner.html",  "Daniella-Kerner"),
    "crafts/metalsdirectorypage/p170.html": ("vickie-sedman.html",    "Vickie-Sedman"),
    "gap/rebecca-strzelec":                 ("rebecca-strzelec.html", "Rebecca-Strzelec"),
    "gap/skip-hunter":                      ("skip-hunter.html",      "Skip-Hunter"),
}

TYPE_LABEL = {
    "university": "university art department", "art-college": "art &amp; design college",
    "community-college": "community / technical college", "craft-school": "craft school / center",
    "trade-school": "private jewelry / trade school", "museum-school": "museum art school",
    "art-association": "art association school", "k12-school": "secondary / day school",
    "unclassified": "",
}

def titlecase(n):
    n = re.sub(r"\s+", " ", (n or "").strip())
    cap = lambda w: "-".join(p.capitalize() for p in w.split("-"))
    return " ".join(cap(w) for w in n.split())

def clean_name(n):  # strip parentheticals like "Phil Renato (Phillip Renato)"
    return re.sub(r"\s*\(.*?\)\s*", "", n or "").strip()

# ---- name fields hold names and names only ----
# No honorifics or academic credentials in a name line or page title (they live
# on the page, in the role/bio), no departments "(sculpture)", no "? to ?", no
# trailing connectors the year-strip leaves behind ("Harlan Butt In"), no role
# tails ("Alan Revere, Director of the Academy"). Hedging happens on the page.
HONOR_RE = re.compile(r"^(?:dr|prof(?:essor)?|mr|mrs|ms)\.?\s+", re.I)
CRED_RE  = re.compile(r"[,\s]+(?:ph\.?\s?d|ed\.?d|m\.?f\.?a|b\.?f\.?a|m\.?a|m\.?s|b\.?a|b\.?s|j\.?d)\.?$", re.I)
TRAILJUNK_RE = re.compile(r"\s+(?:in|at|and|with|from|to|the|of|for|since|until|current|added|present)[\s,]*$", re.I)
def name_only(s):
    s = re.sub(r"\([^)]*\)?", " ", s or "")        # incl. an unclosed "(painting"
    s = re.sub(r"[?]", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" ,;:.&")
    prev = None
    while prev != s:
        prev = s
        s = HONOR_RE.sub("", s)
        s = CRED_RE.sub("", s).strip(" ,;:.")
    s = s.split(",")[0].strip()                    # "Name, Director of ..." -> "Name"
    prev = None
    while prev != s:
        prev = s
        s = TRAILJUNK_RE.sub("", s).strip(" ,;:.")
    return s

# a mention must LOOK like a person's name, or it doesn't get listed at all
ROLEJUNK_RE = re.compile(r"\b(visit\w*|artist|director|academ\w*|professor|prof|instructor|lecturer|faculty|staff|emeritus|emerita|chair|head|dean|coordinator|assistant|associate|guest|adjunct|various|unknown|department|studio|workshop|added|current|retired|deceased|worked|studied|under|formerly|school|college|university)\b", re.I)
NAME_PARTICLES = {"de","da","del","della","der","den","di","du","la","le","van","von","ten","ter","st","mac","mc","y","e"}
def plausible_name(s):
    if not s or any(ch.isdigit() for ch in s): return False
    words = s.split()
    if len(words) < 2 or len(words) > 5: return False
    if ROLEJUNK_RE.search(s): return False
    for w in words:
        wl = w.strip(".'’-")
        if wl and wl[0].islower() and wl.lower() not in NAME_PARTICLES: return False
    return True

def status_phrase(alive, job):
    # state what someone is/was, never emphasize what they aren't
    if alive == "no": return "Deceased"
    if alive == "likely-deceased": return ""        # don't assert a death we're unsure of
    if job == "retired-emeritus": return "Retired"
    if alive == "unknown": return ""
    return "Active"

def srcs(s):
    return [u.strip() for u in (s or "").split("|") if u.strip().startswith("http")]

def stint(status, years):
    # how a teaching stint reads on a chip: faculty appointment vs. a workshop vs. a past post
    y = (years or "").strip()
    if status == "workshop": return ("workshops " + y).strip() if y else "workshop"
    if status == "former":   return ("former " + y).strip()
    return y

def norm(s):  # name normalisation for cross-link resolution
    s = re.sub(r"\([^)]*\)", " ", (s or "").lower())
    s = re.sub(r"\b(dr|prof|professor|mr|mrs|ms|jr|sr|phd|mfa|bfa)\b\.?", " ", s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", s)).strip()

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", clean_name(s or "").lower()).strip("-")

# ---------------------------------------------------------------------------
# choose the build-out set: one row per distinct person, high confidence,
# not disputed. dedupe across the old/new archive trees (keep the checked row).
# ---------------------------------------------------------------------------
checked = [dict(r) for r in con.execute(
    "SELECT * FROM people WHERE fc_checked IS NOT NULL")]
by_name = {}
for r in checked:
    by_name.setdefault(r["name"], []).append(r)
# pick best row per name (most informative summary wins)
people = []
for nm, rows in by_name.items():
    rows.sort(key=lambda r: len(r["fc_summary"] or ""), reverse=True)
    people.append(rows[0])

def buildable(r):
    if r["slug"] in CURATED: return True
    if r["fc_verified"] == "disputed": return False
    if r["fc_confidence"] == "high": return True
    # additions brought current (gap / succession / editor): keep them discoverable
    # if they carry a source/link OR a verified current role + institution (a rotted
    # citation URL shouldn't erase a real, scan-verified faculty listing).
    if r["fc_verified"] in ("snag-gap-2026", "succession-scan", "phil-added") and (
            r["fc_current_link"] or r["fc_sources"] or (r["currently_at"] and r["fc_current_role"])):
        return True
    return False

build_rows = [r for r in people if buildable(r)]

# ---- assign filenames (curated stay fixed; rest auto, de-duped) ----
fname_of = {}     # slug -> filename
used = set(v[0] for v in CURATED.values())
for r in sorted(build_rows, key=lambda r: r["name"]):
    if r["slug"] in CURATED:
        fname_of[r["slug"]] = CURATED[r["slug"]][0]; continue
    disp = clean_name(r["fc_current_name"]) if (r["fc_name_changed"] == "yes" and r["fc_current_name"]) else r["name"]
    disp = name_only(disp) or disp        # filenames are name fields too — no dr-/phd in a URL
    base = slugify(disp) or slugify(r["name"]) or ("person-" + str(r["id"]))
    fn = base + ".html"; i = 2
    while fn in used:
        fn = f"{base}-{i}.html"; i += 1
    used.add(fn); fname_of[r["slug"]] = fn

# ---------------------------------------------------------------------------
# cross-link resolver: any name -> built person's filename
# ---------------------------------------------------------------------------
# index built people by normalised full name, by (last, first-initial), by last name
exact, bylastinit, bylast, lastcount = {}, {}, {}, {}
for r in build_rows:
    for cand in {norm(r["name"]), norm(clean_name(r["fc_current_name"] or ""))}:
        if not cand: continue
        exact.setdefault(cand, r["slug"])
        parts = cand.split()
        if len(parts) >= 2:
            bylastinit.setdefault((parts[-1], parts[0][0]), set()).add(r["slug"])
            bylast.setdefault(parts[-1], set()).add(r["slug"])
# known instructor spelling/nickname aliases -> canonical normalised name
ALIAS = {
    "arthur viertahler": "arthur vierthaler", "alvine pine": "alvin pine",
    "bob ebendorf": "robert ebendorf", "fredrich holschuh": "frederick holschuh",
    "dick hay": "richard hay", "bill macon": "william macon",
}
slug_by_name = {}
for r in build_rows: slug_by_name[r["slug"]] = r

def resolve_file(nm):
    k = norm(nm); k = ALIAS.get(k, k)
    if not k: return None
    if k in exact: return fname_of.get(exact[k])
    parts = k.split()
    if len(parts) >= 2:
        s = bylastinit.get((parts[-1], parts[0][0]))
        if s and len(s) == 1: return fname_of.get(next(iter(s)))
        s = bylast.get(parts[-1])
        if s and len(s) == 1: return fname_of.get(next(iter(s)))
    return None

# ---------------------------------------------------------------------------
# reverse student map: teacher filename -> [(student display, student file)]
# from education.instructor (split on / , & "and") resolved to a built person.
# ---------------------------------------------------------------------------
id2row = {r["id"]: r for r in checked}
name2builtrow = {}
for r in build_rows: name2builtrow[r["name"]] = r
students_of = {}   # teacher_slug -> set of (student_name, student_slug)
slug_of_id = {}
# map person id -> its build slug (dedup by name)
for r in build_rows:
    slug_of_id[r["id"]] = r["slug"]
namebuilt = {r["name"]: r for r in build_rows}

for e in con.execute("SELECT person_id, instructor FROM education WHERE instructor IS NOT NULL AND instructor!=''"):
    student = id2row.get(e["person_id"])
    if not student: continue
    # the student we link to is the built row for that name (if any)
    sb = namebuilt.get(student["name"])
    for part in re.split(r"[/,&]| and ", e["instructor"]):
        part = re.sub(r"\([^)]*\)", "", part).strip()
        if not part: continue
        k = norm(part); k = ALIAS.get(k, k)
        tslug = exact.get(k)
        if not tslug:
            ps = k.split()
            if len(ps) >= 2:
                cand = bylastinit.get((ps[-1], ps[0][0])) or bylast.get(ps[-1])
                if cand and len(cand) == 1: tslug = next(iter(cand))
        if tslug and sb and tslug != sb["slug"]:
            students_of.setdefault(tslug, set()).add((name_only(clean_name(sb["fc_current_name"])) if (sb["fc_name_changed"]=="yes" and sb["fc_current_name"]) else name_only(titlecase(sb["name"])), fname_of[sb["slug"]]))

# ---------------------------------------------------------------------------
# PROGRAMS: profile pages + person<->program cross-links
# ---------------------------------------------------------------------------
programs = [dict(r) for r in con.execute("SELECT * FROM programs WHERE fc_checked IS NOT NULL")]
# dedupe by name (old/new tree) keeping the richest row
prog_by_name = {}
for p in programs:
    prog_by_name.setdefault(p["name"], []).append(p)
programs = []
for nm, rows in prog_by_name.items():
    rows.sort(key=lambda r: len((r["fc_what_happened"] or "")) + len((r["fc_current_faculty"] or "")), reverse=True)
    programs.append(rows[0])

pfile_of = {}   # program slug -> filename
for p in sorted(programs, key=lambda p: p["name"]):
    base = slugify(p["name"]) or ("program-" + str(p["id"]))
    fn = base + ".html"; i = 2
    while fn in used:
        fn = f"{base}-{i}.html"; i += 1
    used.add(fn); pfile_of[p["slug"]] = fn

# program name resolver (for education.school + currently_at -> program page)
prog_exact, prog_list = {}, []
for p in programs:
    n = norm(p["name"])
    if n: prog_exact.setdefault(n, p["slug"]); prog_list.append((n, p["slug"]))
def resolve_prog_file(nm):
    n = norm(nm)
    if not n: return None
    if n in prog_exact: return pfile_of.get(prog_exact[n])
    # substring either way, require a reasonably specific match
    best = None
    for pn, slug in prog_list:
        if len(pn) >= 6 and (pn in n or n in pn):
            best = slug
            if pn == n: break
    return pfile_of.get(best) if best else None

prog_id2slug = {p["id"]: p["slug"] for p in programs}
prog_row = {p["slug"]: p for p in programs}
slug_of_pfile = {v: k for k, v in pfile_of.items()}   # program filename -> slug

# when a person's institution has a notable fate (closed, renamed/merged), say so
# inline WITH a link — a claim like "Siena Heights has closed" never floats unsourced;
# the program page it points at carries the story and the citations.
FATE_WORD = {"no": "closed", "merged-renamed": "renamed / merged"}
def inst_link(nm):
    """institution name -> link to its program page + (html, fate-word-or-None)."""
    if not nm: return "", None
    pf = resolve_prog_file(nm)
    if not pf: return html.escape(nm), None
    fate = FATE_WORD.get(((prog_row[slug_of_pfile[pf]]["fc_still_exists"] or "").strip()))
    out = f'<a class="instr-link" href="{pf}">{html.escape(nm)}</a>'
    if fate: out += f' <a class="fatetag" href="{pf}">{fate}</a>'
    return out, fate

# faculty per program + which programs a person taught at (from program_faculty)
# a deceased person never renders as CURRENT faculty, however the archived row
# reads ("X 1980 to present") — demote to former and drop the "to present"
dead_norms = {norm(r["name"]) for r in people if r["fc_alive"] == "no"}
prog_faculty = {}   # prog_slug -> list of (display, person_file_or_None, status, years)
taught_at = {}      # person_file -> list of (prog_name, prog_file, status, years)
for f in con.execute("SELECT program_id,name,person_url,status,years FROM program_faculty"):
    pslug = prog_id2slug.get(f["program_id"])
    if not pslug: continue
    raw = f["name"] or ""
    yrs = f["years"] or ""
    m = re.search(r"\b(1[89]\d\d|20\d\d).*$", raw)
    if m and not yrs: yrs = raw[m.start():].strip()
    cleannm = re.sub(r"\s+\b(1[89]\d\d|20\d\d).*$", "", raw).strip()
    status = f["status"] or "current"
    if status == "current" and norm(cleannm) in dead_norms:
        status = "former"
        y2 = re.sub(r"(?i)\s*to\s+present\s*$", "", yrs).strip()
        yrs = ("from " + y2) if re.fullmatch(r"1[89]\d\d|20\d\d", y2) else y2
    pf = resolve_file(cleannm)
    prog_faculty.setdefault(pslug, []).append((titlecase(name_only(cleannm)) or titlecase(cleannm), pf, status, yrs))
    if pf:
        taught_at.setdefault(pf, []).append((prog_row[pslug]["name"], pfile_of[pslug], status, yrs))

# alumni per program (people who studied there) + a person's studied-at programs
prog_alumni = {}    # prog_slug -> list of (display, person_file)
studied_at = {}     # person_id -> set(prog_slug)
for e in con.execute("SELECT person_id, school, degree FROM education WHERE school IS NOT NULL AND school!=''"):
    pf_slug = prog_exact.get(norm(e["school"]))
    if not pf_slug:
        # fuzzy
        n = norm(e["school"])
        for pn, slug in prog_list:
            if len(pn) >= 6 and (pn in n or n in pn): pf_slug = slug; break
    if not pf_slug: continue
    studied_at.setdefault(e["person_id"], set()).add(pf_slug)
    student = id2row.get(e["person_id"])
    if not student: continue
    sb = namebuilt.get(student["name"])
    disp = (clean_name(sb["fc_current_name"]) if (sb and sb["fc_name_changed"]=="yes" and sb["fc_current_name"])
            else titlecase(student["name"]))
    pf = fname_of.get(sb["slug"]) if sb else None
    prog_alumni.setdefault(pf_slug, []).append((disp, pf))

# dedupe the per-program lists
for d in (prog_faculty, prog_alumni):
    for k, v in d.items():
        seen=set(); out=[]
        for item in v:
            key=item[0].lower()
            if key not in seen: seen.add(key); out.append(item)
        d[k]=out

STATUS_PROG = {"yes":"Active","no":"Closed","merged-renamed":"Merged / renamed","unknown":""}

# ---------------------------------------------------------------------------
# page template
# ---------------------------------------------------------------------------
CSS = ""
for seed in ("phil-renato.html", "mary-lee-hu.html"):
    p = os.path.join(SITE, seed)
    if os.path.exists(p):
        CSS = open(p).read().split("<style>")[1].split("</style>")[0]; break
if not CSS:
    CSS = "body{font-family:-apple-system,sans-serif;max-width:720px;margin:0 auto;padding:40px}"

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Academic Metals Directory</title>
<style>{css}
  .back{{display:inline-block;margin-bottom:22px;font-size:13px;color:var(--soft);text-decoration:none}}
  .back:hover{{color:var(--ink)}}
  .newadd{{background:#f0efe7}}
  .typetag{{display:inline-block;font-size:11px;letter-spacing:.04em;color:var(--soft);
    border:1px solid #ddd9cd;border-radius:999px;padding:1px 9px;margin-left:6px;vertical-align:middle}}
  .fatetag{{display:inline-block;font-size:11px;letter-spacing:.04em;color:#8a4a2a;
    background:#f6ece3;border:1px solid #e2cfba;border-radius:999px;padding:1px 9px;
    margin-left:6px;vertical-align:middle;text-decoration:none;font-weight:600}}
  .fatetag:hover{{background:#f0e0cf}}
  .people-links a{{color:var(--good);text-decoration:none;font-weight:600}}
  .people-links a:hover{{text-decoration:underline}}
  .lineage-card h3{{margin-top:0}}
  .lineage-card .lbl{{display:block;margin:10px 0 3px}}
  .chip{{display:inline-block;margin:2px 5px 2px 0;padding:3px 9px;border-radius:8px;
    background:#f2f0e8;font-size:13px}}
  .chip a{{color:var(--ink);text-decoration:none}} .chip a:hover{{color:var(--good)}}
  .instr-link{{color:var(--good);text-decoration:none}} .instr-link:hover{{text-decoration:underline}}
</style></head><body><div class="wrap">
  <a class="back" href="./">← the directory</a>
  <p class="kicker">Academic Metals Directory · entry</p>
  <h1 id="name">{title}</h1>
  {former}
  <div class="role">{role}</div>
  <div class="checked">{checked}</div>
  <hr>
  {cards}
  {edu}
  {lineage}
  <hr>
  <div class="bio" id="bio">loading bio…</div>
  <p class="checked">bio source: <span id="bio-src"></span> · <a id="edit-link" href="#" target="_blank" rel="noopener">✎ edit this bio</a></p>
  <hr>
  <h3 style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--soft)">Sources</h3>
  <div class="sources" id="sources">{sources}</div>
  <p class="checked" style="margin-top:14px">{provenance}</p>
  <p class="foot">Structured facts come from <code>acmet.db</code>. The bio is pulled live from
  GitHub (<code>{wiki}</code>) so it stays editable. If GitHub can't be reached, a built-in copy shows.</p>
</div>
<script>
const WIKI={{owner:"{owner}",repo:"{repo}",page:"{wiki}"}};
const SOURCES=[
 {{url:`https://raw.githubusercontent.com/wiki/${{WIKI.owner}}/${{WIKI.repo}}/${{WIKI.page}}.md`,label:"live · github wiki",edit:`https://github.com/${{WIKI.owner}}/${{WIKI.repo}}/wiki/${{WIKI.page}}/_edit`}},
 {{url:`https://raw.githubusercontent.com/${{WIKI.owner}}/${{WIKI.repo}}/main/${{WIKI.page}}.md`,label:"live · github repo",edit:`https://github.com/${{WIKI.owner}}/${{WIKI.repo}}/edit/main/${{WIKI.page}}.md`}}
];
// no wiki page or repo file yet -> GitHub's create-file flow (auto-forks + opens a PR for non-collaborators)
const EDIT_FALLBACK=`https://github.com/${{WIKI.owner}}/${{WIKI.repo}}/new/main?filename=${{WIKI.page}}.md`;
const FALLBACK_MD={fallback};
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}}
function inl(s){{return esc(s).replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>').replace(/\\*\\*([^*]+)\\*\\*/g,'<b>$1</b>').replace(/(^|[^*])\\*([^*]+)\\*/g,'$1<em>$2</em>');}}
function md(t){{let h='',p=[];const f=()=>{{if(p.length){{const x=p.join(' ').trim();if(x)h+=(x.startsWith('*')&&x.endsWith('*')&&!x.includes('**'))?`<p class="note">${{inl(x.replace(/^\\*|\\*$/g,''))}}</p>`:`<p>${{inl(x)}}</p>`;p=[];}}}};
 for(const l of t.replace(/\\r/g,'').split('\\n')){{if(/^###\\s/.test(l)){{f();h+=`<h3>${{inl(l.slice(4))}}</h3>`;}}else if(/^##\\s/.test(l)){{f();h+=`<h2>${{inl(l.slice(3))}}</h2>`;}}else if(/^#\\s/.test(l)){{f();h+=`<h1>${{inl(l.slice(2))}}</h1>`;}}else if(/^---+\\s*$/.test(l)){{f();h+='<hr>';}}else if(/^\\s*$/.test(l)){{f();}}else p.push(l);}}
 f();return h;}}
function show(t,live,label,edit){{document.getElementById('bio').innerHTML=md(t);document.getElementById('bio-src').innerHTML=live?`<span class="badge live">${{label}}</span>`:`<span class="badge local">built-in copy (github unreachable)</span>`;document.getElementById('edit-link').href=edit||EDIT_FALLBACK;}}
(async()=>{{for(const s of SOURCES){{try{{const r=await fetch(s.url,{{cache:'no-store'}});if(r.ok){{show(await r.text(),true,s.label,s.edit);return;}}}}catch(e){{}}}}show(FALLBACK_MD,false,'',EDIT_FALLBACK);}})();
</script></body></html>"""

def kv(label, val):
    return f'<p class="kv"><span class="lbl">{html.escape(label)}</span><br>{val}</p>' if val else ""

def link_instructor(nm):
    """instructor name -> linked if a built page exists, else plain."""
    out = []
    for part in re.split(r"(\s*[/,&]\s*|\s+and\s+)", nm):
        if not part or re.fullmatch(r"\s*[/,&]\s*|\s+and\s+", part):
            out.append(html.escape(part)); continue
        f = resolve_file(part)
        if f:
            out.append(f'<a class="instr-link" href="{f}">{html.escape(name_only(part) or part.strip())}</a>')
        else:
            out.append(html.escape(part))
    return "".join(out)

def fallback_bio(r):
    wf = os.path.join(WIKI_DIR, fname_of[r["slug"]].replace(".html", "").title() + ".md")
    # curated hand-written bios
    if r["slug"] in CURATED:
        p = os.path.join(WIKI_DIR, CURATED[r["slug"]][1] + ".md")
        if os.path.exists(p): return open(p).read(), CURATED[r["slug"]][1]
    # otherwise synthesize from the sourced summary
    disp = name_only(clean_name(r["fc_current_name"])) if (r["fc_name_changed"]=="yes" and r["fc_current_name"]) else name_only(titlecase(r["name"]))
    wikiname = re.sub(r"\.html$", "", fname_of[r["slug"]])
    wikiname = "-".join(w.capitalize() for w in wikiname.split("-"))
    body = r["fc_summary"] or ""
    if not body:
        bits = [r["fc_current_role"], ("at " + r["currently_at"]) if r["currently_at"] else ""]
        body = "; ".join(b for b in bits if b)
    txt = f"# {disp}\n\n{body}\n\n*This entry is auto-drafted from the directory's fact-check notes. Edit to expand.*\n"
    return txt, wikiname

def build_profile(r):
    name = r["name"]; changed = (r["fc_name_changed"] == "yes")
    kind = r["fc_change_kind"]
    cur = name_only(clean_name(r["fc_current_name"])) if (changed and r["fc_current_name"]) else name_only(titlecase(name))
    title = cur
    # if the "change" leaves the displayed name identical, there's nothing to note
    if changed and norm(cur) == norm(titlecase(name)):
        changed = False
    if changed and kind == "spelling-correction":
        former = f'<div class="former">archived (misspelled) as {html.escape(titlecase(name))}</div>'
    elif changed and kind == "name-variant":
        former = f'<div class="former">also listed as {html.escape(titlecase(name))}</div>'
    elif changed:
        former = f'<div class="former">formerly {html.escape(titlecase(name))}</div>'
    else:
        former = ""
    role = html.escape(r["fc_current_role"] or "")
    checked = f'last checked {r["fc_checked"] or ""}'
    gap = (r["kind"] in ("person-gap-addition",))
    succ = (r["fc_verified"] == "succession-scan")
    sp = status_phrase(r["fc_alive"], r["fc_still_in_job"])
    link = r["fc_current_link"]
    dead = (r["fc_alive"] == "no")
    insthtml, instfate = inst_link(r["currently_at"] or "")
    now = (kv("Goes by", f'<b>{html.escape(cur)}</b>')
           # a deceased person doesn't hold a CURRENT role — label it as their last
           + kv("Last role" if dead else "Current role", html.escape(r["fc_current_role"] or ""))
           + (kv("Institution", insthtml) if instfate else "")
           + (kv("Status", f'<b>{html.escape(sp)}</b>' if dead else html.escape(sp)) if sp else "")
           + (kv("Link", f'<a href="{html.escape(link)}" target="_blank" rel="noopener">{html.escape(re.sub(r"^https?://","",link))}</a>') if link else ""))
    nowcard = f'<div class="card now"><h3>Now (checked 2026)</h3>{now}</div>'
    # provenance is a quiet breadcrumb at the BOTTOM, not a banner up top
    if r["fc_verified"] == "phil-added":
        provenance = "Added to the directory in 2026. Not in the original 2014 listing."
    elif succ:
        provenance = "Identified in the 2026 faculty-succession review. Not in the original 2014 listing."
    elif gap:
        provenance = "Surfaced in the 2026 program review. Not in the original 2014 listing."
    else:
        provenance = "From the original Tyler “Academic Metals Directory” (≈2014), brought current in 2026."
    if changed and kind == "name-change":
        provenance += " Name change confirmed against the sources below."
    if gap or succ:
        cards = f'<div style="margin:8px 0">{nowcard}</div>'
    else:
        arch = r["currently_at"] or ""
        thenline = f'<b>{html.escape(titlecase(name))}</b><br>' if changed else ""
        then = (kv("Listed as", f'{thenline}{inst_link(arch)[0]}' + (f' — since {r["since_year"]}' if r["since_year"] else ""))
                + kv("Born", html.escape(", ".join([x for x in [r["dob"], r["birthplace"]] if x]))))
        cards = (f'<div class="grid"><div class="card then"><h3>As archived (≈2014)</h3>{then}</div>{nowcard}</div>')
    # ---- training (with institution-type tag + linked instructors) ----
    edu_rows = con.execute("SELECT level,school,years,major,degree,instructor FROM education WHERE person_id=?", (r["id"],)).fetchall()
    edu = ""
    if edu_rows:
        trs = ""
        for e in edu_rows:
            stype = con.execute("SELECT school_type FROM programs WHERE lower(name)=lower(?) LIMIT 1", (e["school"] or "",)).fetchone()
            tag = f'<span class="typetag">{TYPE_LABEL[stype["school_type"]]}</span>' if (stype and stype["school_type"] in TYPE_LABEL and TYPE_LABEL[stype["school_type"]]) else ""
            instr = (' · instructor: ' + link_instructor(e["instructor"])) if e["instructor"] else ""
            sch = html.escape(e["school"] or "")
            pf = resolve_prog_file(e["school"] or "")
            schhtml = f'<a class="instr-link" href="{pf}">{sch}</a>' if pf else sch
            trs += (f'<tr><td>{html.escape(e["level"] or "")}</td><td><b>{schhtml}</b>{tag}'
                    f'{(" · "+html.escape(e["years"])) if e["years"] else ""}<br>'
                    f'<span class="lbl">{html.escape(e["degree"] or "")}{instr}</span></td></tr>')
        edu = f'<div class="card" style="margin-top:18px"><h3>Training</h3><table class="edu"><tbody>{trs}</tbody></table></div>'
    # ---- lineage: students taught + institutions taught at (cross-links) ----
    kids = sorted(students_of.get(r["slug"], []))
    myfile = fname_of[r["slug"]]
    taught = taught_at.get(myfile, [])
    # dedupe taught-at by program, prefer a 'former'/years-bearing label
    seenp = {}
    for pn, pf2, st, yrs in taught:
        seenp.setdefault(pf2, (pn, st, yrs))
    lineage = ""
    if kids or seenp:
        parts = []
        if seenp:
            def tchip(pf2, pn, st, yrs):
                suf = stint(st, yrs)
                tail = f' <span class="lbl" style="display:inline">· {html.escape(suf)}</span>' if suf else ""
                return f'<span class="chip"><a href="{pf2}">{html.escape(pn)}</a>{tail}</span>'
            tchips = "".join(tchip(pf2, pn, st, yrs) for pf2, (pn, st, yrs) in sorted(seenp.items(), key=lambda x: x[1][0]))
            parts.append(f'<span class="lbl">Taught at</span><div class="people-links">{tchips}</div>')
        if kids:
            chips = "".join(f'<span class="chip"><a href="{f}">{html.escape(n)}</a></span>' for n, f in kids)
            parts.append(f'<span class="lbl">Taught (in this directory)</span><div class="people-links">{chips}</div>')
        lineage = (f'<div class="card lineage-card" style="margin-top:18px"><h3>Lineage</h3>'
                   + "".join(parts)
                   + f'<p class="checked" style="margin-top:8px">Students drawn from who lists this person as an instructor; '
                     f'institutions from faculty records. See the full <a href="lineage.html">lineage timeline →</a></p></div>')
    sources = "".join(f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(u)}</a>' for u in srcs(r["fc_sources"]))
    fb, wikiname = fallback_bio(r)
    fallback = json.dumps(fb)
    out = PAGE.format(title=html.escape(title), css=CSS, former=former, role=role, checked=html.escape(checked),
                      cards=cards, edu=edu, lineage=lineage, sources=sources, provenance=html.escape(provenance),
                      wiki=wikiname, owner=OWNER, repo=REPO, fallback=fallback)
    open(os.path.join(SITE, fname_of[r["slug"]]), "w").write(out)
    return title

# ---------------------------------------------------------------------------
# program profile page
# ---------------------------------------------------------------------------
PROG_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Academic Metals Directory</title>
<style>{css}
  .back{{display:inline-block;margin-bottom:22px;font-size:13px;color:var(--soft);text-decoration:none}}
  .back:hover{{color:var(--ink)}}
  .typetag{{display:inline-block;font-size:11px;letter-spacing:.04em;color:var(--soft);
    border:1px solid #ddd9cd;border-radius:999px;padding:1px 9px;margin-left:6px;vertical-align:middle}}
  .fatetag{{display:inline-block;font-size:11px;letter-spacing:.04em;color:#8a4a2a;
    background:#f6ece3;border:1px solid #e2cfba;border-radius:999px;padding:1px 9px;
    margin-left:6px;vertical-align:middle;text-decoration:none;font-weight:600}}
  .fatetag:hover{{background:#f0e0cf}}
  .people-links a{{color:var(--good);text-decoration:none;font-weight:600}}
  .chip{{display:inline-block;margin:2px 5px 2px 0;padding:3px 9px;border-radius:8px;background:#f2f0e8;font-size:13px}}
  .chip a{{color:var(--ink);text-decoration:none}} .chip a:hover{{color:var(--good)}}
  .chip.plain{{color:var(--soft)}}
</style></head><body><div class="wrap">
  <a class="back" href="./">← the directory</a>
  <p class="kicker">Academic Metals Directory · program</p>
  <h1>{title}</h1>
  <div class="role">{typelabel}{statusline}</div>
  <div class="checked">{checked}</div>
  <hr>
  {cards}
  {faculty}
  {alumni}
  <hr>
  <h3 style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--soft)">Sources</h3>
  <div class="sources">{sources}</div>
  <p class="checked" style="margin-top:14px">{provenance}</p>
  <p class="foot">A program in the Academic Metals Directory. People shown are linked where they
  have an entry. <a href="map/">See it on the map →</a></p>
</div></body></html>"""

def build_program(p):
    title = titlecase(re.sub(r"\s+", " ", p["name"]))
    stype = p["school_type"] or ""
    typelabel = TYPE_LABEL.get(stype, "") or ""
    stat = STATUS_PROG.get(p["fc_still_exists"], "")
    statusline = (f' · {stat}' if stat else "")
    link = p["fc_current_link"] or p["source_url"]
    started = p["program_started"] or ""
    curname = p["fc_current_name"] if (p["fc_still_exists"]=="merged-renamed" and p["fc_current_name"] and norm(p["fc_current_name"])!=norm(p["name"])) else ""
    now = (kv("Status", html.escape(stat)) if stat else "")
    now += (kv("Now known as", html.escape(curname)) if curname else "")
    now += (kv("What happened", html.escape(p["fc_what_happened"])) if p["fc_what_happened"] else "")
    now += (kv("Link", f'<a href="{html.escape(link)}" target="_blank" rel="noopener">{html.escape(re.sub(r"^https?://","",link))}</a>') if link else "")
    then = (kv("Program began", html.escape(started)) if started else "") + (kv("Degrees", html.escape(p["degrees"])) if p["degrees"] else "")
    if then:
        cards = f'<div class="grid"><div class="card then"><h3>As archived</h3>{then}</div><div class="card now"><h3>Now (checked 2026)</h3>{now}</div></div>'
    else:
        cards = f'<div class="card now"><h3>Now (checked 2026)</h3>{now}</div>'
    # faculty
    facs = prog_faculty.get(p["slug"], [])
    faculty = ""
    if facs:
        def fac_chip(t):
            disp, pf, status, yrs = t
            inner = f'<a href="{pf}">{html.escape(disp)}</a>' if pf else f'<span class="plain">{html.escape(disp)}</span>'
            extra = stint(status, yrs) if status != "current" else (yrs or "")
            return f'<span class="chip">{inner}{(" · "+html.escape(extra)) if extra else ""}</span>'
        cur_f = [t for t in facs if t[2] not in ("former", "workshop")]
        old_f = [t for t in facs if t[2] == "former"]
        ws_f  = [t for t in facs if t[2] == "workshop"]
        blocks = ""
        if cur_f: blocks += f'<span class="lbl">Faculty</span><div class="people-links">{"".join(fac_chip(t) for t in sorted(cur_f))}</div>'
        if old_f: blocks += f'<span class="lbl" style="margin-top:8px">Formerly taught here</span><div class="people-links">{"".join(fac_chip(t) for t in sorted(old_f))}</div>'
        if ws_f:  blocks += f'<span class="lbl" style="margin-top:8px">Workshop instructors (selected)</span><div class="people-links">{"".join(fac_chip(t) for t in sorted(ws_f))}</div>'
        faculty = f'<div class="card lineage-card" style="margin-top:18px"><h3>People</h3>{blocks}</div>'
    # alumni (trained here)
    al = prog_alumni.get(p["slug"], [])
    al = [a for a in al if a[1]]   # only those with pages
    alumni = ""
    if al:
        chips = "".join(f'<span class="chip"><a href="{f}">{html.escape(n)}</a></span>' for n, f in sorted(al)[:60])
        more = f' <span class="checked">(+{len(al)-60} more)</span>' if len(al) > 60 else ""
        alumni = f'<div class="card lineage-card" style="margin-top:18px"><h3>Trained here</h3><div class="people-links">{chips}</div>{more}</div>'
    checked = f'last checked {p["fc_checked"] or ""}'
    sources = "".join(f'<a href="{html.escape(u)}" target="_blank" rel="noopener">{html.escape(u)}</a>' for u in srcs(p["fc_sources"]))
    tl = f'<span class="typetag">{typelabel}</span>' if typelabel else ""
    prov = ("Added in the 2026 program review; not in the original 2014 directory."
            if p["fc_verified"] in ("snag-gap-2026", "phil-added")
            else "From the original Tyler “Academic Metals Directory” (≈2014), brought current in 2026.")
    out = PROG_PAGE.format(title=html.escape(title), css=CSS, typelabel=tl, statusline=statusline,
                           checked=html.escape(checked), cards=cards, faculty=faculty, alumni=alumni,
                           sources=sources, provenance=html.escape(prov))
    open(os.path.join(SITE, pfile_of[p["slug"]]), "w").write(out)

# ---- build all profiles ----
built = {}   # name -> (display, filename)
for r in sorted(build_rows, key=lambda r: r["name"]):
    disp = build_profile(r)
    built[r["name"]] = (disp, fname_of[r["slug"]])
print(f"built {len(built)} profiles")

# ---- build all program pages ----
for p in programs:
    build_program(p)
print(f"built {len(programs)} program pages")

# ---------------------------------------------------------------------------
# index: two sets — degree-granting programs & their faculty on top, everything
# else beneath. A person is "degree" if any teaching affiliation (current job or
# a program_faculty link) is at a degree-granting institution.
# ---------------------------------------------------------------------------
DG_TYPES = {"university", "art-college", "community-college"}
pfile_type = {pfile_of[p["slug"]]: (p["school_type"] or "") for p in programs}
row_by_name = {r["name"]: r for r in people}

def bucket_of(name):
    r = row_by_name.get(name)
    fname = built[name][1] if name in built else None
    if r is None: return "degree"
    if fname:
        for (_pn, pf2, _st, _yrs) in taught_at.get(fname, []):
            if pfile_type.get(pf2) in DG_TYPES: return "degree"
    pf = resolve_prog_file(r["currently_at"] or "")
    if pf and pfile_type.get(pf):
        return "degree" if pfile_type.get(pf) in DG_TYPES else "other"
    # no resolvable institution: original-directory people were academic; later
    # gap/succession/editor additions without a degree-granting tie go to "other"
    if r["fc_verified"] in ("snag-gap-2026", "phil-added") or r["kind"] == "person-gap-addition":
        return "other"
    return "degree"

all_names = {r["name"] for r in people if r["kind"] != "person-gap-addition"} | set(built.keys())
deg, oth = [], []
for n in all_names:
    disp, fn = built[n] if n in built else (titlecase(name_only(n)) or titlecase(n), None)
    (deg if bucket_of(n) == "degree" else oth).append((disp, fn))

# ---- mention-only names: anyone listed on a page (an instructor on a Training
# card, a faculty name on a program page) gets a search hit even without an
# entry of their own — the result points at the page that lists them.
# suppress mentions of anyone already here — including under a corrected name
# (the archive often repeats its own misspelling, so the misspelled form matches)
known_norms = {norm(n) for n in all_names} | {norm(clean_name(r["fc_current_name"])) for r in people if r["fc_current_name"]}
# first+last pairs too, so "Gary S Griffin" doesn't shadow the listed Gary Griffin
known_pairs = set()
for kn in list(known_norms):
    w = kn.split()
    if len(w) >= 2: known_pairs.add((w[0], w[-1]))
row_by_id = {r["id"]: r for r in people}
mention_hosts = {}   # display name -> set of (host display, host file)
def mention_add(nm, host_disp, host_file):
    nm = name_only(nm)
    if not plausible_name(nm): return                # names and names only
    if norm(nm) in known_norms or resolve_file(nm): return  # already in the index
    w = norm(nm).split()
    if len(w) >= 2 and (w[0], w[-1]) in known_pairs: return  # middle-initial variant of a listed name
    mention_hosts.setdefault(titlecase(nm), set()).add((host_disp, host_file))
for e in con.execute("SELECT person_id, instructor FROM education WHERE instructor IS NOT NULL AND instructor!=''"):
    pr = row_by_id.get(e["person_id"])
    if not pr or pr["slug"] not in fname_of: continue   # host page must exist
    hd = built.get(pr["name"], (titlecase(pr["name"]),))[0]
    for part in re.split(r"\s*[/,&]\s*|\s+and\s+", e["instructor"]):
        mention_add(part, hd, fname_of[pr["slug"]])
for pslug, flist in prog_faculty.items():
    pname = titlecase(re.sub(r"\s+", " ", prog_row[pslug]["name"]))
    for (dispnm, pf, _st, _yrs) in flist:
        if not pf: mention_add(dispnm, pname, pfile_of[pslug])
mn_html = "\n".join(
    f'<a class="nm mn" href="{hf}">{html.escape(nm)} <span class="mhost">· listed under {html.escape(hd)}</span></a>'
    for nm, hosts in sorted(mention_hosts.items(),
                            key=lambda kv: ((kv[0].split()[-1].lower() if kv[0].split() else kv[0].lower()), kv[0].lower()))
    for hd, hf in [sorted(hosts)[0]])
n_mn = len(mention_hosts)

def render_items(lst):
    lst.sort(key=lambda e: ((e[0].split()[-1].lower() if e[0].split() else e[0].lower()), e[0].lower()))
    return "\n".join(
        f'<a class="on nm" href="{fn}">{html.escape(d)}</a>' if fn else f'<span class="off nm">{html.escape(d)}</span>'
        for d, fn in lst)
deg_html, oth_html = render_items(deg), render_items(oth)
n_deg, n_oth = len(deg), len(oth)

# programs, same split (by the institution's own type)
pdeg, poth = [], []
for p in programs:
    item = (titlecase(re.sub(r"\s+", " ", p["name"])), pfile_of[p["slug"]])
    (pdeg if (p["school_type"] in DG_TYPES) else poth).append(item)
pdeg_html, poth_html = render_items(pdeg), render_items(poth)
n_pdeg, n_poth = len(pdeg), len(poth)

total, nbuilt = n_deg + n_oth, len(built)
INDEX = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Academic Metals Directory</title>
<style>{CSS}
  .names{{column-width:220px;column-gap:32px;margin-top:8px}}
  .names a, .names span{{display:block;padding:4px 0;font-size:15px;break-inside:avoid}}
  .names .off{{color:#b9b6ac}}
  .names a.on{{color:var(--ink);text-decoration:none;font-weight:600}}
  .names a.on::after{{content:" ·";color:var(--good)}}
  .names a.on:hover{{color:var(--good)}}
  .lead{{font-size:17px;color:var(--ink)}}
  .maplink{{display:inline-block;margin-top:16px;padding:9px 16px;border-radius:10px;
    background:#181014;color:#ffd27a;text-decoration:none;font-size:14px;font-weight:600;
    border:1px solid #3a2a1a;box-shadow:0 0 22px rgba(255,150,60,.18)}}
  .maplink:hover{{box-shadow:0 0 30px rgba(255,150,60,.34);color:#ffe2a8}}
  html,body{{overflow-x:hidden}}
  .maplink{{white-space:normal}}
  .search{{width:100%;box-sizing:border-box;padding:12px 16px;font-size:16px;
    border:1px solid #d8d4c8;border-radius:12px;margin:18px 0 4px;background:#fff;color:var(--ink)}}
  .search:focus{{outline:none;border-color:var(--good);box-shadow:0 0 0 3px rgba(120,160,90,.15)}}
  .qcount{{font-size:12px;color:var(--soft);min-height:16px;margin-bottom:6px}}
  .vizhint{{font-size:12px;color:var(--soft);margin-top:8px}}
  @media (max-width:520px){{ .maplink{{display:block;margin-right:0}} }}
  .tabs{{display:flex;gap:8px;margin:14px 0 2px}}
  .tab{{padding:7px 16px;border-radius:999px;border:1px solid #d8d4c8;background:#fff;color:var(--soft);
    font-size:14px;font-weight:600;cursor:pointer}}
  .tab[aria-selected="true"]{{background:#181014;color:#ffd27a;border-color:#3a2a1a}}
  .setlabel{{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--soft);
    margin:22px 0 2px;font-weight:600}}
  .setlabel .setn{{color:#b9b6ac;font-weight:400;letter-spacing:0}}
  .panel[hidden]{{display:none}}
  .names a.mn{{color:var(--soft);text-decoration:none;font-weight:400}}
  .names a.mn:hover{{color:var(--good)}}
  .names a.mn::after{{content:""}}
  .mhost{{font-size:12px;color:#b9b6ac}}
</style></head><body><div class="wrap">
  <p class="kicker">recovered + being updated</p>
  <h1>Academic Metals Directory</h1>
  <p class="lead">US jewelry, metals, and CAD-CAM teaching programs and the people who taught them —
  the old Tyler School of Art directory, brought current. {total} names across {len(programs)} programs;
  the {nbuilt} in <b>bold</b> have a page. Degree-granting programs and their faculty come first;
  craft schools, studios, and workshops follow.</p>
  <a class="maplink" href="map/">🔥 see them on the map →</a>
  <a class="maplink" href="lineage.html" style="background:#0f1418;color:#9ad0ff;border-color:#1a2a3a;box-shadow:0 0 22px rgba(60,150,255,.16)">↳ the lineage &amp; timeline →</a>
  <div class="vizhint">The map and lineage are pinch-to-zoom on a phone, and roomiest on a desktop browser.</div>
  <hr>
  <div class="tabs" role="tablist">
    <button class="tab" id="tab-people" role="tab" aria-selected="true" onclick="showTab('people')">People</button>
    <button class="tab" id="tab-programs" role="tab" aria-selected="false" onclick="showTab('programs')">Programs</button>
  </div>
  <input class="search" id="q" type="search" placeholder="Search people…" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="Search">
  <div class="qcount" id="qcount"></div>

  <div class="panel" id="panel-people" data-noun="people">
    <div class="setlabel" data-set>Degree-granting programs &amp; their faculty <span class="setn">{n_deg}</span></div>
    <div class="names" data-names>
{deg_html}
    </div>
    <div class="setlabel" data-set>Craft schools, studios, trade schools &amp; workshops <span class="setn">{n_oth}</span></div>
    <div class="names" data-names>
{oth_html}
    </div>
    <div class="setlabel" data-set data-mention>Listed on another page <span class="setn">{n_mn}</span></div>
    <div class="names" data-names data-mention>
{mn_html}
    </div>
  </div>

  <div class="panel" id="panel-programs" data-noun="programs" hidden>
    <div class="setlabel" data-set>Degree-granting institutions <span class="setn">{n_pdeg}</span></div>
    <div class="names" data-names>
{pdeg_html}
    </div>
    <div class="setlabel" data-set>Craft schools, studios, trade schools &amp; workshops <span class="setn">{n_poth}</span></div>
    <div class="names" data-names>
{poth_html}
    </div>
  </div>

  <p class="qcount" id="noresults" style="display:none">Nothing matches. Try a last name or a school.</p>
  <p class="foot">Each built page sets the archived 2014 entry beside today's facts, with the teachers,
  students, and programs that connect it to the rest of the directory.</p>
  <p class="foot">Names in grey don't have a page yet — held back pending a clearer source
  (the archived listing is the trusted baseline; anything newer is checked against a citation). Some are
  low-confidence or disputed on purpose, left visible rather than guessed at.</p>
  <p class="foot" style="margin-top:20px;border-top:1px solid #e6e3d8;padding-top:16px">
  <b>Mirror &amp; extend this.</b> The whole project is open source — the database (<code>acmet.db</code>),
  the build scripts, and the recovered archive all live in one repo:
  <a href="https://github.com/philrenato/acmet-l2">github.com/philrenato/acmet-l2</a>.
  Clone it, open the folder with an LLM (Claude Code or similar), and pick up where this left off —
  add people, verify claims, fix a record, or rescope it past metals. Start with
  <a href="https://github.com/philrenato/acmet-l2/blob/main/MIRROR.md">MIRROR.md</a>.
  Nobody needs permission to be in a directory; living people get a say before anything new goes public.</p>
</div>
<script>
(function(){{
  var q=document.getElementById('q'), nr=document.getElementById('noresults'), c=document.getElementById('qcount');
  var panels={{people:document.getElementById('panel-people'), programs:document.getElementById('panel-programs')}};
  var cur='people';
  function active(){{ return panels[cur]; }}
  function run(){{
    var v=q.value.trim().toLowerCase(), n=0, p=active();
    var sets=p.querySelectorAll('[data-names]'), labels=p.querySelectorAll('[data-set]');
    for(var s=0;s<sets.length;s++){{
      var items=sets[s].children, shown=0;
      var isMention=sets[s].hasAttribute('data-mention'); // mention-only names appear only in search results
      for(var i=0;i<items.length;i++){{
        var hit = v ? items[i].textContent.toLowerCase().indexOf(v)>=0 : !isMention;
        items[i].style.display = hit ? '' : 'none'; if(hit){{shown++; n++;}}
      }}
      // hide a set's label + list when nothing in it matches
      if(labels[s]) labels[s].style.display = shown ? '' : 'none';
      sets[s].style.display = shown ? '' : 'none';
    }}
    c.textContent = v ? (n+' '+(n===1?(cur==='people'?'name':'program'):cur==='people'?'names':'programs')) : '';
    nr.style.display = (v && n===0) ? '' : 'none';
  }}
  window.showTab=function(t){{
    cur=t;
    panels.people.hidden = t!=='people'; panels.programs.hidden = t!=='programs';
    document.getElementById('tab-people').setAttribute('aria-selected', t==='people');
    document.getElementById('tab-programs').setAttribute('aria-selected', t==='programs');
    q.placeholder = t==='people' ? 'Search people…' : 'Search programs…';
    run();
  }};
  q.addEventListener('input', run);
}})();
</script>
</body></html>"""
open(os.path.join(SITE, "index.html"), "w").write(INDEX)
print(f"index: {total} names, {nbuilt} built out")
# coverage of cross-links
print(f"teachers with student lists: {len(students_of)}; total student links: {sum(len(v) for v in students_of.values())}")
