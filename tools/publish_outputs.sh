#!/usr/bin/env bash
# =====================================================================
# publish_outputs.sh: commit and push regenerated pipeline outputs.
#
# The one exception to "the maintainer only pulls": run this on the
# machine that holds the raw data, AFTER the local pipeline steps
# (viina/run_all.sh, make_map_previews.py, 30_data_package.py, pulls).
# Code and documents are never committed from here; they come from
# Claude's clone and arrive with `git pull --ff-only`.
#
# Usage (from anywhere inside the repository):
#   tools/publish_outputs.sh --dry-run          # show what would be committed, change nothing
#   tools/publish_outputs.sh                    # commit + push, asks for confirmation
#   tools/publish_outputs.sh "refresh: data to 2026-09"   # custom commit subject
#   tools/publish_outputs.sh --yes "…"          # no confirmation prompt
#
# What it does:
#   1. Refuses unless on main, index clean, and no local commits ahead of origin.
#   2. Fast-forwards to origin/main (git pull --ff-only).
#   3. Classifies every change in the working tree:
#        modified output files        -> staged
#        new files on ALLOW_NEW       -> staged
#        anything else (code, docs, deletions, unknown new files) -> STOP
#   4. Runs guards.sh and the HELD map-page check on the staged state.
#   5. Commits with a fixed message and pushes.
#
# If it stops, nothing is committed. Copy the output to Claude.
# NEVER run `git clean -x`/`-X`/`-fdx` in this tree.
# =====================================================================
set -euo pipefail

# ---- generated outputs (paths or directory prefixes, relative to root)
OUTPUTS=(
  "resilience/tidy/"
  "resilience/public/"
  "resilience/docs/fig1_carpathian_light.png"
  "resilience/docs/fig1_carpathian_light.svg"
  "publication/figures/"
  "viina/strikes_by_month_oblast.csv"
  "viina/qgis/meta.json"
  "viina/qgis/maps/preview/"
)

# ---- new output files allowed on first commit (exact paths).
# Claude adds a path here when a new script starts producing a tracked
# output; once it is committed, the entry can be removed again.
ALLOW_NEW=(
  "resilience/tidy/sphere_classes.json"
)

DRY=0; YES=0; SUBJECT=""
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --yes|-y)  YES=1 ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    -*) echo "unknown option: $a" >&2; exit 2 ;;
    *)  SUBJECT="$a" ;;
  esac
done
[[ -n "$SUBJECT" ]] || SUBJECT="outputs: regenerate $(date +%F)"

cd "$(git rev-parse --show-toplevel)"
stop() { echo; echo "STOP: $*"; echo "Nothing was committed. Copy this output to Claude."; exit 1; }
push_fail() { echo; echo "STOP: push failed. The commit IS made locally: $(git log --oneline -1)"; \
  echo "Retry with: git -c http.postBuffer=157286400 -c http.version=HTTP/1.1 push --progress origin main"; exit 1; }
in_outputs() {
  local f=$1 o
  for o in "${OUTPUTS[@]}"; do
    [[ "$o" == */ ]] && [[ "$f" == "$o"* ]] && return 0
    [[ "$f" == "$o" ]] && return 0
  done
  return 1
}
in_allow_new() {
  local f=$1 o
  for o in "${ALLOW_NEW[@]+"${ALLOW_NEW[@]}"}"; do [[ "$f" == "$o" ]] && return 0; done
  return 1
}

# ---- 1. preconditions --------------------------------------------------
[[ "$(git symbolic-ref --short HEAD)" == "main" ]] || stop "not on branch main"
git diff --cached --quiet || stop "the index already has staged changes (git status); unstage them with: git restore --staged ."
git fetch -q origin main
ahead=$(git rev-list --count origin/main..HEAD)
[[ "$ahead" -eq 0 ]] || stop "main has $ahead local commit(s) not on origin: $(git log --oneline origin/main..HEAD | tr '\n' ';')"

# ---- 2. fast-forward -----------------------------------------------------
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
  echo "== git pull --ff-only"
  git merge --ff-only -q origin/main || stop "fast-forward failed (a regenerated output collides with a new commit on origin)"
fi

# ---- 3. classify changes -------------------------------------------------
stage=(); refused=()
while IFS= read -r -d '' rec; do
  xy=${rec:0:2}; f=${rec:3}
  case "$xy" in
    " M"|" T")
      if in_outputs "$f"; then stage+=("$f"); else refused+=("modified, not an output: $f"); fi ;;
    " D")
      refused+=("deleted: $f") ;;
    "??")
      if in_outputs "$f" && in_allow_new "$f"; then stage+=("$f")
      else refused+=("new file, not on ALLOW_NEW: $f"); fi ;;
    *)
      refused+=("status '$xy': $f") ;;
  esac
done < <(git status --porcelain=v1 -z --untracked-files=all)

if (( ${#refused[@]} )); then
  printf '  %s\n' "${refused[@]}"
  stop "changes outside the publishable outputs (above)"
fi
(( ${#stage[@]} )) || { echo "No changed outputs. Nothing to publish."; exit 0; }

# ---- 4. stage and check --------------------------------------------------
git add -- "${stage[@]}"
unstage() { git restore --staged -- "${stage[@]}" 2>/dev/null || git reset -q -- "${stage[@]}"; }

echo "== guards.sh"
bash .github/workflows/guards.sh || { unstage; stop "guards failed"; }

echo "== HELD map pages"
held=$(python3 - <<'EOF'
import ast, pathlib
src = pathlib.Path("viina/make_map_previews.py").read_text(encoding="utf-8")
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "HELD" for t in node.targets):
        print(" ".join(ast.literal_eval(node.value).keys()))
EOF
)
[[ -n "$held" ]] || { unstage; stop "could not read HELD from viina/make_map_previews.py"; }
for p in $held; do
  hit=$(git ls-files 'viina/qgis/maps/' | grep -E "/${p}_[^/]*$" || true)
  [[ -z "$hit" ]] || { unstage; stop "held map page $p would be committed: $hit"; }
done
echo "held pages not tracked: $held"

echo
echo "== to be committed: $SUBJECT"
git diff --cached --stat

if (( DRY )); then
  unstage
  echo; echo "Dry run: nothing committed, index restored."
  exit 0
fi
if (( ! YES )); then
  read -r -p "Commit and push? [y/N] " ans
  [[ "$ans" == "y" || "$ans" == "Y" ]] || { unstage; echo "Aborted, index restored."; exit 1; }
fi

# ---- 5. commit and push --------------------------------------------------
dirs=$(printf '%s\n' "${stage[@]}" | sed 's|/[^/]*$||' | sort | uniq -c | awk '{printf "  %s (%s)\n", $2, $1}')
git commit -q -F - <<EOF
$SUBJECT

Generated outputs, committed by tools/publish_outputs.sh:
$dirs
EOF
# single-request upload with progress: chunked pushes of several MB time out (HTTP 408) on slow links
git -c http.postBuffer=157286400 -c http.version=HTTP/1.1 push --progress origin main || push_fail
echo; git log --oneline -1
echo "Published."
