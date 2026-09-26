# Contributing and project notes

Working conventions for the Ukraine strikes × hromada resilience pipeline.

## Golden rules

- **Never run `git clean -x`, `-X` or `-fdx` in this tree.** The working copy holds about 40 GB
  of raw data, caches and GeoPackages that git ignores on purpose. `git clean -x` deletes them.
- **The `.gitignore` is a whitelist.** Everything is ignored unless re-included. A new script,
  table or document is not tracked until a matching `!` rule exists. Add rules deliberately and
  check with `git add -n .` before staging.
- **Secrets stay in the home directory**: `~/.earthdata_token` (NASA Earthdata) and
  `~/.dtm_key` (IOM DTM API, sent as `Ocp-Apim-Subscription-Key`). Scripts read them from there.
  Never paste a token into a script, log, notebook or issue.
- **Complete scripts only.** Changes replace whole files; no partial patches or hand edits of
  generated tables.
- **Tracked files are edited in one place only** (see Maintenance workflow). The data machine
  pulls; it never edits code or documents.

## Maintenance workflow

The repository has a single maintainer (Michel Garand). Code and documents are written by
Claude, working in its own clone with push access; the raw data (about 40 GB) exists only on the
maintainer's machine. This splits the work as follows.

| Who | Changes | How |
|---|---|---|
| Claude (own clone) | scripts, documents, `.gitignore`, CI, `numbers.yaml`, tags | commit, pre-push gate, push to `main` |
| Maintainer (data machine) | regenerated outputs only | local pipeline, then `tools/publish_outputs.sh` |
| Maintainer (data machine) | everything else | `git pull --ff-only` only |

### Commit identity

Commits from Claude's clone are authored as `Michel Garand <stewardship@ubec.network>` and end
with a `Co-Authored-By: Claude …` trailer and a `Claude-Session:` link. Commits made by
`publish_outputs.sh` carry the fixed subject `outputs: …` and list the output folders touched.
`git log --grep=Co-Authored-By` therefore separates Claude's commits from the maintainer's.

### Branch policy

- **Default: direct pushes to `main`**, after the pre-push gate below passes in Claude's clone.
  CI (`.github/workflows/checks.yml`) runs on every push and must stay green; a red run on
  `main` is fixed by the next commit, not by force-pushing.
- **Exception: `claude/<topic>` branch and pull request** for large or risky changes: new
  methodology, anything touching rules R1–R6, release preparation, or whenever the maintainer
  asks. The maintainer reviews and merges on GitHub. Claude cannot delete remote branches from
  its environment; enable Settings → General → "Automatically delete head branches", or delete
  the merged branch on GitHub.
- No force-pushes to `main`, no history rewrites.

### Pre-push gate (Claude's clone)

A local `pre-push` hook in Claude's clone aborts the push unless all of these pass:

1. `origin/main` is an ancestor of `HEAD` (fetched first; rebase if not).
2. `python -m py_compile` on all tracked `*.py`, on Python 3.13 as in CI.
3. `bash -n` on all tracked `*.sh`.
4. `cffconvert --validate`.
5. `bash .github/workflows/guards.sh`.
6. No map page listed in `HELD` (`viina/make_map_previews.py`) is tracked.
7. Secret scan (`detect-secrets`) of files changed since `origin/main`. gitleaks is not
   reachable from Claude's environment; GitHub push protection and secret scanning remain on.

New files are checked with `git add -n` against the whitelist before they are staged.

### Publishing regenerated outputs (data machine)

Steps that need local data (`viina/run_all.sh`, `build_qgis_project.py`, `make_map_previews.py`,
`30_data_package.py`, the monthly pulls) rewrite tracked outputs. These are committed with one
script, the only exception to "pull only":

```bash
git pull --ff-only                        # before running the pipeline
viina/run_all.sh                          # or the individual steps
tools/publish_outputs.sh --dry-run        # shows what would be committed; changes nothing
tools/publish_outputs.sh "refresh: data to 2026-09"   # commits and pushes after confirmation
```

The script:

1. refuses unless on `main` with a clean index and no local commits ahead of `origin/main`;
2. fast-forwards to `origin/main`;
3. stages **modified** files under the output paths only:
   `resilience/tidy/`, `resilience/public/`, `resilience/docs/fig1_carpathian_light.{png,svg}`,
   `publication/figures/`, `viina/strikes_by_month_oblast.csv`, `viina/qgis/meta.json`,
   `viina/qgis/maps/preview/`;
4. **stops** on any other change: modified code or documents, deleted files, or new files that
   are not listed in its `ALLOW_NEW` array;
5. runs `guards.sh` and the HELD map-page check on the staged state;
6. commits with a fixed message and pushes.

If it stops, nothing is committed and the index is restored: copy the output to Claude, who
fixes the cause (for example adds a new table to `ALLOW_NEW` after checking it against R1–R6,
or restores a changed script). A new tracked output therefore always passes through a
deliberate decision.

`publication/numbers.yaml` is maintained by hand: `26_publication_tables.py` and
`27_sensitivity.py` print the values; the maintainer passes the printout to Claude, who updates
the file.

The data package (`publication/data_package/out/`) is never committed; it is uploaded to Zenodo.

### When `git pull --ff-only` refuses

Stop and resolve together with Claude. Do not merge, rebase or reset on the data machine, and
never run `git clean`. Send the output of `git status` and `git log --oneline -3 origin/main`.

## Layout and how to run

- `viina/`: strike and alert pipeline, QGIS builder `build_qgis_project.py`, `run_all.sh`.
- `resilience/`: resilience layers, numbered `00_…` to `30_…`. **Run them from `resilience/`.**
  Scripts locate each other through relative paths (`BASE.parent / "viina"`); do not move folders.
- `publication/`: working paper, essay, brief and data-package sources.
  PDFs: `python publication/build/build.py --only paper` (A4, WeasyPrint; layout in
  `publication/build/aux/print.html` and `print.css`, bundled fonts in `aux/fonts/`). Output goes to
  `publication/build/out/` (not in git). Map plates: a `::: {.plate}` div around one image.
- `tools/`: `publish_outputs.sh`.

`viina/run_all.sh` rebuilds everything **from cache** (no downloads) and runs from any directory:

```bash
viina/run_all.sh                 # full rebuild
SKIP_RES=1 viina/run_all.sh      # strikes, alerts and maps only
VENV=/path/to/venv QGIS_PY=/path/to/python3 viina/run_all.sh   # other environments
```

Analysis runs in the venv (see `requirements.txt`); the map builder runs on the QGIS system
Python (`/usr/bin/python3`, QGIS 3.40, `QT_QPA_PLATFORM=offscreen`).

## Data pulls are manual

API pulls are slow, need credentials and are **not** part of `run_all.sh`. From `resilience/`:

| Source | Command |
|---|---|
| Local budgets (openbudget) | `python 03_openbudget.py pull` |
| Budgets, current year | `python 20_budget_quarterly.py pull2026` |
| Night lights, monthly (Black Marble) | `python 19_nl_monthly.py pull` |
| IOM DTM (oblast) | `python 17_dtm_api.py pull` |
| DREAM projects | `python 10_dream.py fetch` |
| ЄДРПОУ regional tables | `python 09_stat_edrpou.py --all` |
| Oblast context sources | see `16_oblast_context.py` |

Earthdata tokens expire; LAADS may return 401 mid-run. Refresh the token and rerun: pulls resume.

## Monthly refresh routine

1. `git pull --ff-only`.
2. Pull new data: `19_nl_monthly.py pull`, `20_budget_quarterly.py pull2026`, `17_dtm_api.py pull`.
3. Rebuild: `viina/run_all.sh`, and check the logs in `viina/qgis/step*.log`.
4. Review: `tools/publish_outputs.sh --dry-run`, key numbers in
   `resilience/tidy/trajectory_models.csv`, the map captions.
5. Publish: `tools/publish_outputs.sh "refresh: data to YYYY-MM"`.
6. Pass the `numbers.yaml:` printout of `26_`/`27_` to Claude if the key numbers changed.
7. Tag when results change materially: Claude creates and pushes `vX.Y-YYYYMM` on request.

## Commit messages

`area: what changed`, e.g. `resilience: add 25_damage.py`, `maps: page 21 damage × recovery`,
`refresh: data to 2026-09`, `outputs: regenerate 2026-09-26`. `main` is always rebuildable
from cache.

## Data protection and sensitivity

- Aggregated open data only. No personal data; no names of officials or volunteers.
- Nothing that locates shelters, volunteers or critical infrastructure below hromada level.
- Hromada-level night-light tables covering the most recent 12 months stay out of git until a
  publication rule (time lag or aggregation) is agreed.
- Data whose terms forbid redistribution (IOM DTM, ACLED; reSCORE pending permission) stays out.
  Include the retrieval script instead.
- Map pages listed in `HELD` (`viina/make_map_previews.py`) are never committed or attached to
  a release.

## Language

Repository text is in English. Ukrainian names of hromadas, oblasts and sources stay in UTF-8
as published (e.g. `Верховинська селищна громада`).
