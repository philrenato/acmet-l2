#!/usr/bin/env python3
"""Remove speculative death language from fc_summary bios (Phil: don't comment on
whether someone is alive unless there's a good source). Sentence-level: drop any
sentence that speculates about a death without a firm date; keep sentences that
state a sourced death (with a year)."""
import os, re, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
con = sqlite3.connect(os.path.join(HERE, "acmet.db")); cur = con.cursor()

SPEC = re.compile(r"(likely|almost certainly|most likely|presumably|very likely|"
                  r"certainly long|certainly|probably)\s+(be\s+)?deceased|"
                  r"status\s+(is|could not be|remains)\s+(unknown|not)|"
                  r"no\s+(obituary|death|record|verifiable|current activity|recent)"
                  r"[^.]*?(found|confirmed|located|could be)", re.I)
HAS_YEAR_DEATH = re.compile(r"(died|d\.|death|passed away|deceased)\D{0,30}(18|19|20)\d\d", re.I)

def split_sentences(t):
    # naive but safe: split on ". " keeping the period
    parts = re.split(r"(?<=\.)\s+", t)
    return [p for p in parts if p.strip()]

changed = []
for pid, name, summ in cur.execute("SELECT id,name,fc_summary FROM people WHERE fc_checked IS NOT NULL AND fc_summary IS NOT NULL"):
    sents = split_sentences(summ)
    kept = []
    drop = False
    for s in sents:
        if SPEC.search(s) and not HAS_YEAR_DEATH.search(s):
            drop = True
            continue  # drop speculative sentence
        kept.append(s)
    if drop:
        new = " ".join(kept).strip()
        new = re.sub(r"\s+", " ", new)
        changed.append((pid, name, summ, new))

print(f"{len(changed)} summaries to scrub\n")
for pid, name, old, new in changed:
    print(f"--- {name} ---")
    print("  BEFORE:", old[-160:])
    print("  AFTER :", new[-160:])
    print()
    cur.execute("UPDATE people SET fc_summary=? WHERE id=?", (new, pid))
con.commit(); con.close()
print("committed.")
