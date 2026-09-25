# Ukraine hromada strikes and resilience dataset

**Version:** {{release_version}} ({{release_date}})
**DOI:** {{zenodo_doi}}
**Author:** Michel Garand, UBEC Platform
**Companion paper:** *Strikes, fiscal capacity and night-light recovery in Ukraine's hromadas, 2022–2026*, {{socarxiv_doi}}
**Licences:** data ODbL 1.0 · documentation CC BY 4.0 · code MIT (see `LICENSE.md`)

<!-- File names under data/ are proposed. Align them with actual pipeline outputs (request 32). -->

## What this is

A hromada-level dataset for Ukraine that joins three kinds of information:
- exposure to Russian strikes and air-raid alerts;
- local budget indicators;
- night-time light as a proxy for recovery.

It is complemented by oblast-level survey and displacement context. It contains the tables and boundaries behind every result in the companion paper, together with the code to rebuild them from the original sources.

All data is aggregated. The dataset contains no personal data. Some information is deliberately withheld or aggregated for security reasons (see *Security rules* below).

## Contents

```
data/
  tables/
    hromada_exposure.csv            strike and alert exposure, whole frame ({{n_hromadas_total}} units)
    hromada_indices.csv             capacity (2021, 2025), recovery ratio, engagement; percentile ranks
    hromada_budget_annual.csv       budget indicators 2021–2025, civilian income tax only
    hromada_budget_quarterly.csv    quarterly budget panel, civilian income tax only
    hromada_nightlight_monthly.csv  monthly night-light index, subject to rules R2 and R3
    hromada_trajectory_metrics.csv  trajectory metrics, subject to rule R3
    oblast_nightlight_monthly.csv   monthly index at oblast level, full period
    oblast_context.csv              reSCORE indicators and IDP figures by oblast
  geo/
    hromadas.gpkg                   hromada polygons with occupation status and key attributes
    oblasts.gpkg                    oblast polygons
docs/
  data_dictionary.csv               every variable: name, table, definition, unit, source, period
  source_catalogue.md               every source: version, access date, licence, processing notes
code/
  fetch/                            scripts that download each source
  run_all.sh                        rebuilds all tables from downloaded sources
  requirements.txt                  pinned Python packages
ATTRIBUTION.md
LICENSE.md
CITATION.cff
```

## Units, keys and projection

- **Unit:** hromada, identified by the hromada-level (k3) segment of the KATOTTH codifier. Column `k3`, a text field; keep leading zeros.
- **Frame:** {{n_hromadas_total}} units.
  - {{n_mainland_codab}} mainland hromadas from OCHA COD-AB level 3.
  - {{n_crimea_units}} settlement-based units for Crimea and Sevastopol. These are used for exposure only.
- **Occupation status:** column `occupied` (true/false). Source and reference date: [[PENDING: request 16]].
- **Projection:** GeoPackages use UA_LAEA, a Lambert Azimuthal Equal Area projection centred on Ukraine. The full CRS definition is embedded in each layer. Reproject to EPSG:4326 for web use.
- **Oblast tables** use the oblast-level KATOTTH code in column `oblast_code`.

## Coverage and missing values

| Measure | Units covered |
|---|---|
| Exposure | {{n_hromadas_total}} |
| Fiscal capacity index | {{n_capacity}} |
| Night-light recovery ratio | {{n_recovery}} |
| Engagement | {{n_engagement}} |

Indices are computed for non-occupied hromadas only. Missing values are empty cells. The reason a value is missing is given in column `missing_reason` where it applies. Codes are listed in `docs/data_dictionary.csv`.

## Key cautions

Read section 11 of the companion paper before using the data. In short:

- **Night lights are affected by more than damage.** Blackouts and lighting policy affect them. The recovery ratio is not a measure of economic recovery.
- **Strike counts reflect reporting density** as well as attacks.
- **Income tax is booked at the employer's address.** Military income tax was moved to the state budget from Q4 2023.
- **Per-capita figures use pre-war (2020) population.**
- **Survey and displacement data are oblast-level** and cannot be attributed to hromadas.
- **All associations are between places,** not individuals.

## Security rules

This dataset follows the publication rules in section 12 of the companion paper:

| Rule | Effect in this package |
|---|---|
| R1 Spatial floor | Nothing below hromada level. No night-light rasters, project points, infrastructure layers or interpolated surfaces. |
| R2 Time lag | Hromada monthly night-light values end 6 months before release. The last 12 months are available at oblast level only. |
| R3 Frontline and border zone | For hromadas within 30 km of the front line or the Russian/Belarusian border, monthly values and trajectory metrics are given at raion level. |
| R4 Military finance | No garrison flag and no military income-tax fields at hromada level. |
| R5 Strike events | Hromada counts only. VIINA event points are not republished. |
| R6 Personal data | No names, addresses or free-text fields from any source. |

If you believe any part of this dataset could put people or infrastructure at risk, contact the author at [[PENDING: contact address]] before republishing. Issues are reviewed and, where needed, a corrected version is released.

## Not included

| Item | Reason | How to obtain |
|---|---|---|
| Raw source downloads | Size, and source licence terms | `code/fetch/` |
| IOM DTM raw data | IOM terms of use | `code/fetch/dtm.py` with your own API access. Oblast aggregates are included only where the terms allow ([[PENDING: request 23]]) |
| Night-light rasters | Rule R1 | NASA LAADS DAAC, product VNP46A3 |
| VIINA event points | Rule R5 | VIINA public repository |
| Garrison flag | Rule R4 | Not released |

## Reproducing the tables

Requirements: Python 3.13; QGIS 3.40 for the maps only.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
bash code/run_all.sh
```

`run_all.sh` downloads missing sources, then rebuilds all tables. A full run takes about {{run_time}}. Results can differ slightly from this release if a source has been revised since the access dates recorded in `docs/source_catalogue.md`.

## Licences

- **Data** (`data/`): Open Database License (ODbL) 1.0. The dataset includes data derived from VIINA and OpenStreetMap, both licensed under ODbL. If you publicly use a derived database, it must also be released under ODbL. Maps, charts and papers produced from the data can carry any licence, with attribution.
- **Documentation** (`README.md`, `docs/`): CC BY 4.0.
- **Code** (`code/`): MIT.

Attribution for every source is required and is set out in `ATTRIBUTION.md`.

## How to cite

Cite both the dataset and the companion paper. The citation metadata is in `CITATION.cff`.

> Garand, M. ({{release_year}}). *Ukraine hromada strikes and resilience dataset* ({{release_version}}) [Data set]. Zenodo. {{zenodo_doi}}

## Changelog

- **{{release_version}}** ({{release_date}}): first public release.
