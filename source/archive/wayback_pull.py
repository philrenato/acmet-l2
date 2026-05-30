#!/usr/bin/env python3
"""
wayback_pull.py — recover the old Temple "Academic Metals Directory" from the
Internet Archive Wayback Machine.

Retrieval + assembly only. No redesign. See HANDOFF_academic-metals-directory.txt.

    pip install requests beautifulsoup4
    python wayback_pull.py

TEXT ONLY: images are deliberately NOT downloaded (Phil's call — the student
gallery imagery is the riskier artifact and isn't needed for the directory).
Each page's image_refs are still recorded so images stay recoverable later.

Design (two clean passes so the corpus is always complete + idempotent):
  1. ENUMERATE  — CDX, NO collapse, keep the LATEST status-200 text/html
                  capture per URL (the handoff's "most complete before takedown"
                  rule). Cached to data/cdx_full.json.
  2. FETCH      — download each page's latest capture via the id_ modifier
                  (original bytes, no Wayback toolbar) into raw/. Resume-safe:
                  files already on disk are skipped.
  3. PARSE      — walk the on-disk raw/ mirror and (re)build pages.json,
                  schools.json, manifest.txt EVERY run, so resuming never
                  yields a partial structured corpus.

Output: ./amd-recovery/{raw, data/{cdx_full,cdx_best,pages,schools}.json, manifest.txt}
"""

import json
import os
import re
import sys
import time
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

# --- config -----------------------------------------------------------------
TARGET   = "temple.edu/crafts/*"
CDX      = "https://web.archive.org/cdx/search/cdx"
RAW_TPL  = "https://web.archive.org/web/{ts}id_/{url}"   # id_ = original bytes
OUT      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "amd-recovery")
UA       = "Mozilla/5.0 (AMD-recovery; metals-directory research; contact: philrenato@gmail.com)"
DELAY    = 1.5
RETRIES  = 6

NAV_NOISE = {
    "Tyler Home", "Index", "About Us", "Gallery", "M/J/C-C Home",
    "Net Resources", "Academic Metals Directory", "Contact Page", "Site Credits",
}

session = requests.Session()
session.headers.update({"User-Agent": UA})


# --- helpers ----------------------------------------------------------------
class Resp:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


def polite_get(url, **kw):
    """GET with backoff. archive.org's id_ endpoint often ends the transfer
    without a clean close though the full body arrived — we stream and keep
    whatever bytes we got, treating a non-empty 200 as success."""
    for attempt in range(RETRIES):
        try:
            r = session.get(url, timeout=60, stream=True, **kw)
            if r.status_code in (429, 503):
                wait = DELAY * (2 ** attempt)
                print(f"    rate-limited ({r.status_code}); backing off {wait:.0f}s", flush=True)
                r.close(); time.sleep(wait); continue
            status = r.status_code
            buf = bytearray()
            try:
                for chunk in r.iter_content(16384):
                    buf += chunk
            except requests.RequestException:
                pass
            finally:
                r.close()
            if status == 200 and not buf:
                wait = DELAY * (2 ** attempt)
                print(f"    empty 200 body; retry in {wait:.0f}s", flush=True)
                time.sleep(wait); continue
            return Resp(status, bytes(buf))
        except requests.RequestException as e:
            wait = DELAY * (2 ** attempt)
            print(f"    error: {e}; retry in {wait:.0f}s", flush=True)
            time.sleep(wait)
    return None


def local_path(original):
    p = urlparse(original)
    rel = (p.path or "/").lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    return os.path.join(OUT, "raw", p.netloc, rel)


def save(path, content, mode="wb"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        f.write(content)


def clean_text(soup):
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return "\n".join(
        ln for ln in text.splitlines()
        if ln.strip() and ln.strip() not in NAV_NOISE
    )


def classify(url, title):
    u = url.lower()
    t = (title or "").lower()
    if "/biographies/" in u or re.search(r"/b\d+\.html?$", u) or t.startswith("biography"):
        return "bio"
    if "gallery" in u:
        return "gallery"
    # individual directory entries (sNN) + program/school pages (pNN) + the tree
    if re.search(r"/[sp]\d+\.html?$", u) or any(k in u for k in ("metalsdirectory", "directory", "school")):
        return "school"
    if u.rstrip("/").endswith(("hhome.html", "intro.html", "index.html")) or "indexpage" in u:
        return "index"
    return "other"


def priority(url):
    """Directory core first so the Carrizzi proof lands early."""
    u = url.lower()
    if "gallery" in u:
        return (2, u)
    core = any(k in u for k in (
        "metalsdirectory", "/local/history", "indexpage", "net", "credit", "hhome", "aboutus"))
    return (0 if core else 1, u)


# --- step 1: enumerate ------------------------------------------------------
def enumerate_latest():
    """{url: {'ts','digest'}} — latest status-200 text/html capture per URL."""
    cache = os.path.join(OUT, "data", "cdx_full.json")
    if os.path.exists(cache):
        print(f"Using cached CDX ({cache})", flush=True)
        rows = json.load(open(cache))
    else:
        params = {
            "url": TARGET, "output": "json",
            "fl": "original,timestamp,statuscode,mimetype,digest",
            "filter": ["statuscode:200", "mimetype:text/html"],
            "limit": "300000",
        }
        print("Enumerating Wayback captures via CDX (no collapse)...", flush=True)
        r = polite_get(CDX, params=params)
        if not r or r.status_code != 200:
            sys.exit("CDX enumeration failed — check connectivity to web.archive.org.")
        rows = json.loads(r.content)
        save(cache, json.dumps(rows).encode())
    if rows and rows[0] and rows[0][0] == "original":
        rows = rows[1:]
    best = {}
    for orig, ts, _st, _mime, dg in rows:
        cur = best.get(orig)
        if cur is None or ts > cur["ts"]:          # LATEST capture wins
            best[orig] = {"ts": ts, "digest": dg}
    print(f"  {len(best)} unique HTML URLs (latest-200 each).", flush=True)
    return best


# --- step 2: fetch ----------------------------------------------------------
def fetch_all(best):
    items = sorted(best.items(), key=lambda kv: priority(kv[0]))
    total = len(items)
    failures = []
    for i, (url, meta) in enumerate(items, 1):
        dest = local_path(url)
        if os.path.exists(dest):
            continue
        print(f"[{i}/{total}] {url}", flush=True)
        r = polite_get(RAW_TPL.format(ts=meta["ts"], url=url))
        time.sleep(DELAY)
        if not r or r.status_code != 200 or not r.content:
            failures.append({"url": url, "why": f"fetch {getattr(r, 'status_code', 'none')}"})
            continue
        save(dest, r.content)
    return failures


# --- step 3: parse on-disk mirror ------------------------------------------
def parse_all(best, failures):
    pages, schools, hits = [], [], []
    referenced_imgs = set()
    for url, meta in sorted(best.items()):
        dest = local_path(url)
        if not os.path.exists(dest):
            continue
        raw = open(dest, "rb").read()
        try:
            soup = BeautifulSoup(raw, "html.parser")
        except Exception as e:
            failures.append({"url": url, "why": f"parse {e}"})
            continue
        title = soup.title.string.strip() if (soup.title and soup.title.string) else ""
        m = re.match(r"Biography:\s*(.+)", title, re.I)
        name = m.group(1).strip() if m else ""
        body = clean_text(soup)
        imgs = [urljoin(url, img["src"]) for img in soup.find_all("img", src=True)]
        links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]
        referenced_imgs.update(imgs)
        kind = classify(url, title)
        rec = {
            "url": url, "timestamp": meta["ts"], "digest": meta["digest"],
            "type": kind, "title": title, "name": name,
            "body_text": body, "image_refs": imgs, "links": links,
        }
        pages.append(rec)
        if kind == "school":
            schools.append(rec)
        if re.search(r"carrizzi|kendall", title + body, re.I):
            hits.append(f"{url}  (title={title!r})")

    save(os.path.join(OUT, "data", "pages.json"),
         json.dumps(pages, indent=2, ensure_ascii=False).encode())
    save(os.path.join(OUT, "data", "schools.json"),
         json.dumps(schools, indent=2, ensure_ascii=False).encode())

    bios = [p for p in pages if p["type"] == "bio"]
    gallery = [p for p in pages if p["type"] == "gallery"]
    carrizzi = [h for h in hits if "carrizzi" in h.lower()]
    lines = [
        "ACADEMIC METALS DIRECTORY — WAYBACK RECOVERY — RUN REPORT",
        "(text only; images deliberately not downloaded)",
        "",
        f"unique HTML URLs enumerated : {len(best)}",
        f"pages fetched + parsed      : {len(pages)}",
        f"  bios                      : {len(bios)}",
        f"  school/directory entries  : {len(schools)}",
        f"  gallery (text) pages      : {len(gallery)}",
        f"  index/other               : {len(pages) - len(bios) - len(schools) - len(gallery)}",
        f"fetch failures              : {len(failures)}",
        f"image URLs referenced (not downloaded) : {len(referenced_imgs)}",
        "",
        "CAPTURE POLICY: latest status-200 text/html capture per URL "
        "(the most complete version before takedown).",
        "",
        f"CARRIZZI located : {carrizzi or 'NOT FOUND — widen sweep / check old era'}",
        "",
        "ALL CARRIZZI / KENDALL SIGHTINGS:",
    ]
    lines += [f"  {h}" for h in hits] or ["  (none)"]
    lines += ["", "FETCH FAILURES:"]
    lines += [f"  {f['url']}  <-  {f['why']}" for f in failures] or ["  (none)"]
    save(os.path.join(OUT, "manifest.txt"), ("\n".join(lines) + "\n").encode())
    print(f"\nParsed {len(pages)} pages | bios {len(bios)} | schools {len(schools)} "
          f"| gallery {len(gallery)} | failures {len(failures)}", flush=True)
    print(f"Carrizzi: {carrizzi or 'NOT FOUND'}", flush=True)


def main():
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    best = enumerate_latest()
    save(os.path.join(OUT, "data", "cdx_best.json"), json.dumps(best, indent=2).encode())
    failures = fetch_all(best)
    parse_all(best, failures)
    print("\nDone. See ./amd-recovery/manifest.txt", flush=True)


if __name__ == "__main__":
    main()
