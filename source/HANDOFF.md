# acmet-l2 — handoff (state as of 2026-06-04)

The recovered Tyler "Academic Metals Directory," brought current and published.
This is the "what's actually done and what's loose" doc; `README.md` is the
front door, `MIRROR.md` is the clone-and-extend guide for the next person.

**Live:** https://renato.design/acmet-l2/  ·  **Repo:** github.com/philrenato/acmet-l2 (the whole project — site + source)

## status: working, published, link-audited.

### the shape of it
- **One database** (`acmet.db`) → three faces: the **directory** (people + program
  pages), the **map** (`/map/`), the **lineage** (`/lineage.html`). Fix a record,
  rebuild, all three update.
- **847 people / 465 programs** in the DB; **779 person pages + 463 program pages**
  built and live. Distinct, deduped (the old/new archive trees produced shadow rows;
  builders filter `fc_checked IS NOT NULL`).

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

## loose threads / next moves (full roadmap in FUTURE.md)
- **Donna Sweigart's "3 additional adjunct faculty"** at Rowan — unnamed, faculty
  directory is JS-rendered; excluded. If she replies with names, verify + add.
- **Okon/Nahabetian studied-with-Skip links** rest on Phil's editor knowledge + the
  era inference (documented rule); fine, but a fetched page naming Skip would harden them.
- **Other scan-fabricated education rows?** Caballero-Perez was caught only because Phil
  knew. A targeted audit (education rows added by workflows vs. a source check) is a
  good next sweep.
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
