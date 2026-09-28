# Resilience in the light of social threefolding — framework proposal

Status: 26 Sep 2026. Decided: threefolding enters the paper now as its frame (Option A, paper v0.4, section 1.4);
the three-sphere analysis with new data follows as the next version (Option B, paper v0.5). The municipal budget
is split between spheres (section 2). The indicator list per sphere is agreed (section 6). Sphere indices
are computed (step 5, 28 Sep 2026: `32_sphere_indices.py`, `tidy/sphere_indices_k3.csv`); maps, associations
and the explanatory inquiry follow.

## 1. The frame

Social threefolding (Rudolf Steiner, *Die Kernpunkte der sozialen Frage*, 1919; English *Towards
Social Renewal*) distinguishes three spheres of social life, each with its own principle:

| Sphere | Principle | Domain |
|---|---|---|
| Rights (political) life | equality, democracy | law, public administration, public finance, representation |
| Cultural (spiritual) life | freedom | art, science, religion, education, the media |
| Economic life | uncoerced cooperation in freely contractual relations | production, trade, work, associations of producers and consumers |

**Resilience, read through this frame,** is the ability of each sphere to keep its own principle
working under attack — equal access and democratic self-government, free cultural and educational
life, cooperative economic life — and the balance between the three: no sphere taking over the
function of another.

The theory is normative. Here it serves as an **interpretive and organising frame**: it decides which
indicators are gathered and how results are grouped. The analysis stays associational, as in the
current paper. It does not test the theory.

## 2. Where the current measures sit

**The municipal budget is split between two spheres** (decision of 26 Sep 2026): the tax base belongs to
economic life, and the autonomy and spending choices of local self-government belong to rights life.
The four components of the current fiscal capacity index divide evenly:

| Capacity component | Sphere |
|---|---|
| Own revenue per resident | Economic (tax base) |
| Civilian income-tax growth | Economic (tax base) |
| Transfer dependency (inverse) | Rights (autonomy) |
| Capital-expenditure share | Rights (spending choices) |

Option B builds two sub-indices from these pairs and reports them separately.

| Measure (existing) | Level | Sphere | Note |
|---|---|---|---|
| Fiscal capacity index: own revenue, income-tax growth / transfer dependency, capital spending | hromada | Economic / Rights | split as above |
| Civilian income tax growth, relative income tax | hromada | Economic | where work and earnings are located |
| Night-time light (recovery, level, outage loss) | hromada | Economic (+ infrastructure) | activity and services; grid is shared infrastructure |
| ЄДРПОУ legal entities and sole proprietors per 1,000 | hromada, 10 oblasts | Economic | partial coverage |
| DREAM reconstruction projects per 10,000 | hromada | Rights | public investment planning and transparency |
| reSCORE: trust in local administration, civic engagement, locality satisfaction | oblast | Rights | |
| reSCORE: belonging, mental wellbeing | oblast | Cultural | |
| reSCORE: community cohesion | oblast | across spheres | decided 26 Sep 2026: reported beside the spheres, in no sphere index |
| reSCORE: economic security | oblast | Economic | |
| IOM DTM displacement | oblast | across spheres | reception involves all three |

**Gap:** the cultural sphere has no hromada-level measure at all, and economic *cooperation* (as
distinct from activity) is not measured.

## 3. Candidate new data

Counts or shares per hromada only; no site locations (rule R1). Schools, libraries and religious
buildings are sensitive targets and are never mapped as points.

| Sphere | Indicator | Source | Level | Effort | To verify |
|---|---|---|---|---|---|
| Cultural | Education and culture spending, share of expenditure (functional classification 09 education, 08 culture and sport) | openbudget.gov.ua API, same source as `03_openbudget.py` (`classificationType=FUNCTIONAL`) | hromada, 2021–2026 | low | one test pull |
| Cultural | Schools and pupils per 1,000; schools operating in person / online | ІСУО / Ministry of Education open data | hromada | medium | licence, war-time updates |
| Cultural | Damaged or destroyed education facilities (count) | saveschools.in.ua (Ministry of Education) | hromada | medium | terms, R1 |
| Cultural | Religious communities per 10,000 | register of religious organisations (data.gov.ua) | hromada via address | medium | geocoding quality |
| Cultural | Libraries and cultural institutions per 10,000 | Ministry of Culture registers | hromada | medium | availability |
| Cultural | Local media outlets | National Council register of media entities | hromada via address | medium | availability |
| Rights | Local election turnout 2020; council composition (gender share) | Central Election Commission | hromada | low–medium | format |
| Rights | Social protection spending share (functional 10); administration share (01) | openbudget.gov.ua (functional) | hromada | low | with the cultural pull |
| Rights | Administrative service centres (ЦНАП) present | Ministry of Digital Transformation / Diia | hromada | low | availability |
| Economic | Cooperatives and associations (legal forms) per 10,000 | ЄДР bulk open data (data.gov.ua) | — | — | **not feasible**: the legal-entity file has no address or location field (`tidy/source_catalogue.md`, section 3) |
| Economic | Housing and communal economy spending share (functional 06) | openbudget.gov.ua | hromada | low | with the cultural pull |

The functional-classification pull is the natural first step: one source already in the pipeline
gives hromada-level measures for all three spheres.

## 4. Spatial analysis design

1. **Sphere indices per hromada** — mean percentile rank of the indicators in each sphere, built like
   the capacity index; oblast-level survey indicators kept separate.
2. **Maps** — one choropleth per sphere, and a **threefold balance map**: each hromada coloured by the
   relative weight of its three sphere indices (ternary colour scheme), under rules R1–R3.
3. **Associations** —
   - each sphere index against exposure (strikes, alert hours), with oblast fixed effects and spatial
     diagnostics, as in Part I;
   - each sphere index against functional resilience (outage loss, recovery), within oblasts;
   - between-sphere associations: do the spheres move together, or does one compensate for another?
4. **Clusters** — LISA on the sphere indices and on the balance, national and Carpathian.
5. **Carpathian reading** — the four oblasts by sphere, including the survey indicators.

## 5. What it means for the paper

- **Option A — lens now, data later.** Keep the two-part v0.3 structure and results; add threefolding
  to the introduction (framework, Table of spheres) and re-read the synthesis through it. Label
  existing measures by sphere. No new data; fits the v1.2 release.
- **Option B — three-sphere paper.** Restructure around the three spheres (rights, cultural,
  economic), with the new data. A larger piece of work: new pulls on the data machine, new scripts
  (`31_functional_spending.py`, …), new maps, and review of every indicator against R1–R6.
- **Recommended:** A for the v1.2 release, B as the next version, starting with the functional
  spending pull.

## 6. Agreed indicators (step 2, 26 Sep 2026)

### Design decisions

- **Night-time light is not in any sphere index.** Light recovery and outage loss are the outcomes
  (functional resilience) in the association step; using them as inputs would make the test circular.
- **Two time points.** A 2021 baseline index (pre-war) and a 2025 index wherever the data allow. The
  baseline is the one tested against the summer-2024 outage loss.
- **At least three hromada-level indicators per sphere and year**, otherwise the sphere index is not
  computed for that year.
- **Oblast survey indicators** (reSCORE) are reported beside the sphere indices, never inside them.
  Community cohesion and displacement (IOM DTM) are reported across spheres.
- **Rule R7** (sensitive cultural data) applies; see README, security rules.

Status: **E** existing in `tidy/`; **C** computed from an existing cache, no new pull; **N** new pull;
**V** source to verify; **✗** not feasible. **S** = sensitive under R1/R6/R7.

### Economic life — index inputs

| Indicator | Direction | 2021 | 2025 | Status | Source / note |
|---|---|---|---|---|---|
| Property and land payments (1801xxxx) per resident | + | ✓ | ✓ | C | INCOMES cache; replaces total own revenue (step 5): PIT is the largest part of own revenue (rank correlation 0.93), so total own revenue would count PIT twice. Own revenue stays in the economic budget sub-index |
| Civilian income tax per resident | + | ✓ | ✓ | E | booked at the employer's address |
| Single tax (єдиний податок, 1805xxxx) per resident | + | ✓ | ✓ | C | INCOMES cache; sole proprietors and group-4 farmers |
| Civilian income-tax growth 2021–2025 | + | — | ✓ | E | `pdfo_civ_growth_rel_2125` |

Context, not in the index: housing and communal economy spending share (functional 06); ЄДРПОУ entities
and sole proprietors per 1,000 (10 oblasts, partial); reSCORE economic security (oblast).
Not feasible: cooperatives and associations (ЄДР has no address field).

### Rights life — index inputs

| Indicator | Direction | 2021 | 2025 | Status | Source / note |
|---|---|---|---|---|---|
| Transfer dependency | − | ✓ | ✓ | E / C | INCOMES (2021 from cache) |
| Capital-expenditure share | + | ✓ | ✓ (2023–25) | E / N | 2021: `03_openbudget.py pull --items EXPENSES_ECONOMIC --years 2021` |
| Social protection spending per resident (functional 10) | + | ✓ | ✓ | N | `31_functional_spending.py`; per resident, not share (step 5, 28 Sep 2026) |
| DREAM projects per 10,000 | + | — | ✓ | E | also reflects damage and donor attention |
| Contestation of the 2020 council election: candidates per seat, relative to its electoral system | + | ✓ | — | done (step 4a) | `33_elections_2020.py`, CEC open data; 1,276 of 1,289 non-occupied hromadas |
| Women's share of council seats 2020 | + | ✓ | — | V, S | aggregated from candidate lists; names never stored |
| Administrative service centres (ЦНАП) per 10,000 | + | ? | ✓ | V (step 4c) | count only |

Context, not in the index: administration spending share (functional 01; direction ambiguous); military
administration established (step 4d; a stratifier, tied to the front); reSCORE trust in local
administration, civic engagement, locality satisfaction (oblast).

### Cultural life — index inputs

| Indicator | Direction | 2021 | 2025 | Status | Source / note |
|---|---|---|---|---|---|
| Culture and arts spending per resident (functional 082x) | + | ✓ | ✓ | N | per resident, not share (step 5) |
| Education spending per resident (functional 09) | + | ✓ | ✓ | N | largely the education subvention: partly measures pupil numbers |
| Extracurricular education spending per resident (functional 096x) | + | ✓ | ✓ | N | art and music schools, clubs; 0 where absent |
| General secondary schools in operation per 10,000 residents | + | — | ✓ | done (step 4b) | `34_schools.py`, ЄДЕБО register (KATOTTG), 1,438 hromadas; higher where settlement is dispersed |

Context, not in the index: sport (0810) and media (0830) spending shares; reSCORE belonging and mental
wellbeing (oblast). Lower priority, only if a step-4 source fails: libraries and cultural institutions,
local media outlets (S), religious communities per 10,000 (S; total only, never by confession),
damaged education facilities (S; impact, not capacity).

### Order of new sources (step 4)

1. Local elections 2020 (rights) — **done 27 Sep 2026.** Turnout is not feasible: the CEC publishes no
   structured turnout for local elections, and the territorial commissions' protocol PDFs cannot be
   linked to the open-data council ids and are partly handwritten scans. Used instead: deputy
   candidates per council seat (`cand_per_seat_rel`, ratio to the median of the same electoral system:
   8.5 with party lists, 2.9 in multi-member districts). Candidates for head are listed for city
   councils only (context).
2. General secondary schools (cultural) — **done 27 Sep 2026.** Index input: working schools per 10,000
   residents (ЄДЕБО register, current). Pupils 2021 (form ЗНЗ-1, pre-war, CC BY 4.0) are context only:
   schools carry no code and are placed by settlement name; pupil counts within a 5 % bound are
   available for 756 hromadas, unevenly by oblast. Class size (ambiguous direction) and suspended
   schools (a war outcome) are context. Register licence statement to confirm before release.
3. Administrative service centres, ЦНАП (rights).
4. Military administrations (stratifier).

Spending enters the cultural and rights spheres **per resident, not as shares** (decision of 28 Sep 2026).
Shares of one budget sum to 1: a high education share lowers every other share, so shares built a
negative cultural–rights correlation into the indices (−0.38) and did not cohere as a cultural sphere
(−0.16 to 0.10). Per-resident amounts rise with fiscal size (cultural–economic 0.61–0.66) — the
economic sphere supplies the means of the cultural one; step 7 examines this. Shares remain a
sensitivity check and context.

## 7. Sphere indices — first results (step 5, 28 Sep 2026)

Coverage: 1,288 non-occupied hromadas for every sphere and year (candidates per seat 1,276).

| | within-sphere rank correlations | leave-one-out ρ | 2021 vs 2025 |
|---|---|---|---|
| Economic | 0.61–0.73 between the three tax bases; PIT growth 0.10–0.22 | ≥ 0.95 | 0.77 |
| Rights | 0.06–0.44 | ≥ 0.92 | 0.70 |
| Cultural | culture–education 0.48–0.55, education–schools 0.64; extracurricular −0.07–0.01, against schools −0.26 (art schools in towns, dense school networks in villages) | ≥ 0.85 | 0.81 |

Between spheres (2021 / 2025): economic–cultural 0.58 / 0.63, economic–rights 0.55 / 0.58, rights–cultural
0.22 / 0.27. Budget sub-indices 2025 (economic vs rights part of fiscal capacity): 0.45.

Carpathian medians (national median ≈ 0.50): economic 2021 0.13–0.16 in Zakarpattia, Ivano-Frankivsk,
Chernivtsi (Lviv 0.40), 2025 0.30–0.32 (Lviv 0.53) — a relative rise to test in step 8 (relocation of firms
and people); cultural 0.38–0.45 (Lviv ≈ 0.5); rights 0.26–0.34 (Lviv ≈ 0.5).

## 8. Maps (step 6, 28 Sep 2026)

Pages 21–24 (`35_sphere_layers.py`, `viina/build_qgis_project.py`), previews published: 21 economic, 22 rights,
23 cultural (2021 | 2025, national quintiles), 24 threefold balance (centred ternary colours: hue = which sphere
weighs more than on national average, strength = size of the departure, one scale for both years). Rule R3:
zone hromadas shown as population-weighted raion values. Patterns to examine in steps 7–8:
- economic: the western border oblasts mostly in the lowest classes in 2021, darker classes spreading west by 2025;
- rights: low in the west in both years (transfer dependency, capital share), high in the centre and east;
- cultural: a broad central and south-western band, rising in the west by 2025; pale zone raions in the east;
- balance: the Carpathian arc cultural and rights-leaning in 2021, cultural and economic-leaning in 2025; the
  Kharkiv and Zaporizhzhia zone raions strongly rights-leaning in 2025 (transfers, reconstruction projects).

## 9. Associations (step 7, 28 Sep 2026)

`36_sphere_associations.py` → `tidy/sphere_associations.csv` (81 rows), `tidy/sphere_lisa_summary.csv`; hromada
LISA classes stay local (`sphere_lisa_k3.csv`, rule R3). 1,288 non-occupied hromadas (recovery index 1,020, summer-2024
light 907). Coefficients in standard deviations; p = wild-cluster bootstrap by oblast (24 clusters); every result
below that is called robust also holds with Conley t at 50 and 100 km. Cross-sectional and associational throughout.

**A. Exposure (strikes since 2022, log).**
- Strikes fell on hromadas that were stronger before the war, in all three spheres and within oblasts (2021, with
  oblast FE and log population: economic +0.24, p < 0.001; rights +0.12, p = 0.009; cultural +0.13, p = 0.001). The
  strikes come after 2021, so this is geography and targeting (larger, better-equipped places), not an effect.
- 2025 given 2021, within oblasts: exposed hromadas fell back in the economic sphere (−0.16, 95 % [−0.27, −0.03])
  and the cultural sphere (−0.11, [−0.22, −0.00]); rights unchanged (+0.01). **Both falls disappear without the 196
  zone hromadas** (economic +0.00, cultural +0.02): the relative loss is a zone phenomenon (within 30 km of the front
  line or border), not a general cost of being struck. Outside the zone, exposed hromadas gained in the rights
  sphere (+0.08, p = 0.013), in line with transfers and reconstruction projects going to struck places. Alert hours
  point the same way but are mostly an oblast-level signal and absorbed by the fixed effects (p 0.08–0.28).
- Balance: exposure goes with a more one-sided profile in 2025 given 2021 (imbalance +0.30, p < 0.001) and with a
  shift from the economic to the rights side (−0.20, p = 0.028) — the rights-leaning zone raions on map 24. Whether
  this also holds without the zone is not yet tested (step 8).
- Per-resident terms use the 2020 population, so in the zone the 2025 values measure budget amounts per pre-war
  resident, not per person still living there.

**B. Pre-war spheres (2021) and functional resilience** (all three together, exposure, log population, lit pixels,
2021 radiance, oblast FE).
- Summer-2024 outages: hromadas with a stronger rights sphere lost less light (+0.20, [+0.08, +0.32]; reliable
  light data only: +0.16, p = 0.020). The clearest link between a sphere and functional resilience.
- Recent light level: a stronger cultural sphere in 2021 goes with a lower recent level (−0.08, [−0.12, −0.05];
  reliable data −0.08, p = 0.012). Likely composition: high education spending per resident marks small rural
  hromadas with dense school networks and shrinking populations — to test in step 8 by indicator.
- Economic sphere: no independent link once rights and culture are in the model (p 0.06–0.70).
- Recovery index: weak (rights +0.09, p = 0.048; cultural −0.06, p = 0.052).
- Buffering: no sphere reliably buffers exposure. One of nine interactions is nominally significant (cultural ×
  exposure on recent light, −0.04, p = 0.032; rights × exposure +0.06, p = 0.054) — not enough to claim buffering.

**C. The spheres against each other** (rank correlation, plain | within oblasts; change = 2021 → 2025).

| | 2021 | 2025 | change |
|---|---|---|---|
| economic–cultural | 0.58 \| 0.58 | 0.63 \| 0.61 | 0.38 \| 0.29 |
| economic–rights | 0.55 \| 0.36 | 0.58 \| 0.53 | 0.09 \| 0.17 |
| rights–cultural | 0.22 \| 0.13 | 0.27 \| 0.25 | 0.14 \| 0.18 |

- Economic and cultural life go together within every oblast, and their changes go together too (FE, population
  control: +0.38, [+0.29, +0.47]). Part of this is budget arithmetic — own revenue pays for culture and part of
  education — which is the "economic sphere supplies the means of the cultural one" of section 6, measured here.
- Economic–rights: in 2021 largely a between-oblast pattern (0.55 plain, 0.36 within); by 2025 it holds within
  oblasts as well (0.53): the two parts of fiscal capacity have come closer inside each oblast.
- Rights and cultural life are nearly independent. The threefold picture is two coupled spheres and one apart.
- Residual Moran's I stays 0.05–0.25: shared regional factors not captured by oblast FE.

**D. Local clusters (LISA, KNN 6).**
- Economic (global I 0.48 / 0.42) and rights (0.41 / 0.43) are regional; cultural is local (0.11 / 0.16).
- The economic change is strongly regional (I 0.45): in the national LISA, 33–44 hromadas in each Carpathian oblast
  are high–high clusters of economic rise, none low–low. Within the four oblasts the rise is even (Carpathian-scope
  I 0.01): the whole region moved, not a few pockets.
- Carpathian arc: low–low economic clusters in 2021 (Zakarpattia 50, Ivano-Frankivsk 43, Chernivtsi 50, Lviv 20),
  fewer by 2025 (32, 26, 43, 7), with a Lviv high–high cluster forming (3 → 18). Rights low–low in both years except
  Lviv. In 2021 the arc was strongly unbalanced (imbalance high–high 30, 30, 24; not Lviv) — cultural-leaning and
  rights- over economic-leaning; by 2025 the imbalance clusters have largely gone (4, 5, 16) and the arc leans
  cultural and slightly economic. This confirms the map-24 reading.
- Counts after a false-discovery-rate cut are smaller (e.g. economic 2021 high–high 200 → 106); no FDR-significant
  imbalance clusters remain in 2025.

**For step 8 ("why there?"):** (1) the zone as the carrier of the economic and cultural fall — which indicators;
(2) the balance shift without the zone; (3) which rights indicators carry the summer-2024 link (transfer dependency,
capital share, social spending, candidates per seat); (4) the negative cultural–light link by indicator and settlement
type; (5) the Carpathian economic rise — relocation of firms and people (IDPs, registrations).

## 10. Why there? (step 8, 28 Sep 2026)

`37_why_there.py` (shared code with 36 in `sphere_common.py`) → `tidy/why_there_models.csv` (117 rows),
`tidy/why_there_profiles.csv` (group medians, groups < 5 suppressed; no light values, rule R2). Same inference as
section 9. **Like-for-like** = mean rank of the indicators measured in both years (the 2025 indices add PIT growth,
DREAM projects and schools; the 2021 rights index has candidates per seat). Rank correlation of like-for-like with
index change: economic 0.83, rights 0.73, cultural 0.64.

**Q1 — the zone carries the fall.** Zone gap within oblasts, 2025 given 2021 (SD): like-for-like economic −0.38
[−0.62, −0.14], rights −0.26 [−0.39, −0.14], cultural −0.55 [−0.83, −0.24].
- Economic: civilian PIT −0.47 and property tax −0.40 per resident; single tax −0.19 (p = 0.12). Half of the
  zone's economic-index fall comes from the 2025-only PIT-growth indicator (zone median rank 0.12, elsewhere ≈ 0.55).
- Rights: transfer dependency rose (−0.44), social spending per resident fell (−0.21); capital share and DREAM
  projects no different from the rest of the oblast. The zone's rights index holds up in 2025 only because of
  capital share (median rank 0.73) and DREAM; like-for-like it fell.
- Cultural: all three items fell (culture and arts −0.42, education −0.44, extracurricular −0.22).
- Exposure without the zone: no fall in any economic or cultural indicator. Struck hromadas outside the zone raised
  capital share (+0.09) and social spending (+0.12) and education per resident (+0.05) — the rights gain of section
  9 is spending, not transfers.
- Per-resident terms use the 2020 population: in the zone the fall is also a fall in the people still paying and
  served.

**Q2 — balance.** Median imbalance fell from 2021 to 2025 everywhere except the zone (zone 0.40 → 0.59; rest of the
same oblasts 0.39 → 0.33; other oblasts 0.43 → 0.32). Exposure goes with a more one-sided profile also without the
zone (+0.13, p < 0.001) and inside it (+0.47). The shift from economic to rights is a zone matter: none without the
zone (+0.01), zone gap −0.63 [−1.06, −0.18], inside the zone −0.45 with exposure. Map 24's rights-leaning zone
raions = economic collapse with capital share and reconstruction projects holding the rights index up.

**Q3 — summer-2024 outages: fiscal independence.** Lower transfer dependency in 2021 goes with a smaller summer-2024
light loss: +0.21 [+0.11, +0.30] (reliable light +0.15, p = 0.016; without zone +0.30, p < 0.001). Capital share
adds +0.08 [+0.02, +0.14] (p = 0.10 on reliable light). Social spending and candidates per seat: nothing. The
"rights" link of section 9 is the fiscal-autonomy part of the rights sphere, with economic and cultural 2021 held
constant.

**Q4 — the negative cultural–light link stays unexplained.** No single cultural indicator carries it robustly
(culture and arts −0.08, p = 0.15; extracurricular −0.05, p = 0.04, gone on reliable light; education 0). School
network (class size, rural school share, pupils per 1,000) and modelled population change leave the coefficient
unchanged (−0.08). Present in settlement and village hromadas (−0.08, −0.07; p 0.08, 0.14), absent in cities.
Higher cultural quintiles are smaller (median population 13,100 → 6,200) and richer (economic 2021 0.30 → 0.77).
Treated as fragile: not a finding for the paper.

**Q5 — the Carpathian rise: measure, catch-up and Lviv.**
- Economic index change 2021 → 2025: Carpathian median +0.15, rest −0.03; like-for-like only +0.04 (Lviv +0.09,
  the other three +0.02). About three quarters of the rise is the 2025-only PIT-growth indicator (Carpathian median
  rank 0.70; PIT growth 1.09 × national median, Lviv 1.15 ×).
- Given the 2021 level (the four oblasts started lowest, 0.13–0.40): like-for-like gap +0.18 [−0.03, +0.39],
  p = 0.08; without Lviv +0.08 (p = 0.21); without the zone p = 0.52. With PIT growth included +0.36 (p = 0.018).
- Clusters of economic rise (national LISA HH, 219): 69 % Carpathian, 6 % zone, low start (economic 2021 0.22).
  Clusters of fall (LL, 129): 78 % zone, none Carpathian.
- Relocation cannot be tested: registration growth covers five oblasts, none Carpathian; hromada-level displacement
  data are not available for publication. Where registrations exist, sole-proprietor growth goes with the single-tax
  change (+0.53), but not robustly (p = 0.21).
- Reading: faster civilian earnings growth in the west is real, but the rise in level is small, concentrated in
  Lviv and partly catch-up. Captions of maps 21 and 24 should say that the 2025 economic index includes PIT growth.

**Decision for step 9:** keep PIT growth in the economic 2025 index (it measures war-time dynamism, agreed in section
6) or report the like-for-like index as the main 2021 → 2025 comparison. Either way the paper states the split.

## 11. Paper v0.5 (step 9, 28 Sep 2026)

- **Structure:** Part I local capacity, recovery and exposure (sections 4–8, unchanged); **Part II the three
  spheres at hromada level** (9 measuring, 10 exposure, 11 functional resilience, 12 relations and clusters, 13 why
  there?); Part III trust, cohesion and reception (14–15, formerly Part II); synthesis by sphere; methods 16–18.
- **Tables:** S1 indicators (in the text); S2–S9 from `resilience/38_sphere_tables.py`, which reads published
  tidy tables only and writes `publication/numbers_spheres.yaml` (generated keys; `build.py` reads it beside
  `numbers.yaml`). Why-there tables W1–W6 (section 13) and W7–W8 (Carpathian light curves, trust with weak
  finances; section 15.5). Carpathian table renumbered 12, reSCORE 11, security audit 13.
- **Decision:** the economic 2025 index keeps civilian income-tax growth (as agreed in section 6); the paper
  reports the like-for-like change beside it and names the split wherever the two diverge.
- **Rules:** R7 (sensitive cultural data) in the paper's rule table; the review rule becomes R8.
- Open in the paper: register licence statement (ЄДЕБО), CEC and MES access dates, reference check.
