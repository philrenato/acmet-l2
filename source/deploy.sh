#!/usr/bin/env bash
# deploy.sh — build the site from acmet.db and publish the whole project to the
# philrenato/acmet-l2 repo (the one GitHub Pages serves at renato.design/acmet-l2/).
#
# Layout in the published repo:
#   /            <- built site (index.html, profile + program pages, map/, lineage.html, *.md bios)
#   /source/     <- the full project: acmet.db, build/load/workflow scripts, archive/, docs
#   /MIRROR.md   <- how to clone & extend (see also the site footer)
#
# Usage:  ./deploy.sh ["commit message"]
# The working copy of the project repo lives at $REPO (cloned if missing).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${ACMET_REPO:-/tmp/acmet-deploy}"
MSG="${1:-Update directory + republish}"

echo "==> build"
cd "$HERE"
python3 build_graph.py >/dev/null
python3 build_map.py >/dev/null
python3 build_lineage.py >/dev/null
python3 build_site.py | tail -2

echo "==> sync into $REPO"
[ -d "$REPO/.git" ] || git clone https://github.com/philrenato/acmet-l2.git "$REPO"
# published site at root
rsync -a --exclude 'wiki/' "$HERE/site/" "$REPO/"
cp "$HERE/site/wiki/"*.md "$REPO/" 2>/dev/null || true
mkdir -p "$REPO/data"; cp "$HERE/data/acmet-graph.json" "$REPO/data/" 2>/dev/null || true
cp "$HERE/MIRROR.md" "$REPO/" 2>/dev/null || true
touch "$REPO/.nojekyll"
# full source under /source (everything except build output, DB backups, git)
rsync -a --delete \
  --exclude 'site/' --exclude '.git/' --exclude '*.bak-*' --exclude '__pycache__/' \
  "$HERE/" "$REPO/source/"

echo "==> commit + push"
cd "$REPO"
git add -A
git commit -q -m "$MSG" || { echo "(nothing to commit)"; exit 0; }
git push origin main | tail -1
echo "==> done. live (after Pages rebuild): https://renato.design/acmet-l2/"
