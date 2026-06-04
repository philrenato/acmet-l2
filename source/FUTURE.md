# acmet-l2 — future direction

> Written 2026-05-29/30; items marked ✅ were completed in later passes — HANDOFF.md
> has the current state.

## Rescope: from Metals/Jewelry to all art / design / crafts (Phil, 2026-05-29)

Expand the directory beyond just **Metals/Jewelry/CAD-CAM** to a broad directory
of **art, design, and crafts schools + people**. The recovered Tyler directory is
the seed; the goal is a wider academic directory.

Keep the same data model that already works here — it generalizes cleanly:

- **people** ↔ **programs** ↔ **instructors**, with education history and a
  fact-check layer (alive / current role / name change / current link).
- The `fc_*` + `factcheck` machinery (sourced, confidence-rated, adversarially
  verified) applies to any discipline unchanged.

What widening the net means in practice:
- Add disciplines: ceramics, fibers/textiles, glass, wood/furniture, sculpture,
  printmaking, graphic/industrial/product design, etc.
- New seed sources per discipline (the field's equivalent of SNAG for metals —
  e.g. NCECA for ceramics, GAS for glass, the Furniture Society, AIGA for design).
- Same recovery trick where other field directories have gone offline (CDX +
  latest-200 + `id_` raw fetch, text-first).

## Roadmap (Phil's notes, 2026-05-30)
- ✅ **Full pages for everyone** we can source — done; `build_site.py` builds every
  record with fc-data (781 person + 463 program pages); thin records carry a
  "corrections welcome" note.
- **Per-page interlinking** — map ↔ lineage ↔ profile all wired: every node links
  to its page; every page links "see in map / see in lineage" centered on that
  person (`?focus=slug` deep-links). Click map → person → back to map.
- **A way for anyone to add a person or program** — a contributor flow (form →
  GitHub issue/PR, or an editable data file like the bios already are). New entry
  = a row in the data + a bio markdown.
- ✅ **Solid search** — done 2026-06-04: index matches names + schools +
  instructors + cities/states + former names (`data-kw`); the map and lineage
  each have a find box; people resolve to the dot where they taught
  (`data/search.json`, one manifest for all three faces).
- ✅ **Finish geocoding** — done 2026-06-04: all 463 programs placed, 462 at
  campus-city precision (`data/geocode_cities.json`); 27 wrong-state dots
  corrected; 19 non-US schools disclosed on the map.

## Other open threads (from this build)
- ✅ **Gap analysis** of current vs. archived programs — done (GAPS.md; the SNAG
  gap pass added 266 programs + ~396 current faculty).
- Re-check the `disputed` / `low-confidence` rows by hand.
- ✅ Republication decided — it's live and public at renato.design/acmet-l2/;
  corrections / removal requests via GitHub are authoritative.

## How it's all wired (so the roadmap is just wiring, not rework)
One database (`acmet.db`) → `build_graph.py` emits `data/acmet-graph.json`
(nodes + edges + geo) → that one file feeds `build_map.py` (US map) and
`build_lineage.py` (timeline/genealogy); `build_site.py` emits the directory +
profile pages. Stable slugs throughout, so cross-linking the three faces is
additive.
