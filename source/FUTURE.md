# acmet-l2 — future direction

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
- **Full pages for everyone** we can source (flip `build_site.py` from the 7-name
  BUILT list to all-with-fc-data; bios via a workflow; thin records carry a
  "corrections welcome" note).
- **Per-page interlinking** — map ↔ lineage ↔ profile all wired: every node links
  to its page; every page links "see in map / see in lineage" centered on that
  person (`?focus=slug` deep-links). Click map → person → back to map.
- **A way for anyone to add a person or program** — a contributor flow (form →
  GitHub issue/PR, or an editable data file like the bios already are). New entry
  = a row in the data + a bio markdown.
- **Solid search** — across names, programs, states, degrees, instructors,
  lineage; powers all three faces (directory, map, lineage).
- **Finish geocoding** the remaining ~84 state-level programs to city precision.

## Other open threads (from this build)
- **Gap analysis** of current vs. archived programs — see the gap-analysis output.
- Re-check the `disputed` / `low-confidence` rows by hand.
- Decide republication model + living-person consent before anything goes public
  (per the original handoff §8).

## How it's all wired (so the roadmap is just wiring, not rework)
One database (`acmet.db`) → `build_graph.py` emits `data/acmet-graph.json`
(nodes + edges + geo) → that one file feeds `build_map.py` (US map) and
`build_lineage.py` (timeline/genealogy); `build_site.py` emits the directory +
profile pages. Stable slugs throughout, so cross-linking the three faces is
additive.
