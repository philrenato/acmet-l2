# acmet-l2 — handoff (state as of 2026-06-04)

The recovered Tyler "Academic Metals Directory," brought current and published.
This is the "what's actually done and what's loose" doc; `README.md` is the
front door, `MIRROR.md` is the clone-and-extend guide for the next person.

**Live:** https://renato.design/acmet-l2/  ·  **Repo:** github.com/philrenato/acmet-l2 (the whole project — site + source)

## status: working, published, link-audited.

### ⚠ STANDING RULE — check inbound FIRST (Phil, 2026-06-04)
At the start of any session on this project (and before any deploy), check for
inbound contributions — nothing notifies us:
```
git clone -q https://github.com/philrenato/acmet-l2.wiki.git /tmp/acmet-wiki && git -C /tmp/acmet-wiki log --oneline | head
gh api repos/philrenato/acmet-l2/issues --jq '.[] | "\(.number) \(.title) (\(.user.login))"'
gh pr list -R philrenato/acmet-l2
```
Inbound claims follow the house rule (verify against fetched sources before
publishing). If a wiki bio was edited, pull it into `site/wiki/` so the next
deploy doesn't fight it.

### ⚠ WRITING RULE — no process exposition in copy (Phil, 2026-06-04)
Public pages never narrate research rules or effort ("belongs in directory",
"per the no-invent rule", "confirmed via…", "couldn't be documented"). State
the fact, or say "Unknown." and stop. The audit trail lives in `factcheck` +
RESEARCH_LOG, not in the copy.

### the shape of it
- **One database** (`acmet.db`) → three faces: the **directory** (people + program
  pages), the **map** (`/map/`), the **lineage** (`/lineage.html`). Fix a record,
  rebuild, all three update.
- **847 fact-checked people / 463 fact-checked programs** in the DB (1062 / 663 raw
  rows — the old/new archive trees produced shadow rows; builders filter
  `fc_checked IS NOT NULL`); **782 person pages + 463 program pages** built and live
  (disputed / low-confidence people held back).

### what got done (chronological-ish)
1. **Recovered** the dead site from the Wayback Machine → `archive/` (4,492 text pages,
   frozen). Tool: `archive/wayback_pull.py`.
2. **Parsed** → `acmet.db` (people / education / programs / program_faculty / factcheck).
   `build_database.py`. ⚠ rerunning DROPS the DB — re-extract THEN reload.
3. **Fact-checked** the archived roster (deaths / name-changes / current job / program
   fate), multi-agent, sourced + adversarially verified. `factcheck_workflow.js`.
4. **Faculty-succession** re-scan of surviving programs → +218 current faculty.
   `succession_workflow.js` → `load_succession.py`.
5. **Coherence audit** (`audit_coherence.py`): added `people.fc_change_kind`
   (genuine name-change vs name-variant vs archive spelling-fix — 8 of the 20 "name
   changes" were just OCR fixes) and `programs.school_type` (university / art-college /
   community-college / craft-school / trade-school / museum-school / art-association /
   k12). Cleaned 387 orphaned `education` rows (build_database left education pointing at
   non-existent person_ids; they collided with new inserts via `lastrowid`).
6. **Re-verification pass** (`updates_2026_05_30.py`, `scrub_death_speculation.py`):
   **PURGED "likely-deceased"** entirely — Phil's rule: never assert/speculate a death
   without a good source (scrubbed speculative death language from 57 bios). Fixed two
   wrong-person sources (Vierthaler→von Neumann; Sipantzi→"Arnold Hassoldt"). Resolved
   disputes (Fred Woell deceased 2015 w/ obituary; Kamal Baum no longer COD faculty).
7. **SNAG gap pass** — pulled SNAG's full community-links list via its WordPress REST API
   (`/wp-json/wp/v2/community_links?link_type=613` schools / `615` craft-centers — bypasses
   the JS pagination that defeats a naive fetch; 282 schools + 208 craft-centers), diffed
   vs the DB → 339 candidates → one verify-agent each (`gap_workflow_v2.js` → `load_gaps.py`)
   → **+266 programs + ~396 current faculty** (73 rejected as out-of-scope: gemology, welding,
   suppliers).
8. **Named additions** (`people_records_workflow.js`/`2` → `load_people_records.py`): Nashef,
   Skelcey, Gayk, Starrett, Elaver, Flood, DeMonte, Beverly Seley, Robyn Kane Haberkorn,
   David Huang + Appalachian State, Grand Rapids CC. Beeler→Dundee, Scotland; Saracino retired;
   Melis Agabigum corrected to Western Michigan (primary) with PenArt as a workshop; Jill
   Baker Gower reconciled to College of DuPage.
9. **Cross-linking** (the headline feature): bidirectional teacher↔student (from
   `education.instructor`) AND person↔program (taught-at / studied-at / faculty / alumni,
   from `program_faculty` + `education.school`). Every instructor name and school name on a
   page is a link where the target has an entry.
10. **UX pass**: directory index now has **People / Programs tabs**, a **two-set split**
    (degree-granting programs & their faculty on top, craft schools / studios / trade /
    workshops beneath), and **live search** over the active tab. Process language ("added
    during gap analysis") moved off page tops to a quiet **provenance breadcrumb at the
    bottom**; real provisos (sources, consent, low-confidence held back) kept in the footer.
    **Map + lineage are pinch-zoom + drag-pan on phone** (d3.zoom + `touch-action:none`),
    with a "best on desktop" note. `program_faculty.status='workshop'` renders workshop
    stints distinctly ("Workshop instructors (selected)" — kept partial; Penland rosters
    would balloon).
11. **Open-sourced** the whole project: the published repo holds the built site at the root
    AND `source/` (acmet.db, all scripts, the archive, the docs) + `MIRROR.md` + one-command
    `source/deploy.sh`. Mirror invitation in the index footer.
12. **Link audit** (`fix_links` pass): checked every displayed external URL (2,629 distinct).
    Dropped **68 confirmed-dead (404/410)** links — per Phil, "if a link doesn't show info
    about the person/program (not just the school), drop it" (so dead deep links are dropped,
    NOT rooted to a school homepage). Tyler-archive URLs (`temple.edu/crafts/...`) →
    **Wayback captures** (they resolve to exactly the recovered entry). Kept personal artist
    sites, art-department pages, specific deep links, and bot-blocked/slow ones (not
    high-confidence dead). **0 broken internal links; cross-link resolution verified.**

### the build + deploy pipeline (one DB → three faces → live)
```
acmet.db ─build_graph.py─▶ data/acmet-graph.json ─▶ build_map.py  (site/map/)
                                                  └▶ build_lineage.py (site/lineage.html)
acmet.db ─build_site.py──▶ site/ (index + person pages + program pages)
source/deploy.sh  ─▶ rebuilds all, syncs site→repo root + source→/source, commits, pushes
```
Run `ACMET_REPO=/tmp/acmet-deploy ./deploy.sh "message"` to publish. Verify live with a
cache-busted `curl` (GitHub Pages lags 1–2 min); the page is JS for tabs/search, so a quick
phone tap-through is worth it.

### ⚠️ the deploy trap (don't relearn this)
`renato.design/acmet-l2/` is served by the **separate `philrenato/acmet-l2` PROJECT repo**,
NOT by `philrenato-web/acmet-l2/`. A project repo named `acmet-l2` publishes to the same
`/acmet-l2/` path and *shadows* a same-named folder in the user-site repo. The local
`~/Documents/claude/acmet-l2` is NOT a git checkout. `deploy.sh` clones/uses the project repo
correctly. Confirm the target with `gh api repos/philrenato/acmet-l2/pages`.

### data model (the fc_* layer is the work)
- `people` — identity + `fc_alive` (yes/no/unknown — never "likely-deceased"),
  `fc_current_role`, `fc_still_in_job`, `fc_current_link`, `fc_sources` (` | `-joined),
  `fc_confidence`, `fc_verified`, `fc_change_kind`, `fc_summary`, `fc_checked`.
- `programs` — `fc_still_exists`, `fc_current_name`, `school_type`, `fc_what_happened`,
  `fc_current_link`, `fc_succession_status`, sources.
- `education` — person_id, level, school, years, degree, **instructor** (drives lineage).
- `program_faculty` — program_id, name, **status** (current/former/workshop), **years**.
- `factcheck` — the dated audit log (every re-verification appends here).

### the renato.design wiring
- Grid card `id="grid-acmetl"` (name "acmetl", tool-tier — grid-only, no featured rotation,
  no per-app accent) in `philrenato-web/index.html`.
- `philrenato-web/data/apps.json` entry slug `acmet-l2` → feeds the polyhedral launcher.
- sitemap entry at 0.8. (Separate repo `philrenato/philrenato.github.io`.)

### 2026-06-04 session — the Rowan pass + editorial-rules day
The directory got its **first inbound contributor email** (Donna Sweigart, Rowan). House
rule held: nothing published on an email alone — research agents re-verified every claim
against fetched URLs, then an adversarial agent re-checked all of it pre-publish.

**Records:**
- **Donna Sweigart** added (Professor, head of Rowan's Metals/Jewelry/CAD area; Tyler MFA
  2004 → cross-links to the home program; UTPA→UTRGV→Rowan). Rank conflict carried as an
  on-page footnote (research profile/bio/sig say Professor; dept page + 2023 archived
  roster + her own CV say Associate Professor and Chair).
- **Maureen Duffy** built out. Her old `ccca.rowan.edu` source URLs are DEAD (301 to an
  unrelated college) — replaced. A **Feb-2023 Wayback capture of Rowan's faculty roster**
  (`/web/20230203221908/https://ccca.rowan.edu/departments/art/facultystaff/`) settles
  ranks for the whole department — the Wayback-the-dead-roster move is reusable.
- **John Van Haren** added (1930–2010; founded EMU's Jewelry Program 1970; 40 yrs EMU,
  15 as dept head — obituary-sourced). Archive typo "John Vanharen" on Wittersheim's card
  fixed; teacher↔student cross-linked. Wittersheim listed Van Haren (not Skip Hunter)
  because they were close — a person's own stated teacher wins.
- **Skip Hunter's lineage** completed: Phil Renato, **Tara Nahabetian** (Buffalo State,
  official bio confirms EMU BFA), **Eric Okon** (EMU; official title "Part Time Lecturer,
  3D Media" footnoted, published as Lecturer). **Juan Carlos Caballero-Perez's education
  was FABRICATED by a scan agent** (EMU/Skip + UW/Mary Lee Hu — both false); RIT's own
  directory says "BFA, MFA, RIT" — replaced. Lesson: a plausible big-name education row
  from a workflow agent is exactly the thing to re-verify.

**Editorial rules (Phil, now policy — see also the memory files):**
- Never "full professor" (only "promoted to full in YEAR" sentences).
- Rank comes from the school's own current/recent page (Wayback counts); people say
  "professor" colloquially. No school evidence → state the ROLE ("teaches jewelry…"),
  which is never wrong the way a mis-stated rank is. Never characterize teaching load.
- Conflicting evidence → publish best-evidenced value + footnote what each source says.
- **Name fields hold names only** — no Dr./PhD/MFA in name lines, page titles, or URLs;
  no departments, date fragments, role tails, or stray words. `name_only()` +
  `plausible_name()` in build_site.py clean every display site AND filenames (11 pages
  renamed; redirect stubs left at the old URLs).
- Lineage inference: X at school Y while Z was the only/primary teacher = "X studied
  with Z" (dates must be right).

**Presentation/engine (all in build_site.py):**
- Deceased people never read as employed: "Last role" label, bold **Deceased**, and
  ~199 archived "…to present" program-roster rows demote to *former* at build time.
- Institution fates carry links: a `closed` / `renamed / merged` tag (`.fatetag`) on
  institution names, pointing at the program page that holds the story + citations.
- **Mention search**: names that appear only on someone else's page (Training-card
  instructors, program rosters) get index search results ("listed under …") — junk
  filtered, misspelled/middle-initial variants of listed people suppressed (77 live).
- "✎ edit this bio" fixed for all pages: no wiki page/repo file → GitHub's create-file
  flow (`/new/main?filename=…`), which auto-forks + PRs for non-collaborators. (The
  GitHub wiki itself STILL doesn't exist — needs one page made in the browser UI once.)

**Update scripts this session:** `updates_2026_06_04_rowan.py` + direct SQL (logged in
RESEARCH_LOG.md). DB now ~849 people; 781 person pages + 463 program pages live.
Four deploys, latest `c71082b`; deploy.sh worked as designed (clear stale
/tmp/acmet-deploy if commit fails oddly).

### 2026-06-04 (later) — full-project audit + Mark Herndon
Phil asked for a top-to-bottom interrogation (facts, grammar, structure, the
how-we-know / how-to-fix / mirror story, and a human-parseable map + timeline).
Four parallel audit agents (docs, site content, map/lineage, deployed state) +
fixes:

**Facts fixed (DB):** Arline Fisch died the day before her **93rd** birthday —
age **92**, not 93 (SNAG remembrance; CHANGES.md's "94th" also fixed); two
`education.years` "200 to 2002" → "2000 to 2002"; Siena Heights source URLs
swapped to `http://` (their HTTPS cert is broken, content live). Rebecca
Strzelec's "University of Michigan" attribution was investigated and is
CORRECT (Penn State Altoona 2002–2023 → Michigan Stamps since ~2023).

**Docs reconciled:** README/FUTURE/GAPS/SUCCESSION no longer claim done work as
future (succession + gap passes, "before it goes public"); name-change count
corrected everywhere to **6 genuine** (`fc_change_kind='name-change'`; the 20
were discrepancies); CHANGES.md got a superseded-snapshot banner (its
"likely deceased" language was purged from live data); HANDOFF numbers above
reconciled; MIRROR's sample query now uses a populated column.

**Engine (build_site.py):** program names render verbatim from the DB — no
more titlecase mangling ("College Of Dupage", "T.t.u."); deceased-roster
demotion now matches name VARIANTS via the resolver (7 pages read "X to
present" on dead people — fixed); meta description + OG tags on the index; an
index footer block "How we know, and how to fix us" (sources, ✎ edit flow,
issues, removal policy); a "Site last rebuilt DATE" stamp; `site/sitemap.xml`
(every page); REPO_README.md → repo-root README (deploy.sh copies it).
⚠ deploy.sh build order now **site FIRST, then graph/map/lineage** — the graph
existence-checks `site/*.html` for profile links, so a brand-new person's page
must exist before the graph builds.

**Map + lineage (Phil: "default timeline zone 1960–present"):** dates inferred
from education/faculty years (1084 undated → 1003 honestly undated — a
current-year fallback that walled 564 nodes at 2026 was tried and REMOVED);
inferred-year nodes draw dashed/hollow + disclosed in the legend; lineage
defaults to the **1960→present window** (label threshold scales with the fit
zoom — a hardcoded `curK>1.9` in `relabel()` was the mush); find-a-person
search (undated people searchable too — panel opens, no dot); `?focus=<slug>`
deep links on both faces; person pages link `lineage.html?focus=…`, program
pages link both faces focused; profile links in the lineage went **7 → ~1,219**
(the stale BUILT list died; build_graph existence-checks pages, name-changed
people via fc_current_name); genuine name-changes display their CURRENT name in
the graph; map disclosed state-centroid dots (221 of 365, dashed/hollow) +
"open program page →" in tooltips + glow/arc legend; provenance footers on both.

**Mark Herndon added** (person 1065, `gap/mark-herndon`) — editor tip,
re-verified: IAIA's own event page ("The Stories We Carry") lists "faculty
'05–'15" (Wayback-confirmed; live page bot-blocked) → former faculty 2005–2015;
runs Herndon Forge, Santa Fe, with designer Naomi Herndon (his site); UNT MFA
2001–04 + Corcoran BFA 1993–97 (LinkedIn-supported, noted as such); studied
with **Harlan Butt** (lineage-inference rule + Phil's statement — flagged
"inferred" in factcheck). No tribal affiliation stated — IAIA tags him faculty
only. Cross-linked: Butt ↔ Herndon, IAIA roster, UNT alumni.
`updates_2026_06_04_herndon.py`; 4 factcheck audit rows.

### 2026-06-04 (third pass) — fabricated-education purge + disputed cleanup
- ⚠⚠ **The education-fabrication audit ran: 67 of 90 workflow-added
  instructor-bearing education rows were FABRICATED** (systematic across the
  succession-scan cohort — invented mid-century educations under marquee
  teacher names, impossible dates). 82 rows deleted, 59 real cited rows
  inserted (spot-checked), ~48 false lineage edges dropped from the graph.
  RULE going forward: never load workflow-generated education rows without a
  per-row source. `updates_2026_06_04_audit2.py` + RESEARCH_LOG.
- **Disputed/low re-verification (24 people):** 3 resolved + 7 improved
  (sourced, promoted to medium, `fc_verified='reverified-2026-06-04'`,
  buildable() extended → 8 new pages, 790 total); 14 honestly unfindable left
  held back; 4 wrong-person sources caught + dropped (Nacke, van Duinwyk,
  Duncan, Sholtis).
- Rowan adjuncts re-attempted (403 + empty headless render + no recent
  Wayback) — still excluded, logged unverifiable in factcheck.

### 2026-06-04 (fourth pass) — city geocoding complete
All 319 imprecise programs resolved to campus cities (318/319; agents,
59 web-verified). **27 wrong-state dots corrected** (Rowan-in-PA, Purdue-in-TX,
Ghost-Ranch-in-GA class errors — centroids were hiding real mistakes).
**Map now 462 city / 1 state / 0 unplaced** (was 144/221/98); 19 non-US
schools disclosed in the legend (Albers-USA can't draw them).
`data/geocode_cities.json` = exact-name overlay read by build_graph
(find_latlng step 0 + find_state); wins over fragment matching.

### 2026-06-04 (fifth pass) — one search, three faces
Roadmap item done. (1) **Index search matches more than names**: every entry
carries `data-kw` — people match on their schools, instructors, institution,
and former name ("carrizzi" finds Phil Renato; "skip hunter" finds his
students); programs match on campus city/state + current name ("glassboro"
finds Rowan). (2) **The map got a find box** (top-left, lineage-style):
searches the shared manifest — programs fly to their dot; a person flies to
the dot where they taught ("at <program>" shown in the suggestion); no-dot
entries fall through to their directory page. (3) The lineage already had its
box. Mechanism: build_site emits `data/search.json` (1,253 entries; person →
mapslug via taught_at) + `data-kw` attrs; build_map embeds it (build order
site-first matters here too). `focusProgram(slug)` refactored out of the
deep-link so search + ?focus= share one path.

## loose threads / next moves (full roadmap in FUTURE.md)
- **Donna Sweigart's "3 additional adjunct faculty"** at Rowan — unnamed, faculty
  directory is JS-rendered + bot-blocked (re-tried 2026-06-04); excluded. If she
  replies with names, verify + add.
- **Okon/Nahabetian studied-with-Skip links** rest on Phil's editor knowledge + the
  era inference (documented rule); fine, but a fetched page naming Skip would harden them.
- **Living-person consent** — it's public now; corrections welcome via GitHub. If anyone asks
  to be removed/edited, that's authoritative.
- **Bot-blocked / slow links** (205 blocked + ~69 timeouts) were left as-is — they're live in a
  browser but a deeper pass could confirm or replace them.
- **Faculty without a live citation** — a handful of scan-verified faculty have a page but no
  working source link (their URL rotted); buildable keeps them via verified role+institution.
  A future pass could re-source them.
- **Disputed / low-confidence rows** still greyed (no page), held for a human pass.
- **Department-page links** — ~8 programs link to an art-department homepage rather than the
  metals/jewelry program page specifically; fine, but tighten if better URLs surface.
- **Rescope beyond metals** → all art/design/crafts (same model; per-discipline seeds like
  NCECA / GAS / Furniture Society). The SNAG-REST gap method generalizes.

## the keeper insight
For a people-directory, the highest-value updates are the ones a flat scan can't see —
**name changes** (Carrizzi→Renato) and **faculty succession** (who replaced whom; which
programs quietly lost the discipline). And a link is only worth showing if it actually shows
the person or program — a dead link or a bare school homepage is worse than none.
