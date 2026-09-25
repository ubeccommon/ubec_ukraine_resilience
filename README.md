# Ukraine strikes × hromada resilience

A reproducible spatial-analysis pipeline linking Russian strikes and air-raid alerts in Ukraine to
the capacity and recovery of Ukraine's 1,763 hromadas (territorial communities), 2022–2026.
It combines open data on strikes, alerts, local budgets, population, displacement and monthly
night-time lights, and builds a 20-page QGIS map atlas.

**Author:** Michel Garand, UBEC Platform · **Status:** v1.1, step 2 (time dimension) ·
**Licences:** code MIT · data ODbL 1.0 · docs and figures CC BY 4.0 (see [`LICENSES.md`](LICENSES.md))

> Aggregated open data only. Nothing below hromada level, no personal data, and no layers that
> locate shelters, volunteers or critical infrastructure. See [Security rules](#security-rules).

## Pipeline

```
strikes + alerts (VIINA, alert records)          viina/
        │  exposure per hromada, surfaces, hot spots
        ▼
resilience v1.1 (budgets, population, lights)    resilience/00–13
        │  capacity, recovery, engagement indices; robustness models
        ▼
oblast context (reSCORE, IOM DTM)                resilience/16–18
        ▼
time dimension                                    resilience/19–22
        │  monthly night lights 2020–2026, quarterly budgets 2021–2026, trajectories
        ▼
Carpathian deep dive                              resilience/23–24
        ▼
QGIS project + 20 map pages                       viina/build_qgis_project.py
```

| Folder | Contents |
|---|---|
| `viina/` | strike and alert pipeline, exposure surfaces and hot spots, QGIS builder, `run_all.sh` |
| `resilience/` | scripts `00_…` to `24_…`, `styles/` (QGIS styles), `docs/` (results notes, Carpathian brief), `tidy/` (derived tables, data dictionary, source catalogue) |
| `publication/` | sources of the working paper, essay, brief, dispatch and data package |

Main scripts in `resilience/`:

| Script | Output |
|---|---|
| `00_units_cod.py` | hromada polygons from OCHA COD-AB keyed to `k3` |
| `03_openbudget.py` | local budget indicators (openbudget.gov.ua) |
| `04_nightlights.py` | Black Marble zonal statistics and v1.1 light ratios |
| `05_population.py` | GHS-POP 2020/2025 per hromada |
| `06_assemble.py`, `11_composite.py` | `resilience_v1_k3.csv`, v1.1 indices |
| `12_moderation.py`, `13_bivariate.py` | robustness models M1–M7, bivariate map layers |
| `16_oblast_context.py`, `17_dtm_api.py`, `18_dtm_hromada.py` | oblast survey and displacement context |
| `19_nl_monthly.py` | monthly night-light panel, Jan 2020 – Aug 2026 |
| `20_budget_quarterly.py` | quarterly budget flows, 2021 Q1 – 2026 Q2 |
| `22_trajectories.py` | trajectory metrics, models and map classes |
| `23_carpathian.py`, `24_carpathian_chart.py` | Carpathian profiles and Figure 1 |

Keys: `k1` oblast (2 digits), `k2` raion (4), `k3` hromada (7 digits of KATOTTH; e.g. `2602003`
Verkhovyna). Keep them as text to preserve leading zeros. Analysis projection is UA_LAEA
(`+proj=laea +lat_0=48.5 +lon_0=31 +ellps=GRS80 +units=m`); the QGIS project uses EPSG:3857.

## Quick start

Requirements: Linux, Python 3.13, QGIS 3.40 (maps only), about 45 GB of disk for raw data.

```bash
git clone https://github.com/ubeccommon/ubec_ukraine_resilience.git
cd ubec_ukraine_resilience
python3.13 -m venv ~/Documents/GEODATA/.venv        # or any path; pass it as VENV=…
. ~/Documents/GEODATA/.venv/bin/activate
pip install -r requirements.txt
```

A fresh clone contains code and small tables but **no raw data**, so `run_all.sh` needs the
inputs below first. Once they are in place:

```bash
viina/run_all.sh                     # full rebuild from local data (no downloads)
SKIP_RES=1 viina/run_all.sh          # strikes, alerts and maps only
VENV=/path/to/venv QGIS_PY=/usr/bin/python3 viina/run_all.sh
```

Analysis runs in the venv. The map builder runs on the QGIS system Python (`/usr/bin/python3`)
with `QT_QPA_PLATFORM=offscreen`.

## Obtaining the raw data

Downloads are manual: they are slow, some need credentials, and none is part of `run_all.sh`.
Credentials are read from the home directory and are never stored in the repository.

| Input | Where it goes | How |
|---|---|---|
| VIINA 2.0 event and control archives (`event_*_latest_YYYY.zip`, `control_latest_YYYY.zip`), tessellations | `viina/` | VIINA repository (see `DATA_SOURCES.md`) |
| KATOTTG codifier `katottg.csv` | `viina/` | data.gov.ua |
| Air-raid alert records (`official_data_*.csv`, `volunteer_data_*.csv`) | `air_raid/` | alert dataset repository |
| OCHA COD-AB Ukraine | `resilience/raw/cod_ab/` | HDX `cod-ab-ukr` |
| JRC GHS-POP R2023A, 100 m tiles | `resilience/raw/ghs_pop/` | JRC GHSL download |
| Local budgets | `resilience/raw/openbudget/` | `python 03_openbudget.py pull`, `python 20_budget_quarterly.py pull2026` |
| NASA Black Marble VNP46A3 (about 36 GB) | `resilience/raw/nightlights/` | `python 19_nl_monthly.py pull` (token in `~/.earthdata_token`) |
| DREAM projects | `resilience/raw/dream/` | `python 10_dream.py fetch` |
| ЄДРПОУ regional tables | `resilience/raw/stat_edrpou/` | `python 09_stat_edrpou.py --all` |
| reSCORE oblast scores | `resilience/raw/rescore/` | `16_oblast_context.py` |
| IOM DTM (oblast) | `resilience/raw/dtm_api/` | `python 17_dtm_api.py pull` (key in `~/.dtm_key`) |

Run the Python pulls from `resilience/`. Earthdata tokens expire; if LAADS returns 401 mid-run,
refresh the token and rerun, and the pull resumes. Source details, access dates and licences are
in [`DATA_SOURCES.md`](DATA_SOURCES.md) and
[`resilience/tidy/source_catalogue.md`](resilience/tidy/source_catalogue.md).

## What is and is not in this repository

**Included:** all pipeline code; QGIS styles; the data dictionary and source catalogue; derived
hromada and oblast tables up to 5 MB; results notes; publication sources.

**Not included:**

| Item | Reason |
|---|---|
| Raw downloads (about 40 GB), caches, GeoPackages, rasters, map PDFs | size; rebuilt by the pipeline or published on Zenodo |
| Monthly and quarterly hromada night-light tables, trajectory metrics | security rule R2 (time lag); released on Zenodo under that rule |
| Tables with military finance fields at hromada level | security rule R4 |
| IOM DTM derived tables | DTM terms forbid redistribution and derivative works |
| reSCORE derived tables | no licence found; pending permission from SeeD |
| ACLED exports, third-party reports | terms of the provider |
| Any hromada/raion displacement file shared by IOM | data-sharing terms |

## Key results (v1.1, step 2)

Working-paper figures; subject to revision. Associations are between places, not individuals.

- **Capacity and exposure are nearly independent** (ρ 0.07–0.18). The "buffering" interaction
  between capacity and exposure disappears once oblast fixed effects are included; oblast
  effects lift R² from 0.11 to 0.57.
- **National night-light trajectory** (median index, 2020–21 = 1): 0.05 in March 2022, 0.40 in
  H2 2023, 0.10–0.11 in the summer-2024 outages, and 0.37 over Sep 2025 – Aug 2026, flat since
  late 2024. Since H2 2023, 37 % of hromadas declined, 51 % were stable and 12 % improved.
- **Summer-2024 outage loss** is the most robust capacity result: within oblasts, higher
  capacity means a smaller loss (+0.20 SD, t 6.3; pre-war capacity +0.13, t 3.6).
- **Recent light level** is dominated by alert exposure (−0.55 SD, t −8.6). Its association with
  capacity (+0.19–0.22) is partly reverse-causal (pre-war capacity only +0.09).
- **Carpathian oblasts** kept a recent light level of 0.62 against 0.30 elsewhere, and fell below
  half of pre-war light in 39 % of quarters against 94 %. Civilian income tax there peaked in
  2022 Q2–Q3, consistent with westward relocation.
- **Displacement:** registered IDPs exceed IDPs present by about 40–75 % in the west and the
  reverse holds in the centre and east (oblast level only).

**Caveats:** night lights reflect blackouts, lighting policy and a pre-war upward trend as well as
activity; strike counts reflect reporting density; income tax is booked at the employer's
address and military income tax left local budgets from Q4 2023; per-capita values use the
pre-war 2020 population; occupied and frontline areas are under-covered; ecological inference
applies throughout.

## Security rules

The repository follows the publication rules of the companion paper:

| Rule | Effect |
|---|---|
| R1 Spatial floor | Nothing below hromada level: no night-light rasters, project points, infrastructure layers or interpolated surfaces. |
| R2 Time lag | Hromada monthly night-light values are published only with a lag; the last 12 months at oblast level only. |
| R3 Frontline and border zone | Monthly values and trajectory metrics near the front line or border are aggregated to raion level. |
| R4 Military finance | No garrison flag and no military income-tax fields at hromada level. |
| R5 Strike events | Hromada counts only; VIINA event points are not republished. |
| R6 Personal data | No names, addresses or free-text fields from any source. |

If you believe anything here could put people or infrastructure at risk, open a private
security advisory on GitHub or contact the author before republishing.

## Licences and citation

Code is MIT ([`LICENSE`](LICENSE)); derived tables are ODbL 1.0
([`LICENSE-ODbL-1.0.txt`](LICENSE-ODbL-1.0.txt)), because several derive from VIINA and
OpenStreetMap; documentation and figures are CC BY 4.0
([`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt)). Upstream sources keep their own terms and
attribution requirements ([`DATA_SOURCES.md`](DATA_SOURCES.md)).

Citation metadata is in [`CITATION.cff`](CITATION.cff); GitHub shows it under "Cite this
repository". A Zenodo DOI will be added with the first release.

> Garand, M. (2026). *Ukraine strikes × hromada resilience: analysis pipeline* (v1.1-step2)
> [Software]. https://github.com/ubeccommon/ubec_ukraine_resilience

Working conventions, the monthly refresh routine and the branch convention are in
[`CONTRIBUTING.md`](CONTRIBUTING.md).
