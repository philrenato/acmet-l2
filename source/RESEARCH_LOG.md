# Academic Metals Directory — Fact-Check Research Log

Project: **acmet-l2** — update the recovered Tyler M/J/C-C "Academic Metals
Directory" (offline; last live captures 2014–2019). For each person/program in
the archive: still in the job? still alive? name changed? current links? what
happened to the program / who replaced them?

Method: every claim carries a **source URL**, a **confidence** level, and a
**date-checked**. Nothing is asserted without a citation. Findings are logged
here (narrative, auditable) and mirrored into `acmet.db` → `factcheck` table.

Initial batch date-checked **2026-05-29**; later passes are dated in their own
section headers below.

---

## Batch 1 — marquee names (proof of method)

### Phil Carrizzi  → **Phillip Renato**  (archive: metalsdirectorypage/s272.html)
- **Name changed: YES.** Now goes by **Phillip Renato** ("formerly Carrizzi").
- **Alive / active: yes.**
- **Current job:** Professor at Kendall College of Art and Design (KCAD), Ferris
  State University; **founding chair of the Allesee Metals/Jewelry Design
  program** (now organized under Product Design at KCAD).
- **Archive said:** "Currently teaching at Kendall College of Art and Design –
  Assistant Professor, Chair Jewelry/Metals since 2002; MFA University of
  Washington." → Education matches; role advanced Asst Prof → Professor;
  program named/endowed as "Allesee."
- Confidence: **high** (official institutional page states the former name).
- Sources:
  - https://www.ferris.edu/redirects/kcad/programs/faculty/renato-phillip.html
    (KCAD faculty profile — "Phillip Renato (formerly Carrizzi)")
  - https://kcad.ferris.edu/news/metals-and-jewelry-design-program-chair-students-featured-in-jewelry-artist-magazine.html

### Mary Lee Hu  (archive: metalsdirectorypage/p82.html; bio b82.html)
- **Alive: yes** (b. 1943, Lakewood, Ohio). Name unchanged.
- **Current job:** **Retired — Professor Emeritus, University of Washington
  (retired 2006).** Archive said "Currently teaching at University of Washington
  since 1980" → now emerita.
- Honors since: ACC College of Fellows (1996), Twining Humber Lifetime
  Achievement (2008).
- Confidence: **high** (Wikipedia, "Living people"; explicit 2006 retirement).
- Sources:
  - https://en.wikipedia.org/wiki/Mary_Lee_Hu
  - https://artisttrust.org/artists/mary-lee-hu/

### Stanley Lechtzin  (the directory's own curator — "send corrections to Stanley Lechtzin, Tyler School of Art")
- **Alive: yes** (b. 1936, Detroit). Name unchanged.
- **Current job:** **Retired — Professor Emeritus, Tyler School of Art, Temple
  University.** Founded Tyler's Jewelry/Metals program in **1962**; **led it
  until his retirement in 2018.** Pioneer of electroforming + CAD-CAM in metals
  (the "C-C" in M/J/C-C).
- **Program succession:** Tyler announced a "**new vision for Tyler
  Metals/Jewelry/CAD-CAM**" in Oct 2018 as Lechtzin retired (program continues).
  → Successor/new leadership to be confirmed in the program fact-check.
- Honors: SNAG Lifetime Achievement (2009); ACC College of Fellows (1992);
  Temple Great Teacher Award (1989).
- Confidence: **high** for status; succession detail pending.
- Sources:
  - https://en.wikipedia.org/wiki/Stanley_Lechtzin
  - https://tyler.temple.edu/faculty/stanley-lechtzin
  - https://news.temple.edu/news/2018-10-23/new-vision-tyler-metalsjewelrycad-cam
  - https://snagmetalsmith.org/2009/06/2009-snag-lifetime-achievement-award-stanley-lechtzin/

---

## Program-level notes seeded from Batch 1
- **Tyler M/J/C-C (Temple)** — still exists; leadership transition 2018 after
  Lechtzin. (the home program of this whole directory.)
- **Kendall College of Art and Design (Ferris State)** — Metals/Jewelry still
  exists as the **Allesee Metals & Jewelry Design** program; now grouped under
  Product Design. Chair: Phillip Renato.
- **University of Washington** — metals program existed; Hu emerita 2006. Status
  of the current UW metals/jewelry offering to be checked in the program pass.

---

## Open method notes
- "Living people" on Wikipedia is a reliable *alive* signal but not proof of
  current employment — pair with the institution's own faculty page where one
  exists.
- Many directory entries are **historical figures** (DOB 1910s–1920s) who are
  near-certainly deceased; those get a "deceased (per dates / obituary)" check,
  not a "still in the job" check.
- Name changes (Carrizzi→Renato) are the highest-value, easily-missed updates;
  flag every one prominently.

---

## Full run — 217 people + 202 programs (multi-agent workflow, 2026-05-29/30)

634 agents · 4,856 web lookups · per-claim sourced · risky claims independently
re-verified by a second skeptic agent. Loaded into `acmet.db` (`fc_*` columns +
`factcheck` table); notable items in `CHANGES.md`.

**People (217):** alive 74 · deceased 68 (+16 likely\*) · unknown 59 ·
retired-emeritus 109 · moved 60 · still-in-archived-job 13.
Confidence: high 152 / medium 41 / low 24. Verify: confirmed 85 / disputed 17 /
not-needed 115.
\* The "likely-deceased" category was later **purged entirely** (2026-05-30
re-verification pass): no death is asserted or implied without a good source.
These 16 were reclassified "unknown" and speculative language scrubbed from bios.

**20 name discrepancies found** — the later coherence audit split these into
**6 genuine name changes** (`fc_change_kind='name-change'`) plus name variants
and archive spelling fixes. E.g.:
- Phil Carrizzi → **Phil Renato** · Lynda Watson-Abbott → **Lynda Watson** ·
  Pamela E. Lins → **Pam Lins** · Sharon Church → **Sharon Church McNabb** ·
  Merry Renk → **Merry Renk-Curtis** · Mary Ann Scherr (née Weckman) ·
  Kathleen Malec Kamal → **Kathleen Kamal Baum** · Jeff Georgantes → T Jeffrey
  Georgantes · Barbara Nilausen-K → **Balpreet Kaur**.
- Several were directory **typos** corrected against authority: Antonio Cirono→
  **Cirino**, Ruth Pennington→**Penington**, Harold O'Conner→**O'Connor**.

**Deaths newly documented with obituaries** include very recent ones the old
directory could never have had — Arline Fisch (Aug 2024), Imogene Gieling (Dec
2024, age 101), Fred Fenster (2024), Joe Reyes Apodaca (2024), Chris Ramsay (Jan
2026), Bob Mitchell (Jan 2025) — plus the field's historical figures (Bertoia,
Loloma, Brent Kington, John Paul Miller, Kenneth Bates, etc.).

**Still active in the same post (13):** incl. Thomas P. Muir (BGSU), Myra
Mimlitsch-Gray (SUNY New Paltz, Head of Metal), Keith Lewis (Central Washington),
Susan Hamlet (UMass Dartmouth), Dale Wedig (Northern Michigan), Phil Renato (Kendall).

**Programs (202):** still-exists 89 · **merged/renamed 64** · **closed 43** ·
unknown 6. High confidence 145. Over half changed status or vanished — e.g.
Memphis College of Art (whole school closed), Northern Arizona U (jewelry BFA
closed), Kendall (metals → concentration within Product Design), Oregon School of
Arts & Crafts (defunct).

**Data hygiene:** rows with `fc_verified='disputed'` (17) or `fc_confidence='low'`
(24) are surfaced for human review, not treated as settled. A few internal
contradictions (e.g. a "deceased" + "still teaching" combo) are intentionally
left visible rather than silently resolved.

---

## 2026-06-04 — Rowan University pass (first inbound contributor email)

Donna Sweigart (Rowan University) emailed the directory with her program's
degrees and faculty — the first real-world correction to arrive by email.
House rule applied: **nothing published on the email alone**; two research
agents re-verified every claim against fetched, live URLs.

- **Donna Sweigart added** (person 1063): Professor of Art & Design, head of
  the Metals/Jewelry/CAD area, Chair of the Department of Art. BFA Beaver
  College/Arcadia 1996; **MFA Tyler School of Art 2004** (a Tyler alum —
  cross-links into the directory's home program). Before Rowan: UT Pan
  American 2008–14 (MFA director 2010–12) → UT Rio Grande Valley 2015–19;
  earlier Univ. of Washington (2006). Rank carries an evidence footnote
  (research profile + her own bio say Professor; the dept faculty page still
  says Associate Professor).
- **Maureen Duffy filled out** (person 488, was a bare succession-scan stub):
  3/4-time Professor of Jewelry and Metalsmithing at Rowan; BFA Moore College
  2005, MFA SUNY New Paltz 2007; ten years a Philadelphia production jeweler;
  prior teaching Tyler, Towson, Moore, Millersville, New Paltz; Fleisher Art
  Memorial; Peters Valley/Touchstone workshops. Her ccca.rowan.edu bio URL is
  **dead** (301s to an unrelated college page) — replaced with live sources.
- **Rowan program (51)** updated: Jewelry & Metals is a named studio area of
  the BFA in Art (rowan.edu BFA page, verbatim); the area is officially the
  **Metals/Jewelry/CAD area** — that page label, not the email, is the citation
  for the CAD claim. Faculty now linked both ways.
- **Excluded:** the email's "3 additional adjunct faculty" — unnamed, and
  Rowan's faculty directory is JS-rendered (no fetchable public page).
- **House style ruling (Phil):** never write "full professor" — someone holds
  a sub-professor rank (assistant/associate) or they are a Professor; "full"
  may appear only in a promoted-to-full-in-year sentence. Scrubbed the one
  violation (Alvin A. Pine); Anne Mondro's "promoted to full Professor May 21,
  2026" is the allowed form. When rank/program-name evidence conflicts,
  publish the best-evidenced value and footnote the conflict.
- **Edit capability fixed:** profiles with no wiki page or repo bio file used
  to point "✎ edit this bio" at a 404; the fallback now opens GitHub's
  create-file flow (auto-fork + PR for non-collaborators), so every one of the
  781 built profiles is publicly editable.

### Same-day follow-ups (2026-06-04, Phil-driven)

- **Maureen Duffy rank corrected by archive evidence**: a Feb 2023 Wayback
  capture of Rowan's official art-department roster lists "Maureen Duffy,
  Instructor" (and corroborates "Donna Sweigart, Associate Professor and
  Chair"). Her record now reads "Teaches Jewelry and Metalsmithing" — role,
  not rank — with the evidence in a footnote. New house rules: never
  characterize teaching load (¾-time etc. — it changes); "professor" is often
  colloquial for the role, so rank comes only from the school's own
  current-or-recent page, and absent that we say what the person *does*.
- **John Van Haren added** (1930–2010): Professor of Art at Eastern Michigan
  University for forty years, **founder of the EMU Jewelry Program (1970)**,
  Head of the Art Department for fifteen years (obituary + independent
  corroboration). The archive misspelled him "John Vanharen" on John
  Wittersheim's card — corrected; teacher and student now cross-link.
- **Deceased ≠ employed, sweep**: deceased people no longer render with a
  "Current role" (label flips to **Last role**, status **Deceased** bolded);
  ~199 archived "…to present" faculty rows for deceased people now demote to
  *former* on program pages at build time ("former from 1980"); Oklahoma
  State's current-faculty text dropped the late Chris Ramsay.
- **Institution fates carry links**: when a person's institution closed or
  was renamed/merged, the card now flags it inline (a small "closed" tag)
  linking to the program page, which holds the closure story and citations —
  e.g. Wittersheim → Siena Heights University (closing at the end of 2025-26).
- **Mention search**: anyone listed on a page — an instructor on a Training
  card, a name on a program roster — now yields a search result even without
  an entry of their own ("listed under …", pointing at the hosting page).
  122 such names became findable.

### Round 2 (2026-06-04, editor corrections — Phil)

- **Juan Carlos Caballero-Perez education was fabricated** (a scan agent had
  him BFA Eastern Michigan under Skip Hunter + MFA U-Washington under Mary Lee
  Hu — neither true). RIT's own directory says "BFA, MFA, Rochester Institute
  of Technology"; rows replaced, false student-of links dissolved.
- **Skip Hunter's real teaching lineage filled in**: Tara J. Nahabetian
  (Associate Professor & Metals/Jewelry program coordinator, SUNY Buffalo
  State — official bio confirms BFA EMU, MFA Kent State) and Eric Okon (BFA +
  MFA EMU; teaches metalsmithing/jewelry there — EMU's pages list him as Part
  Time Lecturer, 3D Media; published as Lecturer with the official title
  footnoted, per the no-load-characterization rule), joining Phil Renato.
- Removed an editorializing line from Phil's bio.

### Round 3 (2026-06-04, name-field hygiene)

- **Name fields hold names and names only** (Phil's rule): no honorifics or
  academic credentials in name lines/page titles (Dr. Samanthessa R. Jacob,
  PhD → Samanthessa R. Jacob — degrees live on the page), no departments
  "(sculpture)", no "? to ?", no role tails ("…, Director of the Academy"),
  no stray connectors ("Harlan Butt In"). `name_only()` now cleans every
  display site: page titles, index entries, lineage chips, program rosters,
  Training-card instructor links.
- **Mentions must look like names**: partial names with only a title
  ("Professor Zicari") and narrative fragments ("worked with…") are pulled
  entirely; misspelled/variant near-names are suppressed when they match a
  listed person — including under corrected spellings and middle-initial
  variants ("Gary S Griffin" ≡ Gary Griffin). Mention set: 122 → 77, all
  plausible names.
- **Lineage evidence rule (Phil)**: X attending school Y while Z was the
  only/primary teacher there is sufficient to record "X studied with Z,"
  dates permitting — with respect for a person's own stated teacher
  (Wittersheim named Van Haren, not Hunter, and that stands).
- Pre-publish adversarial re-check run over every person added/updated today.

**Pre-publish adversarial verdicts** (every person added/updated 2026-06-04):
Duffy VERIFIED · Van Haren VERIFIED (obituary re-fetched) · Nahabetian
VERIFIED · Okon VERIFIED (archived EMU pages re-fetched) · Caballero-Perez
VERIFIED (RIT directory re-fetched) · Sweigart facts VERIFIED via her CV;
the standing rank conflict (Professor vs Associate Professor and Chair) is
carried in her footnote, now including the CV.

---

## 2026-06-04 (later) — full-project audit + Mark Herndon

Four parallel audit agents swept the docs, the built site, the map/lineage,
and the deployed repo. Marquee corrections, each re-verified against a fetch:

- **Arline Fisch's age at death corrected: 92, not 93.** She was born
  August 21, 1931 and died August 20, 2024 — the day before her 93rd
  birthday. SNAG's phrasing ("the day before her 93rd birthday") is the trap
  that produced the off-by-one; JCK's "94th" is its own arithmetic slip. The
  death itself is confirmed by SNAG, Wikipedia, SDSU, and AJF.
  https://snagmetalsmith.org/2024/08/in-remembrance-arline-fisch/
- **Rebecca Strzelec / "University of Michigan" — investigated, CORRECT.**
  An audit flagged it as a likely error (she's the famous Penn State Altoona
  professor); the DB had the full story all along: Penn State Altoona
  2002–2023, then Associate Dean for Academic Programs and Professor at
  Michigan's Stamps School since ~2023 (stamps.umich.edu). A good reminder
  that "I know where this person teaches" is exactly the claim to re-check.
- **Siena Heights "Reflections" URLs** (Wittersheim, Van Haren sources): the
  site's HTTPS certificate is broken but plain http serves the content —
  swapped scheme rather than dropping a live source.
- Two `education.years` rows read "200 to 2002" → "2000 to 2002".
- Doc-wide: the "20 name changes" figure is now stated honestly everywhere —
  20 name *discrepancies*, of which **6 are genuine changes**
  (`fc_change_kind='name-change'`); the rest are variants and archive typos.

### Mark Herndon (editor tip → verified → added, person 1065)

Phil's tip: taught at IAIA, now herndonforge.com, studied with Harlan,
LinkedIn screenshot for education. Verification:
- **IAIA faculty 2005–2015 — VERIFIED by the institution.** IAIA's "The
  Stories We Carry" event page lists "Mark Herndon, faculty '05–'15" (live
  page bot-blocked; text confirmed via the 2024-05-26 Wayback capture).
  Discipline (jewelry/metals) supported by his LinkedIn headline + an IAIA
  Chronicle piece — published as the role, no rank.
- **Herndon Forge, Santa Fe — his own site** (with his wife, designer Naomi
  Herndon). Work spans Southwestern jewelry, damascus steel, vessels.
- **UNT MFA 2001–04, Corcoran BFA (Sculpture) 1993–97 — LinkedIn-supported
  only**; no institutional page corroborates the years. Logged as such.
- **"Studied with Harlan Butt" — INFERRED** (UNT metals MFA inside Butt's
  long tenure) + the editor's direct statement; no fetched page says it.
  Logged "inferred" in factcheck; a page naming Butt would harden it.
- **No tribal affiliation stated or implied** — IAIA's artist list tags
  Native artists "(Tribe) 'year"; Herndon is tagged only "faculty '05–'15".
Cross-links: Harlan Butt ↔ Herndon (teacher/student), IAIA roster (former,
2005–2015), UNT alumni. Script: `updates_2026_06_04_herndon.py`.

---

## 2026-06-04 (third pass) — THE FABRICATED-EDUCATION PURGE + disputed-row cleanup

Phil: "Do everything you have to do/can do." Two audits he'd queued ran in full.

### Education fabrication audit — Caballero-Perez was the tip of the iceberg

Every workflow-added education row carrying a named instructor was verified
against fetched sources (44 people, 90 rows). Verdict: **67 rows FABRICATED,
15 suspect-unsupported, 4 plausible inferences, 4 confirmed.** The
succession-scan agent (2026-05-30) systematically attached invented
mid-century educations under marquee teacher names — Fisch, Ebendorf, Carlyle
Smith, Alvin Pine, Lechtzin, Mary Lee Hu, Fenster — to contemporary faculty.
The tell: impossible dates (Annika Pettersson, b. 1981, "Cleveland Institute
of Art 1936–1940"; Jaydan Moore, b. ~1984, "Emporia State '63").

Action taken: **82 rows deleted, 59 real rows inserted** from each person's
own bio or official directory (every replacement cited; three spot-checked
live before applying — Modena/Academy of Art, Ganch/VCU, Moore/own site).
Suspect rows with no source at all were deleted, not kept: a claim with no
source doesn't ship. ~48 false teacher→student lineage edges left the graph.
Per-person corrections logged in `factcheck`. Lesson for the method docs:
**never load workflow-generated education rows without a per-row source** —
plausible big-name lineage is exactly what scan agents invent.

### Disputed / low-confidence re-verification (24 people)

3 RESOLVED + 7 IMPROVED with real sources (TWU's own mace page for Bud Green;
a 1912 Penn Museum bulletin for Karl Nacke; CCA's library pages for Martin
Streich; VCU alumni material for Nancy Kunkle Thompson; metalcyberspace for
van Duinwyk; CSU/studio trail for Nilda Getty; a 2021 Chisholm Trail show for
Hollis Howard). 14 honestly UNFINDABLE — left held back, attempts logged.
Four wrong-person sources caught adversarially and dropped: Nacke (a German
porcelain artist), van Duinwyk (legal directories), Duncan (a pastor's
obituary), Sholtis (a horn professor). No death asserted anywhere; one
"likely alive" clamped to unknown — the bio states the dated activity instead.
`build_site.py` now surfaces sourced medium-confidence re-verifications
(`fc_verified='reverified-2026-06-04'`), so 8 formerly-greyed names got pages.

Script: `updates_2026_06_04_audit2.py`. Also: Rowan's "3 additional adjunct
faculty" re-attempted (curl 403, headless render empty, no recent Wayback) —
still excluded, logged unverifiable.

---

## 2026-06-04 (fourth pass) — city geocoding: every program placed

Three research agents resolved all 319 imprecisely-placed institutions (221
state-centroid + 98 entirely unplaced) to their actual campus cities:
**318 of 319 resolved** (Dunconnor Workshop unfindable — likely a defunct
private studio), 59 web-verified, the rest unambiguous knowledge.

The headline wasn't precision — it was **27 wrong-state errors hiding under
the centroids**: Rowan plotted in PA (it's Glassboro NJ), Purdue in TX,
Tufts in MI, Ghost Ranch in GA (Abiquiu NM), Peters Valley in DE (Layton NJ),
Washington Glass School in WA state (it's Mount Rainier MD — the scanner
matched the wrong "Washington"), Silvera Jewelry School in VA (its Berkeley CA
street address is "Virginia St"). All corrected via `data/geocode_cities.json`
(exact-name overlay, wins over fragment matching; also corrects find_state).

Also surfaced: **19 non-US schools** (Canada / Mexico / UK / Australia —
NSCAD, OCAD, Instituto Allende, Birmingham School of Jewellery, TAFE NSW…)
that an Albers-USA map can't draw; the map legend now discloses them.

Map before → after: 144 city-accurate / 221 state-centroid / 98 unplaced →
**462 city-accurate / 1 state-centroid / 0 unplaced** (444 on the US map +
19 disclosed non-US).
