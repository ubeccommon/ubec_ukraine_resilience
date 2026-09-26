# Data sources and attribution

Every source used by the pipeline, its terms, and whether anything derived from it is in this
repository. Detailed access notes, periods and coverage are in
[`resilience/tidy/source_catalogue.md`](resilience/tidy/source_catalogue.md); every variable is
defined in [`resilience/tidy/data_dictionary.csv`](resilience/tidy/data_dictionary.csv).

Raw downloads are **not** in the repository (about 40 GB, and some terms forbid redistribution).
The scripts that retrieve each source are included.

## Short attribution line for maps and figures

> Data: VIINA 2.0, Zhukov & Ayers (ODbL); air-raid alert records, V. Klymenko (MIT); OCHA COD-AB / SSPE
> Kartographia (CC BY-IGO); openbudget.gov.ua; NASA Black Marble; JRC GHS-POP; DREAM;
> © OpenStreetMap contributors (ODbL). Analysis: M. Garand, UBEC Platform, CC BY 4.0.

Name only the sources actually used in a given map. Maps that show oblast context (page 18) also
credit *IOM DTM* and *SeeD–UNDP reSCORE Ukraine*.

## Overview

| Source | Used for | Level | Terms | Derived tables in repo? | How to obtain |
|---|---|---|---|---|---|
| VIINA 2.0 (Zhukov) | strike events, control areas | event → hromada | ODbL 1.0 | yes (counts only) | VIINA repository → `viina/` |
| Air-raid alerts (Klymenko) | alert hours | oblast / hromada | MIT | yes (aggregates) | GitHub dataset → `air_raid/` |
| OCHA COD-AB Ukraine | hromada, raion, oblast polygons | ADM1–3 | CC BY-IGO | keys only (no geometry) | HDX `cod-ab-ukr` → `resilience/raw/cod_ab/` |
| KATOTTG codifier | unit keys, names | hromada | UA open data | yes (keys) | data.gov.ua → `viina/katottg.csv` |
| openbudget.gov.ua | local budget indicators | hromada | CMU Res. 835 | yes (annual; quarterly via Zenodo) | `03_openbudget.py pull`, `20_budget_quarterly.py pull2026` |
| NASA Black Marble VNP46A3 C2 | night-light indices | hromada | public domain | older windows only | `04_nightlights.py pull`, `19_nl_monthly.py pull` |
| JRC GHS-POP R2023A | population denominators | hromada | EC reuse (CC BY 4.0) | yes | JRC download → `resilience/raw/ghs_pop/` |
| DREAM | reconstruction project counts | hromada | open data, no licence stated | yes (counts only) | `10_dream.py fetch` |
| State statistics offices (ЄДРПОУ) | enterprise counts, 10 oblasts | hromada | official statistics | yes | `09_stat_edrpou.py --all` |
| SeeD–UNDP SCORE / reSCORE | oblast survey context | oblast | no licence found | **no** (pending permission) | `16_oblast_context.py` |
| IOM DTM API v3 | displacement context | oblast | no redistribution | **no** | `17_dtm_api.py pull` with own key |
| OpenStreetMap | reference layers | — | ODbL 1.0 | no | Geofabrik / OSM |

## Sources in detail

### VIINA 2.0: strike events and control areas
VIINA data are made available under the Open Database License (ODbL) 1.0; rights in individual
contents are licensed under the Database Contents License. Citation requested by the authors:

> Zhukov, Yuri and Natalie Ayers (2023). "VIINA 2.0: Violent Incident Information from News
> Articles on the 2022 Russian Invasion of Ukraine." Cambridge, MA: Harvard University.
> (https://github.com/zhukovyuri/VIINA, accessed [DATE]).

Any redistribution of the data or of works produced from it must include a copy of the ODbL
(`LICENSE-ODbL-1.0.txt`) and keep these notices. Data dates for each build are in
`viina/qgis/meta.json`. Only hromada and oblast counts are republished; event points are not
(security rule R5).

### Air-raid alert records
Air Raid Datasets, Vadym Klymenko, https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset
(official and volunteer alert records by oblast and hromada). MIT License,
"Copyright (c) 2022 Vadym Klymenko"; the copyright and permission notice must be kept with any
redistribution of the raw files.

*Data note:* the official records stop on 7 September 2026. The likely cause is the change of
Ukraine's alert system on 6 September 2026, which introduced yellow and red alert levels; the
volunteer records (oblast level only) continue. Alert windows ending after 7 September 2026 need
a revised method before use.

### OCHA COD-AB: administrative boundaries
Ukraine subnational administrative boundaries, UN OCHA via the Humanitarian Data Exchange
(`cod-ab-ukr`, January 2025). Boundaries originate from SSPE Kartographia. CC BY-IGO.
ADM3 P-code = `"UA" + k3`; 1,757 of 1,763 units match (differences in Crimea only).

### openbudget.gov.ua: local budgets
Local budget execution data, Ministry of Finance of Ukraine / State Treasury, via
`api.openbudget.gov.ua/api/public/localBudgetData` (period = MONTH, year-to-date cumulative).
Open data under Cabinet of Ministers of Ukraine Resolution No. 835 (21 October 2015).
Attribution required.

### NASA Black Marble: night lights
NASA Black Marble VNP46A3 monthly night-time lights, Collection 2, from LAADS DAAC
(`allData/5200`). NASA data is not copyrighted; acknowledgement is requested.
NASA VIIRS Land Science Investigator-led Processing System (2025). *VIIRS/NPP Lunar
BRDF-Adjusted Nighttime Lights Monthly L3 Global 15 arc second Linear Lat Lon Grid* (VNP46A3,
V2). LAADS DAAC. https://doi.org/10.5067/VIIRS/VNP46A3.002.
Román, M. O., et al. (2018). NASA's Black Marble nighttime lights product suite.
*Remote Sensing of Environment*, 210, 113–143. Download requires a NASA Earthdata token
(`~/.earthdata_token`).

### JRC GHS-POP: population
GHS-POP R2023A, 100 m, European Commission, Joint Research Centre,
doi:10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE. Reuse authorised under the Commission's reuse
policy with acknowledgement. Epoch 2020 is the per-capita denominator; 2025 is used for change.

### DREAM: reconstruction projects
Digital Restoration Ecosystem for Accountable Management (DREAM), State Agency for Restoration
and Development of Infrastructure of Ukraine; public API `public-api.dream.gov.ua`
(documentation: https://open-contracting.github.io/dream-api-docs/). DREAM data are announced
as open data published to the Open Contracting Data Standard, but no licence is stated on the
readable portal pages or in the API responses (checked September 2026). Only project counts per
hromada are republished here, with attribution: "Source: DREAM, dream.gov.ua, accessed <date>".
No record-level fields are included.
*Pending: confirmation of reuse terms from the DREAM project office.*

### Regional statistics offices: ЄДРПОУ counts
Enterprise-register tables published by regional offices of the State Statistics Service
(10 oblasts). Regional supplement only; not used in any index. Several offices withhold
tables under martial law.

### SeeD–UNDP SCORE / reSCORE Ukraine: survey context
SCORE Ukraine 2021 and reSCORE Ukraine 2024, Center for Sustainable Peace and Democratic
Development (SeeD) and UNDP, public dashboard `api.scoreforpeace.org`. Oblast-level aggregated
scores only. No explicit licence was found, so derived tables (`rescore_long.csv`,
`oblast_context_k1.csv`) are **not** in this repository. Values may be cited with attribution.
*To confirm: redistribution permission from SeeD.*

### IOM DTM: displacement
International Organization for Migration, Displacement Tracking Matrix, DTM API v3
(Admin 0–1 for Ukraine). The DTM terms of use permit viewing, downloading and printing for
non-commercial use only, with no right to redistribute or create derivative works, and require
crediting DTM as the source. Derived tables (`dtm_oblast_*.csv`, `oblast_context_k1.csv`) are
therefore **not** in this repository. Regenerate them with `resilience/17_dtm_api.py pull` and
`tidy` using your own API subscription (key in `~/.dtm_key`). Cite as "IOM DTM API, accessed
<date>". The hromada/raion file requested from IOM is covered by its own data-sharing terms and
will never be committed.

### OpenStreetMap
© OpenStreetMap contributors, Open Database License 1.0,
https://www.openstreetmap.org/copyright.

## Excluded third-party material

- **ACLED** exports (`acled/`): ACLED terms do not allow redistribution.
- Third-party reports and PDFs kept for reference in the working tree.

## Standing caveats

- Per-capita values use pre-war GHS-POP 2020: inflated where people left, deflated in IDP hosts.
- Personal income tax is booked at the employer's address; military PIT left local budgets from
  Q4 2023.
- Night-light radiance reflects blackout schedules, lighting policy and a pre-war upward trend
  (2021 about 24 % brighter than 2020), not only activity.
- Strike counts reflect reporting density as well as attacks.
- DREAM counts reflect planning capacity, donor attention and damage together.
- Survey and displacement data are oblast-level and cannot be attributed to hromadas.
- Occupied and frontline areas are excluded or under-covered in every source.
