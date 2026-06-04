# Academic Metals Directory (acmet-l2)

**Live site: https://renato.design/acmet-l2/**

The recovered Tyler School of Art "Academic Metals Directory" — US jewelry,
metals, and CAD-CAM teaching programs and the people who taught them, curated
by Stanley Lechtzin until the site died. The only copy left was in the Wayback
Machine. It was pulled back down, parsed into a database, fact-checked person
by person and program by program (alive? still teaching? name changed? what
happened to the program?), and republished — with a US map and a
teacher-to-student lineage timeline back to 1885.

## What's in this repo

- **The repo root is the published site** (GitHub Pages): `index.html`, ~780
  person pages, ~460 program pages, `map/`, `lineage.html`. The HTML here is
  generated — don't hand-edit it; it gets overwritten on every deploy.
- **`/source/` is the actual project**: the database (`acmet.db`, SQLite —
  the single source of truth), the build scripts, the recovered Wayback
  archive, CSV exports, and the research docs (method, findings, audit log).
- **`*.md` files at the root** (e.g. `Phil-Renato.md`) are hand-written bios —
  the one part of a page meant to be edited directly. Each site page loads its
  bio from here when one exists.

## Fix something / add someone

Every claim on the site carries a source URL and a last-checked date.
If something's wrong:

- Use the **✎ edit this bio** link on any page — GitHub forks and opens a
  pull request for you. No write access needed.
- Or [open an issue](https://github.com/philrenato/acmet-l2/issues) with the
  correction and a source.
- Corrections to **your own entry** are authoritative. If a living person asks
  to be edited or removed, that's honored.

## Mirror & extend it

Start with [MIRROR.md](MIRROR.md) — clone, poke at `source/acmet.db` with
`sqlite3` (no setup), rebuild the whole site with four stdlib-only Python
scripts, or open the folder in an LLM coding tool and pick up where this left
off. The data model generalizes past metals to any art/design/craft
discipline; that's the roadmap (`source/FUTURE.md`).

## Ground rules

Sources, not guesses. No death is asserted without a good source. State what
someone is or was doing, never what they aren't. The archived pages
(hand-verified by Stanley Lechtzin) are the trusted baseline; everything newer
carries a citation.
