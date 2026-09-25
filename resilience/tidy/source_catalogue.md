# Resilience data — source catalogue

Status as of 24 September 2026. Companion to `data_dictionary.csv` (indicator definitions) in the same folder.
Join keys: `k3` = 7-digit KATOTTH hromada code, `k2` raion, `k1` oblast. Non-occupied hromadas: 1,290.

## 1. Used — national coverage

| Source | Access | Level / key | Period | Coverage | Licence / attribution |
|---|---|---|---|---|---|
| Local budgets, openbudget.gov.ua (MinFin / Treasury) | `api.openbudget.gov.ua/api/public/localBudgetData`; budget list with KATOTTG via `openbudget.gov.ua/api/localBudgets/aboutBudgets/plain/CSV` | hromada; budget code → `k3` via KATOTTG (2021 list has no KATOTTG → matched by name) | incomes 2021, 2025; expenses 2023–2025 | 1,289 / 1,290 | Ukrainian open data, CMU Res. 835 — attribution |
| GHS-POP R2023A, JRC | 100 m Mollweide tiles, jeodpp.jrc.ec.europa.eu | zonal sum on COD polygons | epoch 2020 (denominator), 2025 | all hromadas | EC reuse notice — attribution |
| COD-AB Ukraine, OCHA / SSPE Kartographia | HDX `cod-ab-ukr` (shapefile) | ADM3 P-code = `"UA" + k3` | Jan 2025 | 1,757 / 1,763 match (differences in Crimea only) | CC BY-IGO. Also replaces the settlement tessellation in `viina/qgis/admin_units.gpkg` |
| Black Marble VNP46A3, NASA | LAADS Collection 2 (`allData/5200`), Earthdata token; Collection 5000 is gone | zonal mean over pixels lit in 2021 (≥ 1 nW/cm²/sr) | Dec 2020 – Feb 2025, monthly | 1,352 hromadas with ≥ 10 lit pixels | public domain — cite NASA Black Marble |
| DREAM recovery projects | `public-api.dream.gov.ua/marketplace/public/dream/ideas[/{id}]` | KATOTTG in project locations → `k3` | 2023–2026 | 16,172 projects; 10,541 valid with a hromada location, 25 % valid without location | public open data — attribute DREAM |
| Strikes (VIINA) and air-raid alerts | existing `viina` pipeline | hromada | see `viina/qgis/meta.json` | exposure side | VIINA ODbL; alerts MIT |

## 2. Used — oblast or regional only

| Source | Access | Level | Period | Notes |
|---|---|---|---|---|
| reSCORE / SCORE Ukraine (SeeD, UNDP), General Population | `api.scoreforpeace.org/api/viz/map?language=en&country_id=ukraine&type=score&year=<Y>&data_stream=1&auth_key=` | oblast + Kyiv city | 2024 (n = 7,758), 2021 (n = 12,482) | excludes Donetsk, Luhansk, Crimea; differences < 0.5 not significant; city boosters (Kharkiv, Odesa, Zaporizhzhia, Dnipro, Kryvyi Rih) kept out of oblast values; aggregated scores only |
| IOM DTM (HDX `ukr-iom-dtm-from-api`) | CSV, admin 0–1 | oblast | IDPs present 31 Mar 2026 (21 oblasts); registered 31 Jul 2026 (24 oblasts, summed over origin) | present ≠ registered (e.g. Dnipropetrovsk 194 vs 134 per 1,000); admin-2 column empty |
| Regional statistics offices, ЄДРПОУ counts by hromada | HTML tables, 10 office sites (`09_stat_edrpou.py`) | hromada, 10 oblasts | 2022 – Jul 2026 (varies) | legal entities 41 %, sole proprietors 33 % of non-occupied hromadas → regional supplement, not in any index. Zhytomyr withholds legal-entity tables, Chernivtsi all tables (martial law); Poltava publishes oblast totals only |

## 3. Checked — not openly available

| Source | What was found | Consequence |
|---|---|---|
| EDR bulk dump, Ministry of Justice (data.gov.ua, CC BY) | legal-entity XML has no address or location field; FOP file is personal data | no hromada counts from EDR; FOP never downloaded, `uo.zip` deleted |
| IOM DTM Area Baseline, raion level | HDX dataset and Round 39 resource return 404; dtm.iom.int round pages (36–46) have no XLSX; hromada file is request-only | registered IDPs below oblast level not available; request from IOM if needed |
| Digital Transformation Index, Mintsyfra (hromada.gov.ua) | public API (`backend.hromada.gov.ua/api/front`) gives hromada list, KATOTTG `code_3`, population, status — no scores; per-hromada scores require login; oblast index only (e.g. Vinnytsia 54) | dropped from national set; API returns names of hromada heads / digital leaders — not stored, probe cache deleted |
| Financial-capacity rating 2025 (decentralization.gov.ua) | 5 PDFs, 1,331 hromadas, names only | not used; comparable indicators recomputed from openbudget |
| HeRAMS (WHO) | facility data withheld for security; oblast reports only | not used |
| School operating mode (MON) | national totals only | not used; shelter locations deliberately not sought |

## 4. Not pursued (candidates for later)

- ETH Zurich Sentinel-1 building damage, ADM3 (Zenodo) — impact rather than capacity; possible covariate.
- REACH MSNA 2024–2025 microdata (oblast strata); IOM General Population Survey (macro-region).
- OCHA 3W/5W and HNRP severity (raion); Prozorro civil-protection procurement.
- reSCORE hromada stream (2023, 32 hromadas); reSCORE 2023 round and SHARP rounds.
- KIIS, Rating, Razumkov — sub-national breakdowns not verified.

## Standing caveats

- Per-capita values use pre-war GHS-POP 2020: inflated where people left, deflated in IDP-host hromadas.
- PIT is booked at the employer's address; military PIT left local budgets from late 2023 (garrison flag from 2021).
- Night-light radiance reflects blackout schedules and lighting policy as well as activity, and follows oblast-wide grid conditions.
- DREAM counts reflect planning capacity, donor attention and damage together.
- Occupied and frontline areas are excluded or under-covered in every source.

## IOM DTM API v3 (checked 2026-09-25)

- Subscription via dtm-apim-portal.iom.int (key in ~/.dtm_key). Script `17_dtm_api.py probe / pull / tidy`.
- Served for Ukraine: Admin 0 and Admin 1 only. Admin 2 returns "No Country found"; Admin 3 not in the API.
- Two operations, never summed together:
  - Registration (MoSP register): monthly Feb 2022 – Aug 2026, host oblast × origin oblast → `tidy/dtm_oblast_od_k1.csv`. Registered location, not residence; deregistration lags; western oblasts overstated vs survey by ~40–75 %.
  - General Population Survey (IDPs present): 7 rounds Aug 2024 – Mar 2026; no values for Donetsk, Zaporizhzhia, Kherson, Luhansk.
- Outputs: `tidy/dtm_oblast_month_k1.csv`, `tidy/dtm_oblast_od_k1.csv`, `tidy/dtm_oblast_latest_k1.csv`.
- Oblast-level IDP variables are collinear with oblast fixed effects → usable only in M1 or as context.
- Hromada (ADM3) / raion (ADM2) file: requested from IOM on 2026-09-25 (status: pending). Join ready: `18_dtm_hromada.py join FILE` (tested with `selftest`). Denominator GHS-POP 2020 (pre-war).
- Licence: IOM DTM terms of use; cite "IOM DTM API, accessed <date>".
