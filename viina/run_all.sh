#!/usr/bin/env bash
# Rebuild the whole pipeline: data (venv) -> resilience layers (venv) -> QGIS project + maps (system python).
# Resilience steps use cached raw data only (no API pulls); skip them with  SKIP_RES=1 ./run_all.sh
# Runs from any directory. Overrides:  VENV=/path/to/venv   QGIS_PY=/path/to/qgis/python3
# Fresh source data is pulled by hand (slow, needs tokens in ~/.earthdata_token and ~/.dtm_key), from resilience/:
#   03_openbudget.py pull | 04_nightlights.py pull | 19_nl_monthly.py pull | 20_budget_quarterly.py pull2026
#   17_dtm_api.py pull | 10_dream.py fetch | 09_stat_edrpou.py --all | sources of 16_oblast_context.py
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
VENV="${VENV:-$HOME/Documents/GEODATA/.venv}"
QGIS_PY="${QGIS_PY:-/usr/bin/python3}"
if [[ ! -f "$VENV/bin/activate" ]]; then
  echo "venv not found: $VENV  (set VENV=/path/to/venv)" >&2; exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python prep_qgis_layers.py        | tee qgis/step0.log   # events, control filter, H3, pickles
python build_admin_centres.py     | tee qgis/step1.log   # oblast/raion/hromada polygons (COD-AB) + centres
python match_alert_units.py       | tee qgis/step2a.log  # alert names -> KATOTTH keys
python build_unit_stats.py        | tee qgis/step2b.log  # strikes + alerts per unit
python build_surfaces.py          | tee qgis/step3.log   # IDW / kriging rasters + isolines, control mask
python build_hotspots.py          | tee qgis/step4.log   # KDE, Gi*, LISA, Moran
python build_kde_west.py                                  # 1 km KDE for the Carpathian zoom
python export_fgb.py                                      # single-layer copies for QGIS
python write_meta.py                                      # data dates for the map captions

if [[ "${SKIP_RES:-0}" != "1" ]]; then
  (
    cd ../resilience
    python 00_units_cod.py                               # COD-AB hromada polygons keyed to k3
    python 03_openbudget.py indicators                   # budget indicators from cached API responses
    python 05_population.py                              # GHS-POP per hromada (cached tiles)
    python 04_nightlights.py zonal                       # lit-pixel zonal stats (cached tiles + month cache)
    python 04_nightlights.py indicators
    python 10_dream.py aggregate                         # DREAM projects per hromada (cached JSON)
    python 06_assemble.py                                # tidy/resilience_v1_k3.csv + dictionary
    python 11_composite.py                               # capacity / recovery / engagement indices
    python 12_moderation.py                              # robustness models (captions of maps 14–16)
    python 13_bivariate.py                               # resilience_maps.gpkg for maps 14–17
    python 16_oblast_context.py                          # oblast context: reSCORE + IDPs (map 18)
    python 17_dtm_api.py tidy                            # DTM oblast tables from cache (pull is manual)
    python 19_nl_monthly.py zonal                        # monthly night-light panel from cache (pull is manual)
    python 20_budget_quarterly.py                        # quarterly budgets from cache (pull2026 is manual)
    python 22_trajectories.py                            # trajectory metrics + models
    python 23_carpathian.py                              # Carpathian profiles + series (docs/carpathian_profiles.xlsx)
    python 24_carpathian_chart.py                        # Figure 1 of the Carpathian brief (docs/fig1_*.png/svg)
    python 25_public_tables.py                           # public copies without R4 fields (public/*.csv)
    python 28_frontline_zone.py                        # R3 front-line and border zone (request 31)
    python 29_r3_aggregate.py                          # R3 raion values in the zone (maps 14–16, 19–20)
    python 26_publication_tables.py                      # paper tables (publication/figures/table*.csv/md)
    python 27_sensitivity.py                            # Table 8 sensitivity (runs 12 variants)
  ) 2>&1 | tee qgis/step_res.log
else
  echo "SKIP_RES=1 — resilience layers not rebuilt (maps 14–17 use the existing resilience_maps.gpkg)"
fi

deactivate
"$QGIS_PY" build_qgis_project.py 2>&1 | grep -v "PNG driver does not support update" | tee qgis/step5.log
