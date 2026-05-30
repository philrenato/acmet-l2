# Academic Metals Directory — Fact-Check Research Log

Project: **acmet-l2** — update the recovered Tyler M/J/C-C "Academic Metals
Directory" (offline; last live captures 2014–2019). For each person/program in
the archive: still in the job? still alive? name changed? current links? what
happened to the program / who replaced them?

Method: every claim carries a **source URL**, a **confidence** level, and a
**date-checked**. Nothing is asserted without a citation. Findings are logged
here (narrative, auditable) and mirrored into `acmet.db` → `factcheck` table.

Date-checked entries below: **2026-05-29**.

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

**People (217):** alive 74 · deceased 68 (+16 likely) · unknown 59 ·
retired-emeritus 109 · moved 60 · still-in-archived-job 13.
Confidence: high 152 / medium 41 / low 24. Verify: confirmed 85 / disputed 17 /
not-needed 115.

**20 name changes found**, e.g.:
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
