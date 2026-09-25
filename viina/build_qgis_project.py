#!/usr/bin/env python3
"""
build_qgis_project.py — run with the SYSTEM python that has PyQGIS (not the venv):

    cd ~/Documents/GEODATA/ukraine/ukraine_strike_data/viina
    deactivate 2>/dev/null; /usr/bin/python3 build_qgis_project.py

Creates qgis/ukraine_strikes.qgz with styled layers and A4 landscape layouts, exports each to qgis/maps/*.png and *.pdf.
 01–05  original products (risk index, settlements, points, alert hours, Carpathian H3 zoom)
 06     IDW strike surface + isolines (national)
 07     IDW vs ordinary kriging (strike counts)
 08     weighted surfaces: recency score / per-capita rate
 09     alert hours — kriging + isobars
 10     kernel density (25 km): unweighted / n_reports-weighted / recency-weighted
 11     Getis-Ord Gi* (60 km band, FDR) + LISA outliers: strikes / alert hours
 12     Carpathian zoom — KDE 10 km (1 km grid), points, alert isobars
 13     Carpathian zoom — Gi*/LISA
 14     resilience: alert-hour exposure x institutional capacity (bivariate 3x3, national terciles)
 15     resilience: strike exposure x capacity (bivariate, variant)
 16     resilience: night-light recovery quintiles (lit pixels)
 17     Carpathian zoom — alert exposure x capacity, regional terciles
 18     oblast context — reSCORE 2024 citizen resilience (difference from national) + IDPs present
 19     trajectories: recent night-light deficit x capacity (bivariate 3x3, national terciles)
 20     trajectories: summer-2024 outage loss (quintiles) | change since H2 2023 vs own noise
Inputs from the venv steps: qgis/*.gpkg, qgis/surfaces/*.tif, qgis/hotspots/*, qgis/fgb/*.fgb (export_fgb.py),
qgis/meta.json (write_meta.py: data dates for the captions),
../resilience/resilience_maps.gpkg (resilience/13_bivariate.py) for maps 14–17,
layer hromada_trajectories + tidy/trajectory_classes.json + tidy/trajectory_models.csv
(resilience/22_trajectories.py) for maps 19–20 (captions read the current model results).
Requires: sudo apt install qgis python3-qgis
"""
import os, json, csv, resource
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# many layers share files; parallel export opens one connection per layer and thread
_soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
resource.setrlimit(resource.RLIMIT_NOFILE, (min(max(_soft, 65536), _hard), _hard))
print("open-file limit:", resource.getrlimit(resource.RLIMIT_NOFILE))

from qgis.core import (
    Qgis, QgsLayoutItemPage,
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
    QgsGraduatedSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsClassificationJenks,
    QgsSymbol, QgsFillSymbol, QgsMarkerSymbol, QgsLineSymbol, QgsGradientColorRamp, QgsRendererRange,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend, QgsLayoutItemScaleBar,
    QgsLayoutPoint, QgsLayoutSize, QgsLayoutExporter, QgsRectangle,
    QgsTextFormat, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
    QgsReferencedRectangle, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer,
    QgsBilinearRasterResampler, QgsLegendStyle, QgsMapLayerLegendUtils, QgsLayoutItemShape,
)
from qgis.PyQt.QtGui import QColor, QFont

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "qgis")
MAPS = os.path.join(DATA, "maps")
SURF = os.path.join(DATA, "surfaces")
HOT = os.path.join(DATA, "hotspots")
AU = os.path.join(DATA, "admin_units.gpkg")
FGB = os.path.join(DATA, "fgb")     # single-layer copies (export_fgb.py)
RES = os.path.normpath(os.path.join(HERE, "..", "resilience", "resilience_maps.gpkg"))
os.makedirs(MAPS, exist_ok=True)
MM = Qgis.LayoutUnit.Millimeters
LS = getattr(QgsLegendStyle, "Style", QgsLegendStyle)

META = {}
_mp = os.path.join(DATA, "meta.json")
if os.path.exists(_mp):
    with open(_mp, encoding="utf-8") as f:
        META = json.load(f)
else:
    print("!! qgis/meta.json missing — run write_meta.py; captions will show '?' for dates")
def md(key):
    return META.get(key, "?")

qgs = QgsApplication([], False)
QgsApplication.setPrefixPath("/usr", True)
qgs.initQgis()

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
project.setTitle("Russian strikes on Ukraine — VIINA / air-raid data")
root = project.layerTreeRoot()

# ------------------------------------------------------------------ helpers
def add_vector(path, name, layer=None, group=None, subset=None):
    if not os.path.exists(path):
        print(f"!! missing {path}"); return None
    uri = path if layer is None else f"{path}|layername={layer}"
    lyr = QgsVectorLayer(uri, name, "ogr")
    if not lyr.isValid():
        print(f"!! could not load {uri}"); return None
    if subset:
        lyr.setSubsetString(subset)
    project.addMapLayer(lyr, group is None)
    if group is not None:
        group.addLayer(lyr)
    return lyr

def add_raster(path, name, group=None, opacity=1.0):
    if not os.path.exists(path):
        print(f"!! missing {path}"); return None
    lyr = QgsRasterLayer(path, name)
    if not lyr.isValid():
        print(f"!! could not load {path}"); return None
    project.addMapLayer(lyr, group is None)
    if group is not None:
        group.addLayer(lyr)
    lyr.setOpacity(opacity)
    rf = lyr.resampleFilter()
    rf.setZoomedInResampler(QgsBilinearRasterResampler())
    rf.setZoomedOutResampler(QgsBilinearRasterResampler())
    return lyr

def ramp(c1, c2):
    return QgsGradientColorRamp(QColor(c1), QColor(c2))

def interp(stops, n):
    cs = [QColor(s) for s in stops]
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        p = t * (len(cs) - 1); j = min(int(p), len(cs) - 2); f = p - j
        a, b = cs[j], cs[j + 1]
        out.append(QColor(int(a.red() + (b.red() - a.red()) * f), int(a.green() + (b.green() - a.green()) * f),
                          int(a.blue() + (b.blue() - a.blue()) * f)).name())
    return out

def graduated(lyr, field, k, c1, c2, geom="fill", outline="#00000000", outline_w=0.1, size=None, fmt=None):
    sym = QgsSymbol.defaultSymbol(lyr.geometryType())
    if geom == "fill":
        sym.symbolLayer(0).setStrokeColor(QColor(outline))
        sym.symbolLayer(0).setStrokeWidth(outline_w)
    r = QgsGraduatedSymbolRenderer(field)
    r.setSourceSymbol(sym)
    r.setSourceColorRamp(ramp(c1, c2))
    r.setClassificationMethod(QgsClassificationJenks())
    r.updateClasses(lyr, k)
    if fmt:
        r.setLabelFormat(fmt)
    if size:
        r.setSymbolSizes(size[0], size[1])
    lyr.setRenderer(r)
    lyr.triggerRepaint()

def graduated_fixed(lyr, field, breaks, stops, outline="#00000000", outline_w=0.1):
    cols = interp(stops, len(breaks) - 1)
    ranges = []
    for i in range(len(breaks) - 1):
        sym = QgsFillSymbol.createSimple({"color": cols[i], "outline_color": outline, "outline_width": str(outline_w)})
        ranges.append(QgsRendererRange(breaks[i], breaks[i + 1], sym, f"{breaks[i]:,g} – {breaks[i + 1]:,g}"))
    lyr.setRenderer(QgsGraduatedSymbolRenderer(field, ranges))
    lyr.triggerRepaint()

DISCRETE = getattr(getattr(Qgis, "ShaderInterpolationMethod", None), "Discrete", None) or QgsColorRampShader.Discrete

def raster_classes(lyr, breaks, stops, transparent_first=True):
    """weather-map style: discrete bands, value <= break gets that band's colour."""
    if lyr is None:
        return
    cols = interp(stops, len(breaks) + 1)
    items = []
    for i, b in enumerate(breaks):
        c = QColor(cols[i])
        if i == 0 and transparent_first:
            c.setAlpha(0)
        lab = f"< {b:,g}" if i == 0 else f"{breaks[i - 1]:,g} – {b:,g}"
        items.append(QgsColorRampShader.ColorRampItem(float(b), c, lab))
    items.append(QgsColorRampShader.ColorRampItem(float("inf"), QColor(cols[-1]), f"≥ {breaks[-1]:,g}"))
    sh = QgsColorRampShader()
    sh.setColorRampType(DISCRETE)
    sh.setColorRampItemList(items)
    sh.setMinimumValue(0.0); sh.setMaximumValue(float(breaks[-1]))
    rs = QgsRasterShader(); rs.setRasterShaderFunction(sh)
    r = QgsSingleBandPseudoColorRenderer(lyr.dataProvider(), 1, rs)
    r.setClassificationMin(0.0); r.setClassificationMax(float(breaks[-1]))
    lyr.setRenderer(r)
    lyr.triggerRepaint()

def label(lyr, field, size=8, color="#333333", placement=None, buffer=False, bold=False):
    s = QgsPalLayerSettings()
    s.fieldName = field
    tf = QgsTextFormat(); f = QFont("DejaVu Sans"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(color))
    if buffer:
        b = tf.buffer(); b.setEnabled(True); b.setSize(0.7); b.setColor(QColor("#ffffff")); tf.setBuffer(b)
    s.setFormat(tf)
    if placement is None:
        gt = lyr.geometryType()
        if gt == Qgis.GeometryType.Polygon:
            placement = Qgis.LabelPlacement.OverPoint
        elif gt == Qgis.GeometryType.Line:
            placement = Qgis.LabelPlacement.Curved
        else:
            placement = Qgis.LabelPlacement.AroundPoint
    s.placement = placement
    if lyr.geometryType() == Qgis.GeometryType.Line:
        try:
            s.repeatDistance = 70
            s.repeatDistanceUnit = Qgis.RenderUnit.Millimeters
        except Exception:
            pass
    lyr.setLabelsEnabled(True)
    lyr.setLabeling(QgsVectorLayerSimpleLabeling(s))

def line_style(lyr, color="#222222", width=0.3):
    if lyr:
        lyr.renderer().setSymbol(QgsLineSymbol.createSimple({"line_color": color, "line_width": str(width)}))

def boundary_style(lyr, color="#555555", width=0.2):
    if lyr:
        lyr.renderer().setSymbol(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": color, "outline_width": str(width)}))

def isolines(layer_name, title, group, color="#222222", subset=None, width=0.3):
    lyr = add_vector(os.path.join(FGB, f"isolines_{layer_name}.fgb"), title, group=group, subset=subset)
    if lyr:
        line_style(lyr, color, width)
        label(lyr, "label", 6.5, color, buffer=True)
    return lyr

GI_CLASSES = [("hot99", "#b2182b", "Hot spot, 99 %"), ("hot95", "#ef8a62", "Hot spot, 95 %"), ("hot90", "#fddbc7", "Hot spot, 90 %"),
              ("ns", "240,240,240,120", "Not significant"),
              ("cold90", "#d1e5f0", "Cold spot, 90 %"), ("cold95", "#67a9cf", "Cold spot, 95 %"), ("cold99", "#2166ac", "Cold spot, 99 %")]

def gi_style(lyr, field):
    if lyr:
        cats = [QgsRendererCategory(k, QgsFillSymbol.createSimple({"color": c, "outline_color": "0,0,0,0"}), lab) for k, c, lab in GI_CLASSES]
        lyr.setRenderer(QgsCategorizedSymbolRenderer(field, cats))

def lisa_style(lyr, field):
    if lyr:
        spec = [("HH", "triangle", "#67000d", "LISA high–high (cluster core)"),
                ("HL", "diamond", "#e7298a", "LISA high–low (isolated high outlier)")]
        cats = [QgsRendererCategory(k, QgsMarkerSymbol.createSimple({"name": s, "color": c, "outline_color": "#ffffff",
                                                                     "outline_width": "0.2", "size": "2.4"}), lab)
                for k, s, c, lab in spec]
        lyr.setRenderer(QgsCategorizedSymbolRenderer(field, cats))

def fdr_outline(lyr, width=0.45, color="#000000"):
    if lyr:
        lyr.renderer().setSymbol(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": color, "outline_width": str(width)}))

# ------------------------------------------------------------------ original layers (bottom -> top)
osm = QgsRasterLayer("type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0", "OpenStreetMap", "wms")
if osm.isValid():
    project.addMapLayer(osm)
    osm.setOpacity(0.55)
else:
    osm = None

outline = add_vector(os.path.join(DATA, "ukraine_outline.gpkg"), "Ukraine outline")
if outline:
    outline.renderer().setSymbol(QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "#333333", "outline_width": "0.6"}))

oblasts = add_vector(os.path.join(DATA, "oblasts.gpkg"), "Oblasts — air-raid alert hours (12 m, oblast-level records only)")
if oblasts:
    graduated(oblasts, "alert_hours_12m", 6, "#fff5eb", "#7f2704", outline="#666666", outline_w=0.25)
    label(oblasts, "ADM1_NAME", 7)

hexes = add_vector(os.path.join(DATA, "risk_index_h3r5.gpkg"), "Strike risk index (H3 r5, 6-month half-life)")
if hexes:
    graduated(hexes, "score_idx", 7, "#ffffcc", "#800026")
    hexes.setOpacity(0.85)

west = add_vector(os.path.join(DATA, "risk_index_west_h3r7.gpkg"), "Strike risk index — Carpathian region (H3 r7)")
if west:
    graduated(west, "score_idx", 6, "#ffffcc", "#800026")
    west.setOpacity(0.85)

settl = add_vector(os.path.join(DATA, "strikes_by_settlement.gpkg"), "Settlements — strike events, last 12 m")
if settl:
    settl.setSubsetString('"n_12m" > 0')
    graduated(settl, "n_12m", 6, "#fee0d2", "#67000d")

pts = add_vector(os.path.join(DATA, "strike_points_12m.gpkg"), "Strike events, last 12 m (points)")
if pts:
    colors = {"airstrike/missile": "#b2182b", "UAV": "#ef8a62", "artillery": "#67001f", "air defence engagement": "#999999"}
    cats = []
    for k, c in colors.items():
        m = QgsMarkerSymbol.createSimple({"name": "circle", "color": c, "outline_color": "#00000000", "size": "1.6"})
        cats.append(QgsRendererCategory(k, m, k))
    pts.setRenderer(QgsCategorizedSymbolRenderer("strike_type", cats))
    pts.setOpacity(0.7)

# ------------------------------------------------------------------ new layers (steps 1–4), in their own group
G = root.addGroup("Admin units, surfaces & hot spots")

obl_b = add_vector(AU, "Oblast boundaries", layer="oblast", group=G); boundary_style(obl_b, "#444444", 0.35)
rai_b = add_vector(AU, "Raion boundaries", layer="raion", group=G); boundary_style(rai_b, "#888888", 0.15)
hro_b = add_vector(AU, "Hromada boundaries", layer="hromada", group=G); boundary_style(hro_b, "#9a9a9a", 0.1)

occ = add_vector(os.path.join(DATA, "hromada_control.gpkg"), "Not under UA control (excluded)", group=G, subset='"occupied" = 1')
if occ:
    occ.renderer().setSymbol(QgsFillSymbol.createSimple({"color": "90,90,90,255", "style": "b_diagonal",
                                                         "outline_color": "#777777", "outline_width": "0.1"}))

alert_rai = add_vector(os.path.join(FGB, "unit_stats_raion_poly.fgb"), "Alert hours, 12 m (pop.-weighted, by raion)", group=G)
if alert_rai:
    graduated_fixed(alert_rai, "alert_hp_12m", [0, 100, 250, 500, 1000, 2000, 3000, 5000, 8000],
                    ["#fff5eb", "#fdae6b", "#e6550d", "#7f2704"], outline="#bbbbbb", outline_w=0.1)

cities = add_vector(os.path.join(FGB, "unit_stats_hromada_pt.fgb"), "Hromadas with ≥ 50 events (12 m)", group=G, subset='"n_12m" >= 50')
if cities:
    cities.renderer().setSymbol(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#000000", "size": "1.0"}))
    label(cities, "label", 7, "#111111", buffer=True)

WEST_TOWNS = ["Львів", "Івано-Франківськ", "Ужгород", "Чернівці", "Тернопіль", "Луцьк", "Верховина", "Косів", "Рахів",
              "Коломия", "Надвірна", "Мукачево", "Хуст", "Дрогобич", "Стрий", "Яремче", "Самбір", "Калуш"]
west_subset = ('"label" IN (' + ",".join("'" + t.replace("'", "''") + "'" for t in WEST_TOWNS) +
               ") AND \"k1\" IN ('07','21','26','46','61','73')")
west_lbl = add_vector(os.path.join(FGB, "unit_stats_hromada_pt.fgb"), "Western towns", group=G, subset=west_subset)
if west_lbl:
    west_lbl.renderer().setSymbol(QgsMarkerSymbol.createSimple({"name": "circle", "color": "#000000", "size": "1.0"}))
    label(west_lbl, "label", 7.5, "#111111", buffer=True, bold=True)

STRIKE = ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
ALERT = ["#f2f0f7", "#bcbddc", "#807dba", "#54278f", "#3f007d"]
KDE = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]
B_COUNT = [0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 300]
B_RATE = [0.5, 1, 2, 5, 10, 20, 50, 100, 200, 400]
B_ALERT = [100, 250, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
B_KDE25 = [0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]
B_KDE10 = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 3000]

r_n12_idw = add_raster(os.path.join(SURF, "strike_n12_idw.tif"), "Strike events per hromada, 12 m — IDW", G, 0.85)
r_n12_kr = add_raster(os.path.join(SURF, "strike_n12_krige.tif"), "Strike events per hromada, 12 m — kriging", G, 0.85)
r_score = add_raster(os.path.join(SURF, "strike_score_idw.tif"), "Recency-weighted score — IDW", G, 0.85)
r_rate = add_raster(os.path.join(SURF, "strike_rate12_idw.tif"), "Events per 100k inhabitants, 12 m — IDW", G, 0.85)
r_alert = add_raster(os.path.join(SURF, "alert_h12_krige.tif"), "Alert hours, 12 m — kriging", G, 0.85)
for r, b, c, tr in [(r_n12_idw, B_COUNT, STRIKE, True), (r_n12_kr, B_COUNT, STRIKE, True), (r_score, B_COUNT, STRIKE, True),
                    (r_rate, B_RATE, STRIKE, True), (r_alert, B_ALERT, ALERT, False)]:
    raster_classes(r, b, c, tr)

NO_SMALL = "\"label\" NOT IN ('1','2')"          # IDW rings at 1–2 events around every small town are clutter
i_n12_idw = isolines("strike_n12_idw", "Isolines — strike events (IDW, from 5)", G, subset=NO_SMALL)
i_n12_kr = isolines("strike_n12_krige", "Isolines — strike events (kriging)", G)
i_score = isolines("strike_score_idw", "Isolines — recency score (IDW, from 5)", G, subset="\"label\" NOT IN ('0.5','1','2')")
i_rate = isolines("strike_rate12_idw", "Isolines — per 100k (IDW, from 5)", G, subset=NO_SMALL)
i_alert = isolines("alert_h12_krige", "Isobars — alert hours (kriging)", G, color="#2d004b")
i_alert_w = isolines("alert_h12_idw", "Isobars — alert hours (IDW)", G, color="#2d004b")

k_n12 = add_raster(os.path.join(HOT, "kde_n12_25km.tif"), "KDE 25 km, events per 1,000 km²", G, 0.9)
k_rep = add_raster(os.path.join(HOT, "kde_rep12_25km.tif"), "KDE 25 km — reports 12 m", G, 0.9)
k_rec = add_raster(os.path.join(HOT, "kde_rec_25km.tif"), "KDE 25 km — recency-weighted, all years", G, 0.9)
kw_path = os.path.join(HOT, "kde_n12_10km_west.tif")
k_w10 = add_raster(kw_path if os.path.exists(kw_path) else os.path.join(HOT, "kde_n12_10km.tif"),
                   "KDE 10 km, events 12 m per 1,000 km²", G, 0.8)
for r, b in [(k_n12, B_KDE25), (k_rep, B_KDE25), (k_rec, B_KDE25), (k_w10, B_KDE10)]:
    raster_classes(r, b, KDE, True)

GI = os.path.join(HOT, "gi_hromada.gpkg")
gi_n12 = add_vector(GI, "Gi* — strike events 12 m (60 km band)", layer="hromada_poly", group=G); gi_style(gi_n12, "n12_db60_gcls")
gi_alert = add_vector(GI, "Gi* — alert hours 12 m (60 km band)", layer="hromada_poly", group=G); gi_style(gi_alert, "alert_db60_gcls")
fdr_n12 = add_vector(GI, "Significant after FDR (q = 0.05)", layer="hromada_poly", group=G, subset='"n12_db60_gfdr" <> 0'); fdr_outline(fdr_n12)
fdr_alert = add_vector(GI, "Significant after FDR (q = 0.05) — alerts", layer="hromada_poly", group=G, subset='"alert_db60_gfdr" <> 0')
fdr_outline(fdr_alert, 0.12, "#333333")
lisa = add_vector(os.path.join(FGB, "gi_hromada_pt.fgb"), "LISA — strike events", group=G,
                  subset="\"n12_db60_lcls\" IN ('HH','HL')"); lisa_style(lisa, "n12_db60_lcls")

# ------------------------------------------------------------------ resilience layers (maps 14–17)
R = root.addGroup("Resilience v1.1 (capacity, recovery)")
BV_PAL = {"11": "#e8e8e8", "12": "#ace4e4", "13": "#5ac8c8",
          "21": "#dfb0d6", "22": "#a5add3", "23": "#5698b9",
          "31": "#be64ac", "32": "#8c62aa", "33": "#3b4994"}
REC_PAL = [("1", "#d7191c", "Lowest 20 % (least recovered)"), ("2", "#fdae61", "20–40 %"), ("3", "#ffffbf", "40–60 %"),
           ("4", "#abd9e9", "60–80 %"), ("5", "#2c7bb6", "Highest 20 % (most recovered)"),
           ("na", "#ffffff", "No value (< 10 lit pixels or missing)")]
E_LBL = {"1": "low", "2": "medium", "3": "high"}

def cat_style(lyr, field, spec, outline="#ffffff", outline_w=0.05):
    if lyr:
        cats = [QgsRendererCategory(v, QgsFillSymbol.createSimple({"color": c, "outline_color": outline,
                                                                    "outline_width": str(outline_w)}), lab)
                for v, c, lab in spec]
        lyr.setRenderer(QgsCategorizedSymbolRenderer(field, cats))

def bv_style(lyr, field, a="exposure", b="capacity"):
    spec = [(k, c, f"{a} {E_LBL[k[0]]} · {b} {E_LBL[k[1]]}") for k, c in BV_PAL.items()]
    spec.append(("na", "#ffffff", "No data"))
    cat_style(lyr, field, spec)

bv_alt = add_vector(RES, "Exposure (alert hours) × capacity — national terciles", layer="hromada_bivariate",
                    group=R, subset="\"occupied\" = 0"); bv_style(bv_alt, "bv_alt")
bv_str = add_vector(RES, "Exposure (strikes since 2022) × capacity — national classes", layer="hromada_bivariate",
                    group=R, subset="\"occupied\" = 0"); bv_style(bv_str, "bv_str")
bv_carp = add_vector(RES, "Carpathian: exposure × capacity — regional terciles", layer="hromada_bivariate",
                     group=R, subset="\"carp\" = 1 AND \"occupied\" = 0"); bv_style(bv_carp, "bv_carp")
rec_q = add_vector(RES, "Night-light recovery 2021→2024 (lit pixels), quintiles", layer="hromada_bivariate",
                   group=R, subset="\"occupied\" = 0"); cat_style(rec_q, "recovery_q", REC_PAL)
# oblast context (resilience/16_oblast_context.py): reSCORE 2024 vs national, IDPs present
CTX = [("trust_local_admin", "Trust in town or village administration"),
       ("community_cohesion", "Community cohesion"),
       ("civic_engagement", "Civic engagement"),
       ("belonging_settlement", "Belonging to the settlement"),
       ("economic_security", "Economic security"),
       ("mental_wellbeing", "Mental wellbeing"),
       ("locality_satisfaction", "Locality satisfaction")]
DIV = [(-10.0, -1.0, "#ca0020", "more than 1 point below national"),
       (-1.0, -0.5, "#f4a582", "0.5 – 1 below"),
       (-0.5, 0.5, "#f7f7f7", "within ±0.5 (not significant)"),
       (0.5, 1.0, "#92c5de", "0.5 – 1 above"),
       (1.0, 10.0, "#0571b0", "more than 1 point above national")]

def div_style(lyr, field):
    if lyr:
        rr = [QgsRendererRange(a, b, QgsFillSymbol.createSimple({"color": c, "outline_color": "#666666",
                                                                 "outline_width": "0.15"}), lab)
              for a, b, c, lab in DIV]
        lyr.setRenderer(QgsGraduatedSymbolRenderer(field, rr))

# first instance of oblast_context opened from the gpkg is a throwaway (page 18 panel 1 stayed empty when
# the first-opened instance was drawn); it is kept hidden in the group and used nowhere
ctx_probe = add_vector(RES, "oblast_context (probe, unused)", layer="oblast_context", group=R)
if ctx_probe:
    NO_LEGEND_EXTRA = id(ctx_probe)
ctx_layers = []
for fld, lab in CTX:
    lyr = add_vector(RES, f"reSCORE 2024 — {lab} (vs national)", layer="oblast_context", group=R)
    div_style(lyr, f"{fld}_2024_vs_nat")
    ctx_layers.append((lyr, lab))
ctx_leg = add_vector(RES, "reSCORE 2024 — classes (legend only)", layer="oblast_context", group=R)
div_style(ctx_leg, "trust_local_admin_2024_vs_nat")       # dedicated legend layer, not drawn in any panel
idp_ctx = add_vector(RES, "IDPs present per 1,000 pre-war residents (IOM DTM)", layer="oblast_context", group=R)
if idp_ctx:
    graduated_fixed(idp_ctx, "idp_present_est_per1k", [0, 50, 75, 100, 150, 250],
                    ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"], outline="#666666", outline_w=0.15)

# trajectories (resilience/22_trajectories.py): maps 19–20
RES_TIDY = os.path.normpath(os.path.join(HERE, "..", "resilience", "tidy"))
TC = {}
_tc = os.path.join(RES_TIDY, "trajectory_classes.json")
if os.path.exists(_tc):
    with open(_tc, encoding="utf-8") as f:
        TC = json.load(f)
else:
    print("!! trajectory_classes.json missing — run resilience/22_trajectories.py")
TRAJ = {}
_tm = os.path.join(RES_TIDY, "trajectory_models.csv")
if os.path.exists(_tm):
    with open(_tm, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            TRAJ[(r["outcome"], r["spec"])] = r

def tb(outcome, spec, coef="cap"):
    r = TRAJ.get((outcome, spec))
    if not r or not r.get(f"b_{coef}"):
        return "?"
    return f"{float(r[f'b_{coef}']):+.2f}, t {float(r[f't_{coef}']):.1f}"

def pct(v):
    return f"{100 * v:.0f} %"

_q = TC.get("s24_quintiles", [])
if len(_q) == 4:
    S24_LBL = [f"< {pct(_q[0])} of H2 2023 (largest loss)", f"{pct(_q[0])} – {pct(_q[1])}",
               f"{pct(_q[1])} – {pct(_q[2])}", f"{pct(_q[2])} – {pct(_q[3])}", f"> {pct(_q[3])} (smallest loss)"]
else:
    S24_LBL = ["Lowest 20 % (largest loss)", "20–40 %", "40–60 %", "60–80 %", "Highest 20 % (smallest loss)"]
S24_PAL = [(str(i + 1), c, S24_LBL[i]) for i, c in enumerate(["#d7191c", "#fdae61", "#ffffbf", "#abd9e9", "#2c7bb6"])]
S24_PAL.append(("na", "#ffffff", "No value (< 10 lit pixels or missing)"))
CHG_PAL = [("declined", "#d7191c", "Declined (beyond own noise)"), ("stable", "#e0e0e0", "Stable (within ±2 × noise)"),
           ("improved", "#2c7bb6", "Improved (beyond own noise)"), ("na", "#ffffff", "No value (< 10 lit pixels)")]

# throwaway first instance (same gpkg quirk as oblast_context on page 18)
traj_probe = add_vector(RES, "hromada_trajectories (probe, unused)", layer="hromada_trajectories", group=R)
traj_bv = add_vector(RES, "Recent light deficit × capacity — national terciles", layer="hromada_trajectories",
                     group=R, subset="\"occupied\" = 0")
bv_style(traj_bv, "bv_rec_cap", a="light deficit")
traj_s24 = add_vector(RES, "Summer-2024 outage: light Jun–Jul 2024 vs H2 2023, quintiles", layer="hromada_trajectories",
                      group=R, subset="\"occupied\" = 0")
cat_style(traj_s24, "s24_q", S24_PAL)
traj_chg = add_vector(RES, "Change last 12 months vs H2 2023 (against own pre-war noise)", layer="hromada_trajectories",
                      group=R, subset="\"occupied\" = 0")
cat_style(traj_chg, "chg_cls", CHG_PAL)
R.setItemVisibilityChecked(False)

for lyr, vis in [(osm, True), (outline, True), (oblasts, False), (hexes, True), (west, False), (settl, True), (pts, False)]:
    if lyr:
        node = root.findLayer(lyr.id())
        if node: node.setItemVisibilityChecked(vis)
G.setItemVisibilityChecked(False)

# ------------------------------------------------------------------ layouts
UA_RECT = QgsRectangle(2450000, 5500000, 4520000, 6900000)
WEST_RECT = QgsRectangle(2449000, 6057000, 2961000, 6586000)
CARP_RECT = QgsRectangle(2430000, 6040000, 3100000, 6615000)   # Lviv, Zakarpattia, Ivano-Frankivsk, Chernivtsi
NO_LEGEND = {id(x) for x in (osm, outline, obl_b, rai_b, hro_b, cities, west_lbl) if x}

def stack(layers):
    """layers given bottom -> top; QgsLayoutItemMap wants top first."""
    return [l for l in reversed(layers) if l]

def add_text(layout, text, x, y, w, h, size=8, bold=False):
    t = QgsLayoutItemLabel(layout); t.setText(text)
    tf = QgsTextFormat(); f = QFont("DejaVu Sans"); f.setBold(bold); tf.setFont(f); tf.setSize(size); t.setTextFormat(tf)
    layout.addLayoutItem(t)
    t.attemptMove(QgsLayoutPoint(x, y, MM)); t.attemptResize(QgsLayoutSize(w, h, MM))
    return t

def new_layout(name):
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(name)
    layout.pageCollection().page(0).setPageSize("A4", QgsLayoutItemPage.Orientation.Landscape)
    return layout

def add_map(layout, layers, x, y, w, h, extent):
    m = QgsLayoutItemMap(layout)
    m.setRect(0, 0, w, h)
    m.setLayers(stack(layers))
    m.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    m.setBackgroundColor(QColor("#ffffff"))
    m.setFrameEnabled(True)
    layout.addLayoutItem(m)
    m.attemptMove(QgsLayoutPoint(x, y, MM)); m.attemptResize(QgsLayoutSize(w, h, MM))
    m.zoomToExtent(extent)
    return m

def style_legend(lg, size=7.0):
    for sid, sz, bold in [(LS.Title, size + 2, True), (LS.Group, size + 1, True),
                          (LS.Subgroup, size + 0.5, True), (LS.SymbolLabel, size, False)]:
        st = lg.style(sid)
        tf = st.textFormat(); f = QFont("DejaVu Sans"); f.setBold(bold); tf.setFont(f); tf.setSize(sz)
        st.setTextFormat(tf)
        lg.setStyle(sid, st)
    lg.setSymbolHeight(3.0); lg.setSymbolWidth(5.0)

def add_legend(layout, m, entries, x, y, w, h, cols=1, title=None, split=True):
    """entries: layers or (layer, legend title), top -> bottom."""
    lg = QgsLayoutItemLegend(layout)
    lg.setTitle(title if title is not None else ("Legend" if cols == 1 else ""))
    if m is not None:
        lg.setLinkedMap(m)
    lg.setAutoUpdateModel(False)
    model = lg.model(); grp = model.rootGroup(); grp.clear()
    seen = set()
    for e in entries:
        l, nm = (e if isinstance(e, tuple) else (e, None))
        if not l or id(l) in NO_LEGEND or id(l) in seen:
            continue
        nl = grp.addLayer(l); seen.add(id(l))
        if nm:                                           # title for this legend only; layer name unchanged
            nl.setCustomProperty("legend/title-label", nm)
            model.refreshLayerLegend(nl)
        if isinstance(l, QgsRasterLayer):                # hide the "Band 1 (Gray)" node
            nodes = model.layerLegendNodes(nl)
            if len(nodes) > 1:
                QgsMapLayerLegendUtils.setLegendNodeOrder(nl, list(range(1, len(nodes))))
                model.refreshLayerLegend(nl)
    style_legend(lg)
    lg.setColumnCount(cols); lg.setSplitLayer(split and cols > 1)
    layout.addLayoutItem(lg)
    lg.attemptMove(QgsLayoutPoint(x, y, MM)); lg.attemptResize(QgsLayoutSize(w, h, MM))
    return lg

def add_scalebar(layout, m, x, y, km):
    sb = QgsLayoutItemScaleBar(layout)
    sb.setLinkedMap(m); sb.setStyle("Line Ticks Up"); sb.setUnits(Qgis.DistanceUnit.Kilometers)
    sb.setNumberOfSegments(2); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(km); sb.setUnitLabel("km")
    tf = QgsTextFormat(); tf.setFont(QFont("DejaVu Sans")); tf.setSize(7); sb.setTextFormat(tf)
    layout.addLayoutItem(sb)
    sb.attemptMove(QgsLayoutPoint(x, y, MM))

def make_layout(name, title, visible_layers, subtitle="", extent=None, scale_km=100, legend=None):
    layout = new_layout(name)
    m = add_map(layout, visible_layers, 8, 22, 215, 165, extent or UA_RECT)
    add_text(layout, title, 8, 6, 280, 10, 15, bold=True)
    if subtitle:
        add_text(layout, subtitle, 8, 190, 280, 16, 7.5)
    add_legend(layout, m, legend or list(reversed(visible_layers)), 227, 22, 64, 148)
    add_scalebar(layout, m, 227, 175, scale_km)
    project.layoutManager().addLayout(layout)
    return layout

def make_layout_multi(name, title, panels, subtitle="", extent=None, scale_km=200, legend=None, legend_cols=3,
                      legend_split=True):
    """panels: list of (layers bottom->top, caption). Maps side by side, one shared legend below."""
    layout = new_layout(name)
    ext = extent or UA_RECT
    n, gap, W = len(panels), 4.0, 281.0
    w = (W - gap * (n - 1)) / n
    h = min(w * ext.height() / ext.width(), 112.0)
    maps, all_layers = [], []
    for i, (layers, cap) in enumerate(panels):
        x = 8 + i * (w + gap)
        maps.append(add_map(layout, layers, x, 27, w, h, ext))
        add_text(layout, cap, x, 21, w, 6, 8.5, bold=True)
        all_layers += list(reversed([l for l in layers if l]))
    add_text(layout, title, 8, 6, 280, 10, 15, bold=True)
    y0 = 27 + h + 3
    add_scalebar(layout, maps[0], 8, y0, scale_km)
    add_legend(layout, maps[0], legend or all_layers, 60, y0, 229, max(20.0, 187 - y0), legend_cols,
               split=legend_split)
    if subtitle:
        add_text(layout, subtitle, 8, 190, 280, 16, 7.5)
    project.layoutManager().addLayout(layout)
    return layout

def make_layout_grid(name, title, panels, cols=4, subtitle="", extent=None, legend=None, legend_cols=2):
    """panels: list of (layers bottom->top, caption); maps in a cols x rows grid, shared legend below."""
    layout = new_layout(name)
    ext = extent or UA_RECT
    n = len(panels)
    rows = (n + cols - 1) // cols
    gap, W = 3.0, 281.0
    w = (W - gap * (cols - 1)) / cols
    h = w * ext.height() / ext.width()
    maps = []
    for i, (layers, cap) in enumerate(panels):
        r, c = divmod(i, cols)
        x, y = 8 + c * (w + gap), 21 + r * (h + 8)
        add_text(layout, cap, x, y, w, 5, 7.5, bold=True)
        maps.append(add_map(layout, layers, x, y + 5, w, h, ext))
    add_text(layout, title, 8, 6, 280, 10, 15, bold=True)
    y0 = 21 + rows * (h + 8) + 1
    if legend:
        add_legend(layout, None, legend, 8, y0, 281, max(18.0, 184 - y0), legend_cols, title="")   # unlinked: never touches panel 1
    if subtitle:
        add_text(layout, subtitle, 8, 184, 280, 24, 6.5)
    project.layoutManager().addLayout(layout)
    return layout

RECT_SHAPE = getattr(QgsLayoutItemShape, "Rectangle", None)
if RECT_SHAPE is None:
    RECT_SHAPE = QgsLayoutItemShape.Shape.Rectangle

def add_bv_legend(layout, x, y, exp_label, cap_label, cell=10.0, notes=None):
    """3x3 grid: exposure increases upwards, capacity to the right."""
    add_text(layout, "Legend", x - 12, y - 12, 60, 6, 9, bold=True)
    for e in "123":
        for c in "123":
            shp = QgsLayoutItemShape(layout)
            shp.setShapeType(RECT_SHAPE)
            shp.setSymbol(QgsFillSymbol.createSimple({"color": BV_PAL[e + c], "outline_color": "#ffffff",
                                                      "outline_width": "0.3"}))
            layout.addLayoutItem(shp)
            shp.attemptMove(QgsLayoutPoint(x + (int(c) - 1) * cell, y + (3 - int(e)) * cell, MM))
            shp.attemptResize(QgsLayoutSize(cell, cell, MM))
    add_text(layout, "low", x - 1, y + 3 * cell + 1, 12, 4, 6.5)
    add_text(layout, "high", x + 2 * cell + 2, y + 3 * cell + 1, 12, 4, 6.5)
    add_text(layout, f"{cap_label} →", x, y + 3 * cell + 5, 60, 5, 7.5, bold=True)
    add_text(layout, "high", x - 10, y + 1, 10, 4, 6.5)
    add_text(layout, "low", x - 10, y + 2 * cell + 5, 10, 4, 6.5)
    add_text(layout, f"↑ {exp_label}", x - 12, y - 6, 62, 5, 7.5, bold=True)
    add_text(layout, notes or ("magenta = high exposure, low capacity\n"
                               "dark blue = high exposure, high capacity\n"
                               "grey (lightest) = low on both"), x - 12, y + 3 * cell + 12, 64, 14, 6.5)

def make_bv_layout(name, title, bv_layer, context, subtitle, exp_label, cap_label="institutional capacity",
                   extent=None, scale_km=100, extra_legend=None, bv_notes=None):
    layout = new_layout(name)
    m = add_map(layout, [osm] + [bv_layer] + context, 8, 22, 215, 165, extent or UA_RECT)
    add_text(layout, title, 8, 6, 280, 10, 15, bold=True)
    add_bv_legend(layout, 245, 40, exp_label, cap_label, notes=bv_notes)
    if extra_legend:
        add_legend(layout, m, extra_legend, 240, 118, 52, 30, title="")
    add_scalebar(layout, m, 227, 175, scale_km)
    if subtitle:
        add_text(layout, subtitle, 8, 189, 280, 18, 7)
    project.layoutManager().addLayout(layout)
    return layout

W_STRIKE = f"{md('event_w12_start')} – {md('event_end')}"
W_ALERT = f"{md('alert_w12_start')} – {md('alert_end')}"
credit = ("Sources: VIINA 2.0 (Zhukov, ODbL); Ukrainian air-raid alerts (Klimenko, MIT); KATOTTG codifier "
          "(mykhailoklimnyk/ua-administrative-codes, CC BY 4.0); boundaries OCHA COD-AB / SSPE Kartographia (CC BY-IGO); "
          "GeoNames (CC BY 4.0); © OpenStreetMap contributors (ODbL). "
          "Events are news-coded and geocoded to settlements: counts reflect reporting density and geocoding precision. "
          f"Crimea and places not under Ukrainian control on {md('control_date')} excluded (hatched). "
          f"Strike data to {md('event_end')}, alert data to {md('alert_end')}.")

N04 = (f"Population-weighted mean of hromada alert hours (own + raion + oblast alerts, overlaps merged), {W_ALERT}. "
       "Since 2025 alerts are issued mostly per raion, so the oblast-only figures used previously undercounted. ")
N06 = (f"IDW (16 nearest hromada centres, power 2) of log(1+events) per hromada, {W_STRIKE}, settlement-precision events only; "
       "5 km grid, isolines from 5 events. The bullseyes are reported city targets. ")
N07 = (f"Same data ({W_STRIKE}), same classes. The fitted variogram is ~80 % nugget: strike counts have almost no continuity between "
       "neighbouring hromadas, so ordinary kriging returns a smooth 0–2 background and cannot reproduce city peaks; IDW keeps them. ")
N08 = (f"Left: recency-weighted score (all events since {md('event_first')}, 6-month half-life). Right: events per 100,000 inhabitants, "
       f"{W_STRIKE} (hromadas ≥ 1,000 inhabitants, dated GeoNames population). Both IDW on log scale, isolines from 5. ")
N09 = (f"Ordinary kriging (exponential variogram, nugget 5 %) of alert hours per hromada, {W_ALERT}; isobars at "
       f"100–8,000 h. Alert records start {md('alert_start')}. ")
N10 = ("Gaussian kernel density, 25 km bandwidth, settlement-precision events, same classes in all panels. "
       f"Left unweighted ({W_STRIKE}); centre weighted by number of reports (same window); right all years, 6-month half-life. "
       "Density reflects reported towns. ")
N11 = (f"Getis-Ord Gi*, 60 km distance band (~30 neighbours), 9,999 tie-aware conditional permutations; strikes {W_STRIKE}, "
       f"alerts {W_ALERT}; outlined = significant after FDR (q = 0.05). Triangles/diamonds: LISA high–high cores and "
       "high–low isolated outliers. ")
N12 = (f"KDE 10 km (1 km grid) of settlement-precision events ({W_STRIKE}), individual events by type, alert-hours isobars "
       f"(IDW, {W_ALERT}). Few events: single strikes on Lviv, Ternopil, Uzhhorod, Lutsk dominate the picture. ")
N13 = ("Gi* and LISA as in map 11. Cold spots here are nominal: none survives FDR for strike counts — read as "
       "'no detectable clustering', not 'safe'. ")

credit_res = ("Sources: budgets openbudget.gov.ua (MinFin/Treasury, open data CMU 835); population JRC GHS-POP R2023A "
              "(EC reuse); night lights NASA Black Marble VNP46A3 C2 (public domain); alerts Klimenko (MIT); strikes VIINA 2.0 "
              "(Zhukov, ODbL); boundaries OCHA COD-AB / SSPE Kartographia (CC BY-IGO); © OpenStreetMap contributors (ODbL). "
              f"Places not under Ukrainian control on {md('control_date')} excluded.")
CAP_TXT = ("Capacity = mean percentile rank of own revenue per capita 2025, transfer dependency (inverse), capital-expenditure "
           "share 2023–25 and civilian PIT growth 2021–25 (per capita on pre-war GHS-POP 2020). ")
FIND = ("Capacity and exposure are nearly independent (ρ ≈ 0.1); within oblasts capacity goes with somewhat better night-light "
        "recovery, but it does not measurably soften the effect of exposure (interaction ≈ 0 after oblast controls; "
        "cross-sectional association). ")
N14 = (f"Terciles among non-occupied hromadas. Exposure = air-raid alert hours ({W_ALERT}); alerts are issued per raion "
       "or oblast, hence the blocky pattern. White north of Kyiv: Chornobyl exclusion zone (no budget). " + CAP_TXT + FIND)
N15 = ("Exposure classes: 1 = no geocoded strike since 2022 (77 % of hromadas), 2/3 = below/above the median of hromadas with "
       "strikes (log count). Strike counts reflect reporting density and settlement geocoding. " + CAP_TXT)
N16 = ("Recovery = mean percentile rank of 2024/2021 annual and winter 2024-25/2020-21 radiance ratios over pixels lit in 2021 "
       "(≥ 1 nW/cm²/sr). Radiance also reflects blackout schedules and street-lighting policy, and follows oblast-wide grid "
       "conditions (oblast effects explain most of the variance). White = too few lit pixels. ")
N17 = ("Terciles computed within Ivano-Frankivsk, Zakarpattia, Lviv and Chernivtsi oblasts only (regional classes — not "
       f"comparable with map 14). Exposure = alert hours ({W_ALERT}). " + CAP_TXT)

N18 = ("reSCORE 2024 (SeeD / UNDP, General Population; n = 7,758, face-to-face, Jun–Sep 2024; government-controlled "
       "areas excluding Donetsk, Luhansk and Crimea): oblast score minus national score on the 0–10 scale; SeeD treats "
       "differences within ±0.5 as not significant. Blank oblasts: not surveyed. City booster samples (Kharkiv, Odesa, "
       "Zaporizhzhia, Dnipro, Kryvyi Rih) not included. IDPs present = IOM DTM estimate of IDPs living in the oblast, "
       "31 Mar 2026, per 1,000 pre-war residents (GHS-POP 2020); registered IDPs differ (e.g. Dnipropetrovsk 194 present "
       "vs 134 registered per 1,000); no estimate for Zaporizhzhia, Kherson, Donetsk. Sources: SCORE Ukraine "
       "(scoreforpeace.org); IOM DTM via HDX; JRC GHS-POP; boundaries OCHA COD-AB / SSPE Kartographia (CC BY-IGO); "
       "© OpenStreetMap contributors (ODbL).")

_cs = TC.get("change_share", {})
def _sh(grp):
    d = _cs.get(grp, {})
    return " / ".join(pct(d.get(k, 0)) for k in ("declined", "stable", "improved")) if d else "?"
_O1, _O2 = "log recent level", "log summer-24 dip vs H2-23"
N19 = (f"Light deficit = terciles (reversed) of mean lit-pixel radiance {TC.get('recent_window', '?')} relative to the same "
       "calendar months in 2020–21; non-occupied hromadas with ≥ 10 lit pixels (white = fewer). Capacity terciles as map 14. "
       f"Within oblasts, capacity goes with a higher recent light level ({tb(_O1, 'M2 FE')}; with controls "
       f"{tb(_O1, 'M3 FE+ctrl')}; standardised); with pre-war 2021 capacity only ({tb(_O1, 'M5 pre-war cap')}), so part of "
       "the association runs from local economic activity to both. No buffering: exposure × capacity "
       f"({tb(_O1, 'M3 FE+ctrl', 'int')}) after oblast effects. Radiance reflects street-lighting policy and grid conditions, "
       "not only damage; cross-sectional association. ")
N20 = ("Left: mean radiance Jun–Jul 2024 (rolling outages) as a share of the same hromada's Jul–Dec 2023 level; quintiles. "
       f"Within oblasts, higher capacity goes with a smaller loss ({tb(_O2, 'M3 FE+ctrl')}), also with pre-war 2021 capacity "
       f"({tb(_O2, 'M5 pre-war cap')}). Right: last 12 months vs Jul–Dec 2023, change beyond ±2 × the hromada's own "
       f"pre-war month-to-month noise (2021 vs 2020); declined / stable / improved: all {_sh('national')}, Carpathian "
       f"oblasts {_sh('carpathian')}. Baseline = same month 2020–21; June 2025 excluded (retrieval artefact). ")

layouts = [
    make_layout("01_risk_index", "Russian strike risk index — H3 hexagons, recency-weighted",
                [osm, outline, hexes], credit),
    make_layout("02_settlements_12m", "Strike events by settlement — last 12 months",
                [osm, outline, settl], credit),
    make_layout("03_points_12m", "Individual strike events by type — last 12 months",
                [osm, outline, pts], credit),
    make_layout("04_alert_hours", "Air-raid alert hours by raion — last 12 months",
                [alert_rai, occ, obl_b, outline], N04 + credit),
    make_layout("05_carpathian_zoom", "Strike risk index — Carpathian region, H3 res 7 (~5 km cells)",
                [osm, outline, west, pts], credit, extent=WEST_RECT, scale_km=25),
    make_layout("06_idw_strikes", "Strike intensity surface — IDW of events per hromada, last 12 months",
                [osm, r_n12_idw, rai_b, occ, i_n12_idw, obl_b, outline, cities], N06 + credit),
    make_layout_multi("07_idw_vs_kriging", "Strike intensity — IDW vs ordinary kriging (same data, same classes)",
                      [([osm, r_n12_idw, occ, i_n12_idw, obl_b, outline], "IDW"),
                       ([osm, r_n12_kr, occ, i_n12_kr, obl_b, outline], "Ordinary kriging")], N07 + credit,
                      legend=[(r_n12_idw, "Strike events per hromada, 12 m (both panels)"),
                              (i_n12_idw, "Isolines (labelled in events)"), occ]),
    make_layout_multi("08_weighted_surfaces", "Weighted strike surfaces — recency and per capita",
                      [([osm, r_score, occ, i_score, obl_b, outline], "Recency-weighted score (all years)"),
                       ([osm, r_rate, occ, i_rate, obl_b, outline], "Events per 100,000 inhabitants (12 m)")], N08 + credit,
                      legend=[(r_score, "Recency score (left)"), (r_rate, "Per 100k (right)"), (i_score, "Isolines"), occ]),
    make_layout("09_alert_kriging", "Air-raid alert hours — kriged surface with isobars, last 12 months",
                [osm, r_alert, occ, i_alert, obl_b, outline], N09 + credit),
    make_layout_multi("10_kde_25km", "Kernel density of strike events — 25 km bandwidth",
                      [([osm, k_n12, occ, obl_b, outline], "Unweighted, 12 m"),
                       ([osm, k_rep, occ, obl_b, outline], "Weighted by reports, 12 m"),
                       ([osm, k_rec, occ, obl_b, outline], "Recency-weighted, all years")], N10 + credit,
                      legend=[(k_n12, "Density per 1,000 km² (all panels)"), occ]),
    make_layout_multi("11_gi_star", "Hot spots — Getis-Ord Gi* on hromada centres (60 km band, FDR-controlled)",
                      [([osm, gi_n12, occ, fdr_n12, obl_b, outline, lisa], "Strike events, 12 m"),
                       ([osm, gi_alert, occ, fdr_alert, obl_b, outline], "Alert hours, 12 m")], N11 + credit,
                      legend=[(gi_n12, "Gi* class (both panels)"), fdr_n12, lisa, occ]),
    make_layout("12_carpathian_surfaces", "Carpathian region — strike density, events and alert isobars, last 12 months",
                [osm, k_w10, hro_b, i_alert_w, obl_b, outline, pts, west_lbl], N12 + credit, extent=WEST_RECT, scale_km=25,
                legend=[(pts, "Strike events, 12 m"), (i_alert_w, "Alert-hour isobars"), (k_w10, "KDE 10 km, per 1,000 km²")]),
    make_layout("13_carpathian_hotspots", "Carpathian region — Gi* hot/cold spots and LISA outliers, strike events 12 m",
                [osm, gi_n12, hro_b, fdr_n12, obl_b, outline, lisa, west_lbl], N13 + credit, extent=WEST_RECT, scale_km=25,
                legend=[lisa, fdr_n12, (gi_n12, "Gi* class, 60 km band")]),
    make_bv_layout("14_resilience_alerts_capacity",
                   "Exposure and institutional capacity — alert hours × capacity, hromadas",
                   bv_alt, [occ, obl_b, outline, cities], N14 + credit_res,
                   "exposure: alert hours, 12 m", extra_legend=[occ]),
    make_bv_layout("15_resilience_strikes_capacity",
                   "Exposure and institutional capacity — strikes since 2022 × capacity, hromadas",
                   bv_str, [occ, obl_b, outline, cities], N15 + credit_res,
                   "exposure: strike events", extra_legend=[occ]),
    make_layout("16_resilience_recovery", "Night-light recovery 2021 → 2024, lit areas — hromada quintiles",
                [osm, rec_q, occ, obl_b, outline, cities], N16 + credit_res,
                legend=[(rec_q, "Recovery quintile"), occ]),
    make_bv_layout("17_carpathian_resilience",
                   "Carpathian region — alert hours × institutional capacity (regional terciles)",
                   bv_carp, [hro_b, obl_b, outline, west_lbl], N17 + credit_res,
                   "exposure: alert hours (regional)", cap_label="capacity (regional)",
                   extent=CARP_RECT, scale_km=50),
    make_layout_grid("18_oblast_context",
                     "Citizen resilience by oblast — reSCORE 2024 (difference from national) and IDPs present",
                     [([osm, l, outline], lab) for l, lab in ctx_layers] + [([osm, idp_ctx, outline], "IDPs present per 1,000")],
                     cols=4, subtitle=N18,
                     legend=[(ctx_leg, "reSCORE indicator vs national (0–10 scale)"),
                             (idp_ctx, "IDPs present per 1,000 pre-war residents")]),
    make_bv_layout("19_trajectory_level_capacity",
                   "Night lights now vs pre-war — light deficit × institutional capacity, hromadas",
                   traj_bv, [occ, obl_b, outline, cities], N19 + credit_res,
                   "light deficit, last 12 m", extra_legend=[occ],
                   bv_notes="magenta = low light, low capacity\n"
                            "dark blue = low light, high capacity\n"
                            "teal = high light, high capacity"),
    make_layout_multi("20_trajectory_outage",
                      "Summer-2024 power outages and change since 2023 — night lights, hromadas",
                      [([osm, traj_s24, occ, obl_b, outline], "Light Jun–Jul 2024 vs Jul–Dec 2023"),
                       ([osm, traj_chg, occ, obl_b, outline], "Last 12 months vs Jul–Dec 2023")],
                      N20 + credit_res,
                      legend=[(traj_s24, "Outage loss (quintiles)"), (traj_chg, "Change vs own noise"), occ],
                      legend_cols=3, legend_split=False),
]

# ------------------------------------------------------------------ export
for lay in layouts:
    ex = QgsLayoutExporter(lay)
    png = QgsLayoutExporter.ImageExportSettings(); png.dpi = 200
    pdf = QgsLayoutExporter.PdfExportSettings()
    r1 = ex.exportToImage(os.path.join(MAPS, lay.name() + ".png"), png)
    r2 = ex.exportToPdf(os.path.join(MAPS, lay.name() + ".pdf"), pdf)
    print(f"{lay.name()}: png={'ok' if r1 == QgsLayoutExporter.ExportResult.Success else r1}  pdf={'ok' if r2 == QgsLayoutExporter.ExportResult.Success else r2}")

UA_EXTENT = QgsReferencedRectangle(UA_RECT, QgsCoordinateReferenceSystem("EPSG:3857"))
project.viewSettings().setDefaultViewExtent(UA_EXTENT)
project.viewSettings().setPresetFullExtent(UA_EXTENT)
project.setFilePathStorage(Qgis.FilePathType.Relative)

proj_path = os.path.join(DATA, "ukraine_strikes.qgz")
project.write(proj_path)
print("project saved:", proj_path)
qgs.exitQgis()
