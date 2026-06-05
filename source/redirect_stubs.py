#!/usr/bin/env python3
"""redirect_stubs.py — overwrite retired page filenames with redirect stubs.

When the 2026-06-05 dedup pass merged duplicate programs/people (and fixed the
Nebraska Wesleyan OCR garble), their old URLs stayed live — GitHub Pages keeps
whatever was pushed, and deploy.sh rsyncs without --delete at the site root.
So each retired filename becomes a tiny meta-refresh + canonical stub pointing
at the page that absorbed it. Rerunnable; safe to run after any rebuild
(build_site.py never writes these names again).
"""
import html, os

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")

REDIRECTS = {  # retired file -> live target (same directory)
    # merged duplicate programs
    "academy-of-art-university.html":  "academy-of-art-college.html",
    "arcadia-university.html":         "beaver-college.html",
    "craft-alliance.html":             "craft-alliance-center-of-art-and-design.html",
    "front-range-community-college.html": "front-range-community-college-larimer-campus.html",
    "glassell-school-of-art-studio-school.html": "glassell-school-of-art-the-museum-of-fine-arts.html",
    "nebraska-wesl-e-yan-university.html": "nebraska-wesleyan-university.html",
    "ox-bow-school-of-art.html":       "ox-bow-school-of-art-artists-residency.html",
    "southern-illinois-university.html": "southern-illinois-university-carbondale.html",
    "suny-buffalo-state-university.html": "state-university-college-at-buffalo.html",
    "suny-new-paltz.html":             "state-university-of-new-york-at-new-paltz.html",
    "suny-college-at-brockport-department-of-art-and-design.html":
        "state-university-of-new-york-at-brockport.html",
    "tennessee-tech-university-appalachian-center-for-craft.html":
        "appalachian-center-for-crafts-t-t-u.html",
    "university-of-texas-rio-grande-valley-school-of-art-and-design.html":
        "the-university-of-texas-pan-american.html",
    # merged duplicate people
    "andrew-lowrie.html":              "andy-lowrie.html",
    "andrewlowrie.html":               "andy-lowrie.html",
    "bill-derrevere.html":             "william-r-derrevere.html",
    "carlyle-smith.html":              "carlyle-h-smith.html",
    "caryn-hetherston.html":           "caryn-l-hetherston.html",
    "kristi-glick.html":               "kristina-glick.html",
    "phillip-renato.html":             "phil-renato.html",
    # renamed person (name fix on an earlier pass left the old file behind)
    "jill-gower.html":                 "jill-baker-gower.html",
    # page built under an older eligibility rule, since held back — send to the
    # program that lists him
    "stephen-f-saracino.html":         "state-university-college-at-buffalo.html",
}

STUB = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url={t}">'
        '<link rel="canonical" href="{t}"><title>{n}</title></head>'
        '<body><a href="{t}">{n}</a></body></html>')

for src, target in REDIRECTS.items():
    tp = os.path.join(SITE, target)
    assert os.path.exists(tp), f"target missing: {target}"
    name = html.escape(target[:-5].replace("-", " ").title())
    open(os.path.join(SITE, src), "w").write(STUB.format(t=target, n=name))
print(f"wrote {len(REDIRECTS)} redirect stubs")
