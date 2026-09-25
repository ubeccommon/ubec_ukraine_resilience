"""Copy the vector layers QGIS reads several times from one GeoPackage into single-layer FlatGeobuf files
(qgis/fgb/), avoiding SQLite connection errors in headless PyQGIS export."""
from pathlib import Path
import pyogrio
import geopandas as gpd

OUT = Path("qgis"); FGB = OUT / "fgb"; FGB.mkdir(exist_ok=True)
jobs = [(OUT / "surfaces" / "isolines.gpkg", lyr, f"isolines_{lyr}.fgb")
        for lyr, _ in pyogrio.list_layers(OUT / "surfaces" / "isolines.gpkg")]
jobs += [(OUT / "unit_stats.gpkg", lyr, f"unit_stats_{lyr}.fgb") for lyr in ("raion_poly", "hromada_pt")]
jobs += [(OUT / "hotspots" / "gi_hromada.gpkg", "hromada_pt", "gi_hromada_pt.fgb")]
for src, lyr, dst in jobs:
    g = gpd.read_file(src, layer=lyr, engine="pyogrio")
    for c in g.columns:
        if g[c].dtype == bool:
            g[c] = g[c].astype(int)
    g.to_file(FGB / dst, driver="FlatGeobuf", engine="pyogrio")
    print(f"{dst}: {len(g)} features")
