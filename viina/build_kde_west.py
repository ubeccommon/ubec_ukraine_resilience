"""1 km KDE for the Carpathian zoom (layout 12): qgis/hotspots/kde_<var>_10km_west.tif, events per 1,000 km2.
vars: n12 (last 12 m), nall (all years). Settlement-precision events, Gaussian 10 km bandwidth."""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.features import geometry_mask
from scipy.ndimage import gaussian_filter
from shapely.geometry import box

OUT = Path("qgis"); HOT = OUT / "hotspots"
RES, BW, PAD, NODATA = 1000, 10000, 40000, -9999.0
ctl = gpd.read_file(OUT / "hromada_control.gpkg", engine="pyogrio")
CRS = ctl.crs
outline = gpd.read_file(OUT / "ukraine_outline.gpkg", engine="pyogrio").to_crs(CRS)
win = gpd.GeoSeries([box(2449000, 6057000, 2961000, 6586000)], crs=3857).to_crs(CRS)
xmin, ymin, xmax, ymax = win.total_bounds
xmin, ymin = np.floor((xmin - PAD) / RES) * RES, np.floor((ymin - PAD) / RES) * RES
xmax, ymax = np.ceil((xmax + PAD) / RES) * RES, np.ceil((ymax + PAD) / RES) * RES
nx, ny = int((xmax - xmin) / RES), int((ymax - ymin) / RES)
transform = from_origin(xmin, ymax, RES, RES)
shape = (ny, nx)
inside = ~geometry_mask(outline.geometry, out_shape=shape, transform=transform, invert=False)
occ = geometry_mask(ctl.loc[ctl["occupied"].astype(bool), "geometry"], out_shape=shape, transform=transform, invert=True)
valid = inside & ~occ

stp = pd.read_pickle(OUT / "strike_events_settlement.pkl")
END = stp["date"].max(); START12 = END - pd.Timedelta(days=365)
pts = gpd.GeoDataFrame(stp, geometry=gpd.points_from_xy(stp["longitude"], stp["latitude"]), crs="EPSG:4326").to_crs(CRS)
xe = np.arange(xmin, xmax + RES / 2, RES); ye = np.arange(ymin, ymax + RES / 2, RES)
for name, df in {"n12": pts[pts["date"] >= START12], "nall": pts}.items():
    H, _, _ = np.histogram2d(df.geometry.x, df.geometry.y, bins=[xe, ye])
    H = H.T[::-1]
    dens = gaussian_filter(H, sigma=BW / RES, mode="constant") / (RES / 1000) ** 2 * 1000
    a = np.where(valid, dens, NODATA).astype("float32")
    path = HOT / f"kde_{name}_10km_west.tif"
    with rasterio.open(path, "w", driver="GTiff", height=ny, width=nx, count=1, dtype="float32", crs=CRS.to_wkt(),
                       transform=transform, nodata=NODATA, compress="deflate") as dst:
        dst.write(a, 1)
        dst.set_band_description(1, f"KDE {name} 10 km")
    print(f"{path}: {nx}x{ny} @ 1 km, events in window {H.sum():.0f}, max {dens[valid].max():.1f} /1000 km2")
