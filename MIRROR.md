# Mirror & extend the Academic Metals Directory

This whole project is open source. If you want to pick it up — fix a record, add
people, verify claims, or rescope it past metals — you can have it running locally
in a couple of minutes, and an LLM (Claude Code or similar) can do most of the work.

**Live site:** https://renato.design/acmet-l2/

## What this is

A recovered, brought-current directory of US jewelry / metals / CAD-CAM teaching
programs and the people who taught them — originally the Tyler School of Art
"Academic Metals Directory" (curated by Stanley Lechtzin), which went offline and
survived only in the Wayback Machine. It was pulled back down, parsed into a
database, fact-checked, and cross-linked. One database (`acmet.db`) feeds three
faces: the directory of people, a US map, and a lineage timeline.

## Get it

```
git clone https://github.com/philrenato/acmet-l2.git
cd acmet-l2
```

- The **published site** is at the repo root (`index.html`, the profile pages,
  `map/`, `lineage.html`) — that's what GitHub Pages serves.
- **Everything you'd edit** is in **`source/`**: the database, the build scripts,
  the recovered archive, the docs.

```
cd source
```

## The database is the source of truth

`source/acmet.db` (SQLite). Poke at it with no setup:

```
sqlite3 acmet.db "select name, currently_at from people where fc_checked is not null limit 10;"
sqlite3 acmet.db "select name, fc_current_name from people where fc_change_kind='name-change';"
sqlite3 acmet.db "select name, school_type, fc_still_exists from programs;"
```

Key tables: `people`, `programs`, `education` (who studied where, under whom),
`program_faculty` (who taught where, current/former), `factcheck` (the audit log).
The `fc_*` columns hold the fact-check layer (alive / current role / name change /
source URL / confidence), all dated and sourced.

## Rebuild the site from the database

Python 3, no dependencies beyond the standard library:

```
python3 build_graph.py     # acmet.db -> data/acmet-graph.json (nodes + edges + geo)
python3 build_map.py       # -> site/map/
python3 build_lineage.py   # -> site/lineage.html
python3 build_site.py      # -> site/  (the directory index + every profile + program page)
```

Then the contents of `source/site/` are copied to the repo root to publish.
`deploy.sh` does the whole build-and-publish in one step.

## Work on it with an LLM

Open this folder in an LLM coding tool and tell it what you want. Good first asks:

- *"Read MIRROR.md and the *.md docs, then summarize the data model and what's
  been done."*
- *"Add <person>: here's their current institution and a source — insert them and
  cross-link."* (see how recent additions were done in `load_people_records.py`)
- *"Re-verify everyone marked low-confidence or disputed and fix the records with
  solid permalink sources."*
- *"Find current metals/jewelry faculty we're missing"* — the gap pass used SNAG's
  public directory via its WordPress REST API
  (`/wp-json/wp/v2/community_links?link_type=613` for schools, `615` for craft-centers).

Read `HANDOFF.md` and `RESEARCH_LOG.md` for the method, and `CHANGES.md` /
`GAPS.md` / `SUCCESSION.md` for what was found.

## Ground rules (please keep these)

- **Sources, not guesses.** Every factual change needs a real link — ideally the
  institution's own page or an obituary. Never invent a URL. Mark honest
  "unknown" / "low confidence" rather than padding.
- **Don't speculate about whether someone is alive.** If there's no good source,
  say nothing about it.
- **State what someone is or was doing, never what they aren't** ("Professor
  Emerita," not "no longer teaching").
- **The archived pages are the trusted baseline** (hand-verified by Stanley
  Lechtzin). Anything newer than the archive should be verifiable.
- **Living people get a say** before new entries about them go public.

## How to contribute back

Open a pull request or an issue at https://github.com/philrenato/acmet-l2 with the
change and its source. Corrections to your own entry are especially welcome.
