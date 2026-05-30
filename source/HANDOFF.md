# acmet-l2 — handoff (state as of 2026-05-30)

Where this project is, so anyone (or a future Claude session) can pick it up cold.
Plain-language map; the README is the front door, this is the "what's actually done
and what's loose" doc.

## status: working. everything below is built, run, and verified.

### what got done
1. **recovered** the dead Tyler "Academic Metals Directory" from the Wayback Machine
   → `archive/` (4,492 text pages, frozen). tool: `archive/wayback_pull.py`.
2. **parsed** it into `acmet.db` (people / education / programs / program_faculty /
   factcheck). extractor: `build_database.py`.
3. **fact-checked** 217 people + 202 programs with a multi-agent workflow (alive? job?
   name change? program fate?) — sourced + adversarially verified. → `factcheck_workflow.js`,
   loaded by `load_factcheck.py`. notable stuff in `CHANGES.md`.
4. **gap analysis** — programs the directory missed / nothing founded post-2014.
   → `gap_workflow.js` → `GAPS.md`.
5. **faculty-succession re-scan** of 152 surviving programs — who teaches metals *now*.
   added **218 successors** (db now 651 people), flagged 34 programs that quietly lost
   metals. → `succession_workflow.js` → `load_succession.py` → `SUCCESSION.md`.
6. **the site** — directory index (218 names, the built-out ones lit) + per-person
   profile pages (then/now + DB facts + bio pulled live from GitHub). `build_site.py`.
   7 built out: Phil Renato, Mary Lee Hu, Stanley Lechtzin, Daniella Kerner, Vickie
   Sedman, Rebecca Strzelec, Skip Hunter.
7. **three cohered faces over one database:**
   - the **directory** (names) — `index.html` + profile pages
   - the **map** — `site/map/` — US map, glowing program dots + lineage-migration arcs,
     city-level geocoding. `build_graph.py` → `build_map.py`.
   - the **lineage** — `site/lineage.html` — dark timeline/genealogy (my `/ecosystem/`
     system rebuilt natively): timeline / lineage / all-connections modes, click-to-trace.
     `build_graph.py` → `build_lineage.py`.

### the build pipeline (one DB → three faces)
```
acmet.db ──build_graph.py──▶ data/acmet-graph.json ──▶ build_map.py     (map)
                                                    └─▶ build_lineage.py (lineage)
acmet.db ──build_site.py──▶ index + profile pages
```
Stable slugs throughout, so cross-linking the faces is additive, not rework.

### the live page
- repo: `github.com/philrenato/acmet-l2` (PUBLIC), served by GitHub Pages on renato.design.
- `site/phil-renato.html` — then/now entry, facts from the DB, bio pulled live from GitHub.
- `site/wiki/Phil-Renato.md` — the editable bio (also pushed to the repo root as `Phil-Renato.md`).
- bio source order: github **wiki** → github **repo file** → built-in copy. right now it
  serves the repo file ("live · github repo") because the wiki isn't bootstrapped yet.
- "✎ edit this bio" link on the page → GitHub editor for the bio.

### the one loose thread: the wiki
GitHub won't let a wiki be created by API or push — the **first page must be made in the
browser** once. to finish wiring the true wiki:
1. go to `github.com/philrenato/acmet-l2/wiki` → create the first page (save anything).
2. then push the bio:
   ```
   cd /tmp && rm -rf w && git clone https://github.com/philrenato/acmet-l2.wiki.git w
   cp ~/acmet-l2/site/wiki/Phil-Renato.md w/ && cd w
   git add . && git commit -m "Phil Renato bio" && git push
   ```
3. the page auto-flips to "live · github wiki" — no code change.

## open items / next moves  (full roadmap in FUTURE.md)
- **full pages for everyone** sourceable — flip `build_site.py` BUILT→all-with-fc-data; bios via a workflow.
- **per-page interlinking** — map ↔ lineage ↔ profile via `?focus=slug` deep-links (click map → person → back).
- **let anyone add a person/program** — contributor flow (form → GitHub issue/PR, or editable data file).
- **solid search** across names / programs / states / degrees / instructors / lineage.
- **finish geocoding** the last ~84 state-level programs to city precision (CITY/INST_CITY tables in build_graph.py).
- **rescope** beyond metals → all art/design/crafts. same data model.
- **clean the noisy rows**: `fc_verified='disputed'` (17) + `fc_confidence='low'` need a human pass.
- **consent** before any of this goes public for living people (original handoff §8).

## gotchas (don't relearn these the hard way)
- DON'T re-run `build_database.py` on the live DB — it drops + rebuilds, wiping the `fc_*`
  columns. re-extract, THEN re-run the loaders. (build_graph/map/lineage/site are safe to re-run.)
- workflow results come back wrapped — read `result.{people|programs}` from the task
  **output file**, not the truncated inline notification. per-agent transcripts are the backup.
- verify any live page with headless Chrome + a `?v=$(date +%s)` cache-bust; Pages' CDN
  lags a few minutes, and **Safari caches HTML hard** (⌥⌘R to force-refresh).
- recovery enumeration must NOT use CDX `collapse=urlkey` (gives earliest, not latest).
- **map geocoding** is city-level via tables in `build_graph.py` (state centroids were wrong —
  "no dots in Detroit"). 90 city-accurate, 84 still state-level.
- **lineage perf/layout** (build_lineage.py): cap dot size + fixed lane spacing or dots overlap;
  declutter labels (≤16) + reveal on zoom/hover; NEVER drop-shadow all 639 nodes (Safari crash) —
  glow only on focus; use edge index not E.indexOf; clamp junk years.
- "state what someone is/was doing, never what they aren't" (Phil's copy rule — baked into build_site.py).

## the keeper insight
for a people-directory, the updates that matter most are the ones a flat scan can't see:
**name changes** (Rizzi→Carrizzi→Renato) and **faculty succession** (who replaced whom; which
programs quietly died when someone retired). build for those first.
