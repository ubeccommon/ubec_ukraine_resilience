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

## Layout and how to run

- `viina/`: strike and alert pipeline, QGIS builder `build_qgis_project.py`, `run_all.sh`.
- `resilience/`: resilience layers, numbered `00_…` to `24_…`. **Run them from `resilience/`.**
  Scripts locate each other through relative paths (`BASE.parent / "viina"`); do not move folders.
- `publication/`: working paper, essay, brief and data-package sources.

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

1. Pull new data: `19_nl_monthly.py pull`, `20_budget_quarterly.py pull2026`, `17_dtm_api.py pull`.
2. Rebuild: `viina/run_all.sh`, and check the logs in `viina/qgis/step*.log`.
3. Review: key numbers in `resilience/tidy/trajectory_models.csv`, the map captions, and
   `git diff --stat`.
4. Commit tidy outputs and docs: `git add -n .`, then `git add -A`, then
   `git commit -m "refresh: data to YYYY-MM"`.
5. Tag when results change materially: `git tag -a vX.Y-YYYYMM -m "…"` and `git push --tags`.

## Branches and commits

- `main` is always rebuildable from cache.
- New analysis steps go on `step/<number>-<short-name>` (e.g. `step/25-damage-covariate`).
  Merge into `main` when the step runs inside `run_all.sh` and its maps build.
- Commit messages: `area: what changed`, e.g. `resilience: add 25_damage.py`,
  `maps: page 21 damage × recovery`, `refresh: data to 2026-09`.

## Data protection and sensitivity

- Aggregated open data only. No personal data; no names of officials or volunteers.
- Nothing that locates shelters, volunteers or critical infrastructure below hromada level.
- Hromada-level night-light tables covering the most recent 12 months stay out of git until a
  publication rule (time lag or aggregation) is agreed.
- Data whose terms forbid redistribution (IOM DTM, ACLED; reSCORE pending permission) stays out.
  Include the retrieval script instead.

## Language

Repository text is in English. Ukrainian names of hromadas, oblasts and sources stay in UTF-8
as published (e.g. `Верховинська селищна громада`).
