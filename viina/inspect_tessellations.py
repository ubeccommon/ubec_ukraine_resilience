"""Inspect both tessellation GeoJSONs before building admin centres."""
import re
import geopandas as gpd
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 40)

FILES = ["katotth_UA_tess.geojson", "gn_UA_tess.geojson"]

def inspect(path):
    print("=" * 100)
    print(path)
    gdf = gpd.read_file(path, engine="pyogrio")
    print(f"rows={len(gdf)}  crs={gdf.crs}  bounds={[round(b, 3) for b in gdf.total_bounds]}")
    print("geometry types:", gdf.geom_type.value_counts().to_dict())
    print("invalid:", (~gdf.geometry.is_valid).sum(), " empty:", gdf.geometry.is_empty.sum())
    print("-" * 100)
    print(f"{'column':<24}{'dtype':<10}{'nunique':>9}{'nulls':>8}  samples")
    for c in gdf.columns:
        if c == gdf.geometry.name:
            continue
        s = gdf[c]
        try:
            nun = s.nunique(dropna=True)
        except TypeError:
            nun = -1
        samples = s.dropna().astype(str).unique()[:4]
        print(f"{c:<24}{str(s.dtype):<10}{nun:>9}{s.isna().sum():>8}  {list(samples)}")
    print("-" * 100)
    # low-cardinality columns: likely level/category/type fields
    for c in gdf.columns:
        if c == gdf.geometry.name:
            continue
        s = gdf[c]
        if s.dtype == object or str(s.dtype).startswith("str"):
            nun = s.nunique(dropna=True)
            if 1 < nun <= 25:
                print(f"value_counts[{c}]:")
                print(s.value_counts(dropna=False).to_string())
                print()
    # KATOTTH-style codes: UA + 17 digits
    for c in gdf.columns:
        s = gdf[c]
        if s.dtype == object or str(s.dtype).startswith("str"):
            m = s.dropna().astype(str).str.match(r"^UA\d{17}$")
            if m.any():
                print(f"KATOTTH code column candidate: {c}  ({m.sum()}/{m.notna().sum()} match)")
                codes = s.dropna().astype(str)[m]
                print("  prefix lengths present (non-zero tail trimmed):")
                trimmed = codes.str.replace(r"0+$", "", regex=True).str.len()
                print("  ", trimmed.value_counts().sort_index().to_dict())
                print("  sample codes:", codes.head(8).tolist())
    print("head(3):")
    print(gdf.drop(columns=gdf.geometry.name).head(3).to_string())
    return gdf

for f in FILES:
    try:
        inspect(f)
    except Exception as e:
        print(f"ERROR reading {f}: {e!r}")
