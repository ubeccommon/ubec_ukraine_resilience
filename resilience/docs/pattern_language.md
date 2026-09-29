# Patterns of resilience — a pattern-language round on the hromada data

Status: 28 Sep 2026, proposal for discussion. Starts after paper v0.5 / data v1.3 (commit e794570). Step 1 script:
`39_quality.py`. Nothing here changes the paper's results; it proposes a further round of analysis on the same data
and names the data that would widen it.

## 1. Where the project stands

Fifty-nine scripts, twelve open sources joined at hromada level, 111 variables, 35 tidy tables, a 24-page atlas and
four publication outputs (paper v0.5, brief v0.2, essay v0.2, data package). The conceptual path ran in three moves:
strikes → capacity → recovery (buffering tested and rejected); time (monthly light and quarterly budgets: most
recovery variation is oblast-wide); social threefolding (the budget split between economic and rights life, a
cultural sphere from spending and the school register, the three spheres measured for 2021 and 2025).

Seven findings survive every robustness check (oblast fixed effects, wild-cluster bootstrap by oblast, Conley errors,
reliable light, without the zone):

| # | Finding | Evidence |
|---|---|---|
| 1 | Fiscal autonomy before the war goes with keeping light when the grid failed | transfer dependency 2021 → summer-2024 loss: +0.21 SD [+0.11, +0.30]; without zone +0.30; reliable light +0.15 |
| 2 | Local capacity does not buffer exposure; no sphere does | interaction ≈ 0 with FE for four outcomes; 1 of 9 sphere interactions nominal |
| 3 | Recovery is oblast-wide | R² 0.11 → 0.57 with oblast FE; all four Carpathian oblasts fell together in July 2024 |
| 4 | The relative fall since 2021 is a zone phenomenon | like-for-like zone gap: economic −0.38, rights −0.26, cultural −0.55; outside the zone no fall |
| 5 | Outside the zone, struck hromadas spent more | capital share +0.09, social protection +0.12, education +0.05 |
| 6 | Economic and cultural life move together; rights life stands apart | econ–cult 0.63 (2025), changes +0.38; rights–cult 0.27 |
| 7 | Strikes fell on stronger places | 2021 spheres predict later strikes within oblasts: +0.24, +0.12, +0.13 |

Three more hold at oblast level only (trust does not follow the fiscal map; Carpathian PIT peaked in 2022 Q2–Q3;
the Carpathian economic rise is mostly PIT growth, catch-up and Lviv), and one is fragile (cultural 2021 → lower
recent light, −0.08).

## 2. Where the current form reaches its limits

Five of the paper's limitations are limits of form, not of data:

1. Indices average away configuration. The finding that matters most (transfer dependency → outage retention)
   appeared only when the rights index was taken apart again in step 8.
2. Rank scores are relative and zero-sum (16.13). A benchmark needs an absolute statement: this configuration is
   present here, or it is not.
3. Budget lines measure means, not life (16.12). Civic life outside the budget is unmeasured, partly by design (R7).
4. Relational resilience is stuck at oblast level; the clearest Carpathian observation (weak finances, high trust)
   cannot be tested.
5. The "why there?" tables W1–W8 are already pattern statements — problem, candidate forces, evidence, what is
   open — written for one place at a time. A pattern language generalises them.

## 3. What we take from Christopher Alexander: the method, not the patterns

Alexander's 253 patterns (*A Pattern Language*, 1977) are answers to the forces of towns and buildings in his
context. Borrowing them one to one would import his answers into a question he never asked. What transfers is the
way he arrived at them (*The Timeless Way of Building*, 1979; *The Oregon Experiment*, 1975):

1. Start from the places that have the quality — "the quality without a name" — before it can be named.
2. Isolate the invariant: the configuration the living places share and the dead ones lack. A configuration, not a
   variable.
3. State it so it can be wrong: context, problem, forces, solution, in ordinary words.
4. Test it and rate it: two asterisks for an invariant seen everywhere, one for a solution that works but may not be
   the only one, none for a hypothesis.
5. Link it: patterns complete larger ones and are completed by smaller ones; the set is a language only when the
   links hold.

**The quality without a name, in our data.** A hromada has it when it held up under the same oblast conditions as
its neighbours — the same grid, exposure and distance to the front — and the models cannot say why from what they
already contain. Spatially that is the *residual*: the light kept, the revenue retained, the cultural provision
maintained that fixed effects, exposure and budget do not explain. Call it the **spatial data without a name**.
Where it recurs across outcomes and clusters in space, it marks the places to observe. Alexander's observation was
walking; ours is a residual map, followed by walking — the Carpathian dispatches and conversations in hromadas are
the field half of the method.

**Discipline.** No pattern is named before the observation. What a reader of Alexander or of the resilience
literature would expect is written down first and set aside (Annex A), to be compared with what the data produce
afterwards, not to steer it. Names come last, from what was seen, in the hromada's own words where possible.

We keep from his form: the pattern statement (context, problem in bold, forces, *therefore*), the confidence stars,
the scale hierarchy (oblast → hromada → settlement and institution), and the rule that a language is a network.
*The Nature of Order* (2002) adds properties to watch for once invariants emerge — levels of scale, boundaries,
roughness, not-separateness — as questions to ask of a configuration, not as patterns to look for.

## 4. The discovery loop

Six steps, repeated: (1) observe — hromadas that held up under the same oblast conditions: the residual map;
(2) isolate the invariant — what the held-up share and the others lack, as recurring configurations, not scores;
(3) state the pattern — problem, forces, therefore, named from what was seen; (4) test in the data — within oblast,
without the zone, bootstrap, a star for each check survived; (5) test in the field — does it ring true to those who
live there; (6) link into a language — which patterns co-occur, which complete which, at which scale; then back to
(1) with new outcomes and new data.

Threefolding supplies the rows in which a discovered pattern is placed afterwards (economic, rights, cultural,
across); the scale hierarchy supplies the columns (oblast context, hromada, settlement and institution). Neither
decides what the patterns are. Two structural findings of the paper act as context patterns for every hromada
pattern: recovery is oblast-wide (judge a hromada within its oblast), and the 30 km zone is a boundary, not a
gradient (score zone hromadas as a separate population).

## 5. The design

### 5.1 Defining the quality

| Outcome family | Residual from | "Held up" means |
|---|---|---|
| Light kept in the summer-2024 outages | 36, model B | kept more of its own 2023 light than the oblast and its budget predict |
| Light level 2025–26 given exposure | 22, level model | brighter than exposure and oblast predict (R2 lag applies to publication, not analysis) |
| Economic retention 2021 → 2025, like-for-like | 37, Q1 | held its tax bases relative to the oblast |
| Cultural retention 2021 → 2025 | 37, Q1 | held culture, education and extracurricular provision |
| Own-revenue retention after 2023 Q4 | 20 | own revenue did not fall when military PIT left local budgets |

Rule: **held up** = residual in the top quarter on at least two families and in the bottom quarter on none;
**faltered** = the reverse; the middle is set aside (Alexander compared the living with the dead, not with the
average). Zone hromadas (196) form their own population with their own residuals. Reception — the 2022 PIT gain and
IDPs taken in — is a different quality from holding up and gets its own set in a second round.

First check: LISA on the composite residual. Where the quality clusters, the configuration behind it is probably
regional and belongs to the oblast row; where it is scattered, it is a hromada-level pattern.

### 5.2 The observation set — `39_quality.py`

Reads the published tidy tables and refits the residuals (variant `spheres`: given exposure, population, light
controls and the 2021 sphere indices; variant `raw`: without the spheres), writes `tidy/quality_k3.csv` (local,
rule R2), `tidy/quality_summary.json` and `tidy/quality_profile.csv` (public), and the map layer
`hromada_quality` in `resilience_maps.gpkg` (zone hromadas as "zone", R3). Beside each hromada goes its profile:
the sphere inputs, schools, population change, hromada type, balance. Nothing that defines the quality is in the
profile. Expected size: roughly 120–200 hromadas in each of the two groups; the exact counts are the first thing to
report. The script also does the plain comparison of 5.3, method 1.

### 5.3 Isolating the configurations — `40_configurations.py` (next)

1. **Plain comparison.** For every profile variable, the share of held-up and of faltered hromadas above their oblast
   median (in 39). A check that the groups are not simply big versus small or west versus east.
2. **Rule induction.** A classification tree of depth at most three, cross-validated by oblast. Its leaves are
   conjunctions, and conjunctions are what a pattern is.
3. **Qualitative comparative analysis** (Ragin, fuzzy sets). Profile variables calibrated to set membership
   (absolute thresholds where natural, e.g. own revenue at half of total; within-oblast terciles otherwise).
   Necessary conditions and sufficient configurations with consistency and coverage: consistency ≥ 0.8 and
   coverage ≥ 0.1 make a candidate, provided it beats the noise ceiling — the best consistency a conjunction of
   the same length reaches when the outcome is shuffled within oblasts (`40_configurations.py`; on pure noise
   400 conjunctions pass the thresholds and none the ceiling).
4. **Kinds of held-up hromada.** Archetype analysis or clustering within the held-up group alone: several ways of
   holding up, not one recipe.

A configuration becomes a candidate pattern when it recurs in at least a tenth of the held-up hromadas, is rare
among the faltered, holds inside oblasts and in at least three of the four macro-regions, survives removal of the
zone, and can be said in one plain sentence. More than twelve candidates are merged by co-occurrence; fewer than
seven means the profile is missing something (section 6).

### 5.4 Stating, naming, testing, linking

Each candidate is written in pattern form: context (oblast row, hromada row), problem in one sentence, forces
(the evidence), *therefore* (what a hromada, oblast or donor would do). Names from the content, English and
Ukrainian side by side. Numbers only when the set is closed, ordered by scale, then sphere. Only then is Annex A
opened.

Tests in the data: each pattern against the outcome families not used to define the set for that run (define on
three, validate on two), with the paper's inference. Two stars for a configuration that survives every check; one
for a caveat; none for a hypothesis kept for the next round. Tests in the field: three to five hromadas per
pattern in the Carpathian oblasts, from the held-up set, through the dispatch series; a pattern nobody recognises
is wrong or badly named. Language: the co-occurrence matrix, placement in spheres and scales, links up and down.

### 5.5 Round 1 results (28 Sep 2026, `39_quality.py --reliable-light`, `40_configurations.py`)

**The observation set.** Outside the zone 181 held up, 181 faltered, 731 middle; zone 36 / 34 / 125. Moran's I of the
composite 0.09 (p = 0.001), nothing after FDR: the quality is hromada-level, not regional. Villages are 58 % of the
held-up against 37 % of the faltered; Carpathian hromadas are 30 % of both extremes against 19 % of the middle.

**The composite is not one quality.** Rank correlations between the five residual families: the two light families
0.53 with each other, the three budget families 0.09–0.33 among themselves, light with budget 0.02–0.22 (mean
off-diagonal 0.17). Held-up hromadas qualified mostly through budgets (top quarter on econ 69 %, cult 61 %, own
64 %; summer-2024 light 30 %). Holding light and holding the tax base are different things.

**The pre-war budget profile carries no configuration.** Composite and every single family: the tree is at chance
(balanced accuracy 0.48–0.61 with oblasts held out); of 5,252 conjunctions of up to three conditions, none beats the
permutation ceiling for holding up. One exception, for faltering on cultural retention: low payroll PIT, low single
tax and low autonomy in 2021 each pass alone (excess over the ceiling 0.03, precision 0.62–0.64) — cultural provision
held where the 2021 tax base paid for it (the paper's finding 6 as a condition; Annex A's "culture from own
revenue"; budget arithmetic more than a pattern). The "kinds" of held-up hromada are the same in every family: a
well-off kind high on every budget line and a poor kind low on every line, in similar numbers — holding up happens
at both ends of the budget.

**The recovery test.** Autonomy does not surface on summer-2024 retention, where the paper finds +0.21 SD within
oblasts (+0.15 on reliable light). The configurational search is calibrated to invariants (synthetic tests: it
finds a single condition at r ≈ 0.5 and rejects noise); the paper's associations are 0.1–0.2 SD. They are real,
and they are not patterns in Alexander's sense. `40` now reports the linear side beside the search (rank
correlation of each condition with the outcome against a permutation ceiling), so that weak associations are
visible rather than absent.

**Reading.** The design's own rule applies: fewer than seven configurations means the profile is missing what
matters. The budget lines record means, not the configuration that keeps a place going. The consequences table
gives the first lead — held-up hromadas had modelled population growth 2020 → 2025 (65 % above their oblast median
against 46 % of the faltered) — so people moving in, and who receives them, is the first thing to measure.

**Decisions for round 2.** (1) Split the quality: a functional quality (the two light families, reliable light
only) and a fiscal quality (the three budget families), each its own observation set. (2) Pull the NHSU
declarations (present population by hromada, weekly, CC BY 4.0) and the 2019 turnout by polling station before the
next round; then the civic-life and reserve sources of section 6 in the order of the consequences table.
(3) Keep the composite only as a check.

### 5.6 Round 2 set-up (28 Sep 2026)

Three qualities in `39`: composite (check), functional (light), fiscal (budgets). First results: the functional
quality has no pre-war budget signal at all (tree 0.50; no condition above the linear ceiling of 0.115, autonomy
+0.08); the fiscal quality has a weak linear local-tax-base signal (single tax +0.16, property tax +0.13, payroll PIT
+0.10, autonomy +0.09; ceiling 0.085) and no configuration. The functional "kinds" split sharply: a well-off,
village, western kind and a poorer, urban, central kind. Neither quality clusters much (I 0.10–0.11).

New sources: `41_nhsu_declarations.py` built (1,377 of 1,387 hromadas: 1,351 by name, 26 by a vote of their
settlements; 0.3 % of rows unplaced; median 796 declarations per 1,000 residents of 2020, p10 385, p90 1,316).
`42_cec_2019.py` is parked: the open CEC results are by electoral district, not polling station.

**Present population and age (NHSU, 2026) carry nothing either.** Share above the oblast median, held up vs
faltered: declarations per 1,000 +0.04 (composite), −0.02 (functional), +0.10 (fiscal); for the functional
quality, held-up hromadas are older (share 65+ +0.11, share under 18 −0.16). With the NHSU measures as conditions,
no configuration passes for either quality (8,180 conjunctions), and neither measure clears the linear ceiling
(functional: young −0.07, people present −0.04, ceiling 0.126; fiscal: people present +0.04, ceiling 0.089). The
round-1 lead (modelled population growth) does not survive a measured present population.

### 5.7 What two rounds show, and the turn to the field

Two rounds, three qualities, 15 conditions, some 8,000 conjunctions: no configuration of the open hromada data
precedes or accompanies holding up. What exists are weak linear associations — a local tax base (single tax,
property tax) with fiscal retention at r ≈ 0.15, fiscal autonomy with keeping light in summer 2024 at about
0.2 SD. The quality without a name is not in what budgets, registers and satellites record at hromada level.

That is a finding about the data, not about the method, and it brings the method back to where Alexander started:
observation of places first, abstraction second. The data work has done its part of step 1 — it names the places
to observe. Round 3 is therefore field-first:

1. **Pairs.** From `tidy/quality_k3.csv` (local), pairs of hromadas in the Carpathian oblasts, one held up and one
   faltered, in the same oblast, of the same type (city, settlement, village) and similar size and exposure — so
   that what differs between them is not what the models already control. Separately for the functional and the
   fiscal quality. The pair list stays local (R2: it is derived from recent light residuals).
2. **Observation.** Visits and conversations through the Soil and Peace dispatch series, with an open question —
   what here kept going, and how — and without Annex A in hand.
3. **Candidates.** What recurs across the held-up member of several pairs and is absent in their partners is
   written as a candidate pattern, in the words used there.
4. **Return to the data.** Each candidate is given the nearest open measure (section 6 lists the candidates:
   reserve, civic institutions, reception, self-formation) and tested on all hromadas as in 5.3–5.4.

The benchmark set of 7–12 patterns comes out of step 3 and is validated in step 4; the open data then serve as the
test, not as the source.

### 5.8 The field sheet reviewed before the first pairs (29 Sep 2026)

The six questions of `43_pairs.py` were written with the light pairs in mind. Read against the method's own rules —
observe the place first, ask what is rather than what is thought, keep the two qualities apart, record what can
later be tested — they needed five corrections, all made in the sheet before L2 and B2 rather than after, because
each would otherwise cost a visit:

1. **Question 1 named the outcome.** "The outages of summer 2024" is the definition of the functional quality; asked
   in a budget pair it steers the conversation to light and away from money. It now asks what kept going since 2022,
   through the winters, the outages and the alerts, and what stopped, and when.
2. **Nothing asked about money.** The fiscal quality — a tax base held, cultural provision kept, own revenue not lost
   when military PIT left — had no question at all. Question 5 now asks where the money comes from for what the
   hromada does for itself: own means, the oblast, donors, people abroad. Phrased in things, not budget lines.
3. **"Who decided" invites names.** Rule R6 is now on the sheet: answers by role or institution.
4. **Timing was absent.** The return to the data (5.9) has to know whether a practice pre-dates 2022 (a condition,
   testable against pre-war registers) or arose in response (a consequence, or the holding up itself). Each practice
   noted gets a "since when" (before 2014 / 2014–21 / 2022 / 2024).
5. **Nothing was observed without asking.** Alexander's observation begins with the place. The sheet now lists a
   walk to be made before the conversations — council hours, market, school gate, club, church, notice board,
   generators and heating points, fields, houses, the bus — and a row for what it shows.

Two more things the sheet now fixes: who is asked (the same three roles in both members of a pair, so that the
contrast is like for like — council, an institution, the market or a farm), and that question 4 asks for kinds and
numbers of households, not their stories.

What the questions cannot reach, so that silence is not read as absence: how the hromada was formed (Annex A's
self-formation) and participation between elections. A seventh question on formation is held in reserve; the "since
when" row will show whether it is needed ("since the amalgamation" is an answer people give). Participation stays
out until a pattern points to it. The review after L2 and B2 stands as planned: which questions earned their place,
which words recurred, what the walk showed that the conversations did not.

### 5.9 Return to the data: `44_measures.py` and `45_candidates.py` (29 Sep 2026)

Step 4 of the field round is prepared so that a candidate pattern can be tested the week it is stated.

**`44_measures.py`** gives each section-6 aspect its nearest open measure, one value per hromada, counts and shares
only (R1, R6, R7). One placement engine serves every source — KATOTTG code, COD pcode, hromada name (the matcher of
`33`), settlement name within the raion or oblast (the codifier of `34`), coordinates (spatial join, then dropped),
or a free-text address parsed into these. Sub-commands: `civil` (functional 0320, civil protection, from `31`'s
local table: share of civilian expenditure 2021, 2022–23, 2024–25, per resident, and the change — the reserve a
hromada set aside once the war came; no network needed); `prozorro` (tenders for generators and generating sets
2022–2024 by the council and by communal entities, counts and expected value per resident; Prozorro search API);
`nonprofit` (the State Tax Service register: public associations, charities, OSBB and housing co-operatives,
agricultural co-operatives, unions — religious organisations and parties are never counted, R7); `w3` (OCHA 3W on
HDX: organisations active per hromada, of which local); `formation` (Wikidata: year the hromada was formed, before
or in the administrative wave of 12 June 2020); and `places`, which counts any list — invincibility points, youth
centres, veteran spaces, libraries, IDP councils, service centres, community officers — and deletes a point file
after use. Each sub-command has `probe`, `pull`, `build`; the probes exist because none of these sites can be opened
from Claude's workspace, so column names and dataset ids are confirmed on the data machine first. `assemble` merges
everything into `tidy/measures_k3.csv` (public) and writes the `m_*` rows of the data dictionary. First runs (29 Sep 2026): `civil` and `formation` built; `prozorro` running against a rate limit; `nonprofit` and `w3` parked — the register has no address and the ЄДР dump none either, and every 3W file is by oblast (section 6.2).

**`45_candidates.py`** takes a measure (or several: each alone, then their conjunction), a quality and a sign, and
runs the checks the design's stars stand for, each named and logged: C1 the plain comparison; C2 the linear
association against the within-oblast permutation ceiling; C3 the paper's inference (oblast fixed effects,
wild-cluster bootstrap); C4 the families that did not define the quality (define on some, validate on the others);
C5 three of four macro-regions; C6 the zone as a separate population (a caveat, not a failure); C7 the
configurational search of `40` with the candidate as an added condition — the difference between an association and
a configuration. Two stars for C1–C5 and C7; one for an association that is not a configuration, or one soft check
missed; none otherwise. A measure dated after February 2022 is marked as accompanying, not preceding. The row goes
to `tidy/candidates.csv` with the calibration thresholds the profile table of section 7 will use. Synthetic tests
(29 Sep 2026): a planted single condition at r ≈ 0.6 earns two stars and is found in 31 conjunctions; noise earns
none and passes no conjunction; a paper-scale association at r ≈ 0.24 passes the linear checks and, with few
permutations, the ceiling — run with `--perms 20` or more before believing a configuration.

## 6. Data not yet used

Discovery can only find configurations among the variables it is given; the current 111 describe budgets, light,
exposure, elections and schools, little about how a hromada is put together. Checked 28 Sep 2026 from Claude's
workspace (which cannot open Ukrainian government sites: "verify" = confirm on the data machine). Counts and shares
per hromada only (R1, R7).

### 6.1 Closing known weaknesses

| Source | What it gives | Level | Terms | Weakness closed |
|---|---|---|---|---|
| NHSU: declarations with a primary-care doctor (data.gov.ua a8228262…) | active declarations by hromada and settlement, by age and sex; weekly since 2018, last update 28 Sep 2026 | hromada, settlement | CC BY 4.0 | the 2020 population denominator (16.6); use the by-community file only — the doctor file carries names (R6); declarations lag moves, read the change |
| CEC 2019 presidential and parliamentary results by polling station (data.gov.ua, CEC) + State Voter Register station list | turnout per polling station, stations by settlement | station → hromada | CC BY | no turnout for the 2020 local elections: pre-war participation from 2019 instead |
| Historical borders 1914 and interwar (published replication data, e.g. Grosfeld and Zhuravskaya 2015) | empire and interwar state per hromada | overlay | research data | "regional history of institutions", open in Table W8 |
| Copernicus DEM 30 m / SRTM | elevation, slope, share above 500 m | hromada | free | terrain, request 30 |

### 6.2 Widening the profile

| Source | What it gives | Level | Terms | Aspect | Verify |
|---|---|---|---|---|---|
| openbudget INCOMES cache (pulled) | revenue diversity: shares of PIT, single tax, property and land, excise, rent; Herfindahl of own revenue; tourist tax (1811), retail excise (1404–1405), parking and advertising fees | hromada 2021–2026 | CMU 835 | tax-base composition; visitor and retail economy | codes in the cache |
| openbudget functional 03xx | civil protection (0320) per resident, 2022–2025 change | hromada | CMU 835 | what the hromada set aside for itself | built 29 Sep 2026 (`44 civil`): 770 hromadas with 0320 in 2021, 1,077 in 2025; 2022–2024 not yet in `31`'s cache |
| Prozorro public API | tenders by hromada councils and communal enterprises: generators and energy equipment 2022–24, repair contracts, share won by local suppliers | buyer ЄДРПОУ → k3; supplier by locality | CMU 835, API open | reserve, repair, local supply chains | EDRPOU→k3 crosswalk, supplier address quality |
| nezlamnist.gov.ua | invincibility points per 10,000 | point → count | public by design | reserve | counts only, delete point cache (R1) |
| decentralization.gov.ua / Wikidata (CC0) | formation date, voluntary amalgamation before 2020 vs administrative, councils merged | hromada | site terms / CC0 | how the community came to be | built 29 Sep 2026 (`44 formation`, P9435): year known for 1,144 hromadas, 783 formed before 12 June 2020 |
| E-DEM petitions; data.gov.ua petitions | petitions and signatures per 10,000; participatory-budget hromadas | hromada | CC BY (data.gov.ua part) | participation between elections | no signer data (R6) |
| Mintsyfra ЦНАП list | service centres per 10,000 | hromada | verify | access to administration | bulk list |
| IDP councils (CMU resolution, Aug 2023; SSS list) | hromadas with an IDP council, date | hromada | verify | reception | official register |
| Register of non-profits (State Tax Service, CC BY 4.0) | CSOs, charities, OSBB, cooperatives by non-profit code | tax office (raion) at best | CC BY | civic life outside the budget | verified 29 Sep 2026: no address in the register (229,416 entities, Feb 2022) and none in the ЄДР legal-entity dump — parked; nearest substitute: statistics offices' counts by legal form (`09`, 10 oblasts) |
| Youth centres and veteran spaces registers | per 10,000 | hromada via settlement | verify | civic life | existence, format |
| Ukrainian Library Association / Ministry of Culture | public libraries per 10,000; closures since 2022 | via settlement | verify | cultural provision | licence |
| ЄДЕБО (pulled) | schools by operating mode, shelter share, mountain flag | hromada | terms pending | cultural provision under fire | fields present |
| OCHA Ukraine 3W/5W (HDX, CC BY, `ukraine-who-does-what-where-3w`) | organisations and sectors active; local vs international | oblast only | CC BY | reception; local NGOs as implementers | verified 29 Sep 2026: all 73 files, the 2022 weekly rounds included, are by oblast — parked |
| Sentinel-1 building damage (Zenodo 15088349, Dietrich et al. 2025) | share of buildings damaged per ADM3 | hromada | CC BY | separates damage from targeting | ADM3 coding |
| NBU bank branches; Ukrposhta and Nova Poshta points; pharmacy licences | services per 10,000, closures since 2022 | address → hromada | open / site terms | service retreat or growth | address fields, reuse terms |
| Prozorro.Sale land and lease auctions | communal land and property auctioned per hromada | hromada (seller) | open API | use of common assets | seller→k3 |
| Geocadastre normative monetary valuation by settlement | land value index | settlement → hromada | open data | quality of the land base | format |
| Ministry of Economy relocated-enterprise programme | enterprises relocated by receiving hromada | hromada or oblast | verify | reception of firms (section 13) | level published |
| Naftogaz heat-supply debtors | utility financial stress per city | company → hromada | published list | fragility below the grid | terms |
| Verkhovna Rada renaming acts 2022–2025 | derussification renamings per hromada, and how early | hromada | official acts | identity work in the cultural sphere | compile from acts |
| Wikidata twinning | twin towns per hromada | hromada | CC0 | outside ties | coverage beyond cities |
| UCF and House of Europe grant lists | funded cultural projects by locality | via locality | published lists | cultural initiative outside the budget | applicant names not stored |
| IATI activities for Ukraine (d-portal) | donor activities with subnational locations | admin1–3 where geocoded | open | who receives outside help | share geocoded below oblast |
| єВідновлення compensation statistics | applications and payments by hromada | hromada or oblast | dashboard | repair at household level | level published |
| National Police community-officer programme | hromadas with an officer, since when | hromada | published lists | a rights institution present or absent | current list |
| OSM edit history (ohsome) | edits and mapped buildings per hromada since 2022 | hromada | ODbL | digital civic activity | run on the data machine |
| Ministry of Justice civil-status statistics | births and marriages per 1,000, 2021–2025 | oblast; raion where published | published | "life goes on" | raion availability |
| NASA FIRMS; NASA Harvest / Copernicus crop maps; Global Forest Watch; Ookla tiles | fires, cultivated vs abandoned cropland, forest loss, connectivity per hromada | hromada | free, attribution | independent exposure; agricultural continuity; forest commons; digital reserve | — |

Checked and not feasible for hromada counts: cooperatives and associations from the ЄДР dump (no address field),
local election turnout (no structured CEC data), the Digital Transformation Index (login only), sole proprietors
from the single-tax register (the open part carries no tax address; group 4 to verify). One class found and
rejected: anything that locates people or infrastructure below hromada level (shelters, outage maps, community
channels, the doctor-level NHSU file). Under R1 and R6 none of it enters, and no counts are derived from it.

Two derived measures need no new source: the revenue Herfindahl and the civil-protection spending change, from the
INCOMES and EXPENSES caches. The NHSU declarations file and the 2019 turnout are worth pulling before the first
round because they change the profile for every hromada.

## 7. From discovered patterns to benchmarks

| Element | Rule |
|---|---|
| Presence | fuzzy membership in the configuration; present ≥ 0.67, partial 0.33–0.67, absent below; calibration thresholds published with the pattern |
| Reference | absolute where the threshold is natural; within-oblast otherwise |
| Zone | same rules, separate calibration and validation |
| Rating | two stars: survives every check and holds in three of four macro-regions; one: a caveat; none: hypothesis, published as such |
| Profile | one row per hromada, one column per pattern, present / partial / absent, plus stars; never summed |
| Language | co-occurrence matrix and scale links, published beside the profiles |
| Publication | presence only, under R1–R7; counts and shares; zone hromadas as raion values (R3); light-derived flags with the R2 lag |

Three rules: a pattern is found, then validated, never assumed — nothing in Annex A enters unless the data produce
it; co-occurrence is part of the evidence; recognition is the final test — a pattern people in the held-up hromadas
do not recognise goes back to step 2.

## 8. Next steps

1. Agree the design (section 5): the five families, the quartile rule, the zone as a separate population, reception
   as a second round.
2. Run `39_quality.py` on the data machine; report counts, clustering and the plain comparison.
3. Compute the revenue Herfindahl and civil-protection change from the caches (script to follow).
4. `40_configurations.py`: tree, QCA, kinds of held-up hromada.
5. Draft the pattern statements; open Annex A.
6. Field round in the Carpathian oblasts through the dispatch series: L2 and B2 first, with the sheet of 5.8;
   review the questions after them.
7. Before the notes come back: `44_measures.py civil` (no network), then the probes for `prozorro`, `nonprofit`,
   `w3`, `formation` on the data machine, and `assemble`. The other lists of section 6 through `places` as they
   are found.
8. For each candidate from the pairs: its nearest measure, `45_candidates.py`, stars; Annex A opened only then.
9. Write-up: a short paper on the method and the patterns, a dispatch per pattern, the profile table in the data
   package. Map page 25 (the observation set) after review.

Decisions needed before step 2: keep all five families or drop own-revenue retention (Q4 2023 break); quartiles or
terciles; whether the field round belongs in this year's dispatch plan.

## Annex A. Expectations written down and set aside (28 Sep 2026, before step 1)

None of these enters the pattern set on its own account.

| Expectation | How it would appear | Evidence so far |
|---|---|---|
| Self-government over own means (low transfer dependency) goes with holding up | transfer dependency among the necessary or sufficient conditions | strong: +0.21 SD on outage retention |
| A local reserve (generators, civil protection, invincibility points) | reserve measures in the sufficient configurations, given autonomy | none; the paper cannot distinguish it from network quality |
| A diverse tax base survives the loss of one employer or the garrison | low revenue Herfindahl, high single-tax share | indirect: garrison sensitivity check; single tax least correlated with PIT |
| Continued investment under fire | capital share held or rising, DREAM projects | modest: +0.09 outside the zone |
| Contested elections and participation between them | candidates per seat, petitions, participatory budget | none for outage |
| Self-formed communities act as one | voluntary amalgamation before 2020, moderate size | none; not yet collected |
| A school in operation keeps families | share of schools in person | none; schools per 10,000 is a fragile negative signal |
| Culture paid from own revenue is kept | culture and extracurricular spending maintained, own-funded | partial: economic and cultural life move together (+0.38) |
| Civic institutions outside the budget | non-profits, youth and veteran spaces, libraries per 10,000 | none; not measured |
| Reception brings work and taxes | 2022 PIT gain, IDP council, IDPs present | oblast level: Carpathian PIT peak 2022 |
| Trust substitutes for weak finances | trust (reSCORE) | oblast level only |
| Balance across the three spheres | small, non-widening distance from the national balance | partial: imbalance rose only in the zone |

If the data confirm most of these, the pattern form still adds thresholds, stars and the language. If they confirm
few and produce configurations not on this list, the method has earned its place.

## Sources

Alexander, C. et al. (1977). *A Pattern Language.* Oxford University Press. Alexander, C. (1979). *The Timeless
Way of Building.* Alexander, C. et al. (1975). *The Oregon Experiment.* Alexander, C. (2002–2005). *The Nature of
Order.* Ragin, C. (2008). *Redesigning Social Inquiry: Fuzzy Sets and Beyond.* Grosfeld, I. and Zhuravskaya, E.
(2015). Cultural vs. economic legacies of empires: evidence from the partition of Poland. *Journal of Comparative
Economics* 43(1). Dietrich, O. et al. (2025). An open-source tool for mapping war destruction at scale in Ukraine
using Sentinel-1 time series. *Communications Earth & Environment.*

Data pages opened 28 Sep 2026: NHSU declarations (data.gov.ua/dataset/a8228262-5576-4a14-beb8-789573573546);
CEC datasets (data.gov.ua, organisation 858f48bc…); State Voter Register open data (drv.gov.ua); Geocadastre open
data (land.gov.ua/open-data); State Tax Service on the single-tax register's public fields (zp.tax.gov.ua, news
681052); Ministry of Justice statistics (minjust.gov.ua/actual-info/stat_info); Prozorro API documentation;
register of non-profits (data.gov.ua/dataset/5c78eb60…); E-DEM petitions; nezlamnist.gov.ua; IDP councils
(minre.gov.ua, 4 Aug 2023); Ukraine 3W (HDX); Sentinel-1 damage (zenodo.org/records/15088349).
