# Ukraine hromada strikes and resilience dataset

**Version:** {{release_version}} ({{release_date}})
**DOI:** {{zenodo_doi}}
**Author:** Michel Garand, UBEC Platform
**Companion paper:** *Strikes, fiscal capacity and night-light recovery in Ukraine's hromadas, 2022–2026*, {{socarxiv_doi}}
**Code:** https://github.com/ubeccommon/ubec_ukraine_resilience, release {{release_version}}
**Licences:** data ODbL 1.0 · documentation CC BY 4.0 · code MIT (see `LICENSE.md`)

## What this is

A hromada-level dataset for Ukraine that joins three kinds of information:
- exposure to Russian strikes and air-raid alerts;
- local budget indicators;
- night-time light as a proxy for recovery.

It contains the tables and boundaries behind the results of the companion paper. The code that rebuilds them from the original sources is in the GitHub repository, release {{release_version}}; this package does not duplicate it.

All data is aggregated. The dataset contains no personal data. Some information is deliberately withheld or aggregated for security reasons (see *Security rules* below).

## Contents
data/
tables/
hromada_exposure.csv strike and alert exposure, all units including occupied ones
hromada_indices.csv capacity (2025 and pre-war 2021), recovery, engagement; missing_reason
hromada_budget_annual.csv budget totals 2021–2025, civilian income tax only
hromada_budget_quarterly.csv quarterly budget totals from 2021, civilian income tax only
hromada_nightlight_monthly.csv monthly night-light index to {{pub_end}}, reliable units only (rules R2, R3)
hromada_trajectory_metrics.csv trajectory metrics computed on data to {{pub_end}} (rules R2, R3)
oblast_nightlight_monthly.csv monthly night-light index by oblast and nationally, full period
geo/
hromadas.gpkg layer "units" (hromadas and R3 raions), layer "frontline_border"
oblasts.gpkg oblast polygons
docs/
data_dictionary.csv every column: definition, unit, source, period, aggregation of R3 rows; codes
source_catalogue.md every source: version, access, licence, processing notes
ATTRIBUTION.md
LICENSE.md
licenses/ full licence texts
CITATION.cff
SHA256SUMS checksums of all files

## Units, keys and projection

- **Unit:** each row is a hromada (`unit_type = hromada`) or, under rule R3, a whole raion (`unit_type = raion_r3`).
- **Keys:** `k3` is the hromada-level segment of the KATOTTH codifier (text; keep leading zeros; empty for raion rows); `k2` the raion code; `k1` the oblast code.
- **Frame:** {{n_hromadas_total}} units: {{n_mainland_codab}} mainland hromadas from OCHA COD-AB level 3 and {{n_crimea_units}} settlement-based units for Crimea and Sevastopol, used for exposure only.
- **Occupation status:** column `occupied` (1/0), from VIINA territorial control on {{control_date}}: a unit is occupied if at least half of its population-weighted places are held by Russia or contested. Crimea and Sevastopol are always occupied.
- **Projection:** GeoPackages use UA_LAEA, a Lambert Azimuthal Equal Area projection centred on Ukraine. The full CRS definition is embedded in each layer. Reproject to EPSG:4326 for web use.

## Coverage and missing values

| Measure | Hromadas covered in the paper's frame |
|---|---|
| Exposure | {{n_hromadas_total}} |
| Fiscal capacity index | {{n_capacity}} |
| Night-light recovery ratio | {{n_recovery}} |
| Engagement | {{n_engagement}} |
| Reliable monthly night lights (rule R2) | {{n_light_reliable}} |

Under rule R3, {{n_r3_hromadas}} hromadas in {{n_r3_raions}} raions appear in this package only as raion rows. The tables therefore have {{n_package_units}} unit rows. Indices are computed for non-occupied hromadas only. Missing values are empty cells; column `missing_reason` gives the reason where it applies. Codes are listed in `docs/data_dictionary.csv`.

## Key cautions

Read section 11 of the companion paper before using the data. In short:

- **Night lights are affected by more than damage.** Blackouts and lighting policy affect them. The recovery ratio is not a measure of economic recovery.
- **Strike counts reflect reporting density** as well as attacks.
- **Income tax is booked at the employer's address.** Military income tax was moved to the state budget from Q4 2023.
- **Per-capita figures use pre-war (2020) population.**
- **All associations are between places,** not individuals.
- **Raion rows are not comparable to hromada rows in size.** Use rates and indices, not totals, when comparing them.

## Security rules

This dataset follows the publication rules in section 12 of the companion paper:

| Rule | Effect in this package |
|---|---|
| R1 Spatial floor | Nothing below hromada level. No night-light rasters, project points, infrastructure layers or interpolated surfaces. |
| R2 Time lag | Hromada monthly night-light values end in {{pub_end}}, at least 6 months before release, and are given only for hromadas with reliable light data (at least 30 lit pixels, pre-war month-to-month noise at most 0.35). Trajectory metrics are computed on data to {{pub_end}}. The latest months are available at oblast level only. |
| R3 Frontline and border zone | Every raion with a hromada within 30 km of the front line or of the border with Russia or Belarus is given as one raion row in all tables; none of its hromadas appear individually. Aggregating only the part within 30 km would let values of single hromadas be recovered by subtraction. |
| R4 Military finance | No garrison flag and no military income-tax fields. Revenue and own funds exclude military income tax. |
| R5 Strike events | Counts per unit only. VIINA event points and event dates are not republished. |
| R6 Personal data | No personal names, addresses or free-text fields from any source. |

If you believe any part of this dataset could put people or infrastructure at risk, contact the author at [[PENDING: contact address]] before republishing. Issues are reviewed and, where needed, a corrected version is released.

## Not included

| Item | Reason | How to obtain |
|---|---|---|
| Raw source downloads | Size, and source licence terms | Fetch scripts in the repository |
| Oblast survey and displacement context (reSCORE, IOM DTM) | Source terms do not allow redistribution | Repository scripts `16_oblast_context.py`, `17_dtm_api.py`, with your own access |
| Night-light rasters | Rule R1 | NASA LAADS DAAC, product VNP46A3 |
| VIINA event points | Rule R5 | VIINA public repository |
| Garrison flag | Rule R4 | Not released |

## Reproducing the tables

Requirements: Python 3.13; QGIS 3.40 for the maps only. From a clone of the repository at release {{release_version}}:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash viina/run_all.sh
python resilience/30_data_package.py
```

Source downloads are separate steps, listed in `CONTRIBUTING.md`. A full rebuild from cached sources takes about {{run_time}}. Results can differ slightly from this release if a source has been revised since the access dates in `docs/source_catalogue.md`.

## Licences

- **Data** (`data/`): Open Database License (ODbL) 1.0. The dataset includes data derived from VIINA, licensed under ODbL. If you publicly use a derived database, it must also be released under ODbL. Maps, charts and papers produced from the data can carry any licence, with attribution.
- **Documentation** (`README.md`, `docs/`): CC BY 4.0.
- **Code** (in the repository): MIT.

Attribution for every source is required and is set out in `ATTRIBUTION.md`.

## How to cite

Cite both the dataset and the companion paper. The citation metadata is in `CITATION.cff`.

> Garand, M. ({{release_year}}). *Ukraine hromada strikes and resilience dataset* ({{release_version}}) [Data set]. Zenodo. {{zenodo_doi}}

## Changelog

- **{{release_version}}** ({{release_date}}): first public release.
