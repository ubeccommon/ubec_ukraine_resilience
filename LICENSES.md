# Licences

This repository contains three kinds of material, each under its own licence.
The split matches the publication data package (`publication/data_package/LICENSE.md`).

| Part | Files | Licence | Full text |
|---|---|---|---|
| Code | `*.py`, `*.sh`, `resilience/styles/*.qml`, `publication/build/` | MIT | `LICENSE` |
| Data | `resilience/tidy/*.csv`, `resilience/tidy/*.json`, `viina/strikes_by_month_oblast.csv`, `viina/qgis/meta.json` | Open Database License (ODbL) 1.0 | `LICENSE-ODbL-1.0.txt` |
| Documentation and figures | `*.md` (except licence files), `resilience/docs/`, `publication/` texts, map previews | CC BY 4.0 | `LICENSE-CC-BY-4.0.txt` |

## Why ODbL for the data

Several tables are databases derived from VIINA and OpenStreetMap, both licensed under ODbL 1.0,
which requires publicly used derived databases to carry the same licence. One licence for all
tables avoids per-file mistakes. Maps, figures and texts are "produced works" under ODbL and are
released under CC BY 4.0 with attribution.

## Third-party data

Upstream sources keep their own licences and terms; see `DATA_SOURCES.md` for attribution.
Data whose terms do not allow redistribution (IOM DTM; reSCORE until permission is confirmed;
ACLED) is **not** in this repository. The scripts that retrieve it are included, and users
obtain the data themselves under the provider's terms.
