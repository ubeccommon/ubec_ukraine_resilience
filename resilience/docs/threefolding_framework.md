# Resilience in the light of social threefolding — framework proposal

Status: 26 Sep 2026. Decided: threefolding enters the paper now as its frame (Option A, paper v0.4, section 1.4);
the three-sphere analysis with new data follows as the next version (Option B, paper v0.5). The municipal budget
is split between spheres (section 2). The indicator list per sphere is agreed (section 6). Nothing in sections
3–6 is computed yet.

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
