# acmet-l2

my old grad-school world, dug back up and brought current.

this is the academic metals directory — the directory of US jewelry/metals/cad-cam
programs and the people who taught them, run out of tyler (temple) and curated by
stanley lechtzin. it died. every page 404s. the only copy left was in the wayback
machine. so i pulled all of it back down, then went person by person, program by
program, and asked: are you still here? still teaching? still alive? did your name
change? what happened to your program?

(my own entry is in here, under my old name — phil carrizzi, now phil renato.
that's how i knew the recovery worked.)

## three ways to look at it (all from one database)

live at **renato.design/acmet-l2/**:

- **the directory** — the list of names. greyed until someone's built out; a handful
  are done (me, mary lee hu, lechtzin, kerner, sedman, strzelec, skip hunter). each
  built page is the old listing next to today's facts, with a bio you can edit on github.
- **the map** (`/map/`) — everybody on a us map, glowing by how connected they are, with
  arcs showing where people studied then went off to teach. the craft spreading across
  the country.
- **the lineage** (`/lineage.html`) — a timeline, 1885 to now. who taught whom, running
  down the page. hover for a name, zoom in to read them all, click anyone to trace their line.

one database feeds all three. fix a record, they all update.

## what's in the box

- **archive/** — the recovered site, frozen. don't touch it. 4,492 pages, text only
  (i skipped the student-gallery images on purpose — wrong thing to be hauling around).
  the recovery tool (`wayback_pull.py`) and the original handoff live in here too.
- **build_graph.py → build_map.py / build_lineage.py** — turn the db into the map + lineage.
  **build_site.py** — turn the db into the directory + pages. all safe to re-run.
- **acmet.db** — the actual database. people, programs, who taught who, and the
  fact-check layer (alive / current job / name change / current link, all with sources).
- **exports/** — same thing as plain csv if you'd rather open it in numbers.
- **CHANGES.md** — just the stuff that changed: name changes, deaths, closed programs.
- **GAPS.md** — programs that should've been in the directory but weren't.
- **SUCCESSION.md** — who's teaching metals now at programs that survived (and which
  programs quietly lost metals when their person retired).
- **RESEARCH_LOG.md** — the show-your-work. method + the marquee write-ups.
- **FUTURE.md** — where this goes next (short version: stop being just metals).

## what i found

- ~half the programs are gone or folded into something else. nobody started a new
  one after this went offline — the last decade was closures, not openings.
- 20 people changed their names. those are the easy-to-miss ones, so they're flagged loud.
- a lot of the old guard has died — the directory had no way to know. now it does,
  with obituaries attached.
- the real gold isn't in the directory's own names — it's the people who *replaced*
  them and never got listed. anne mondro at michigan. that whole layer was invisible
  until i went looking program by program.

## poking at it

```
sqlite3 acmet.db "select name, fc_current_name from people where fc_name_changed='yes';"
sqlite3 acmet.db "select name, fc_what_happened from programs where fc_still_exists='no';"
open exports/people.csv
```

## fair warning

- anything marked low confidence or "disputed" needs a human look. those are mostly
  obscure folks with no web trail, or two facts that don't agree. left visible on purpose.
- old-timers with no findable obituary are marked "unknown," not guessed dead.
- don't re-run `build_database.py` on the live db — it rebuilds from scratch and wipes
  the fact-check columns. re-extract first, then reload.

## next

faculty-succession pass (who teaches metals *now* at every surviving program),
clean up the disputed rows, then open it up past metals into the rest of art/design/crafts.
nobody needs to ask permission to be in a directory — but living people get a say
before any of this goes public.
