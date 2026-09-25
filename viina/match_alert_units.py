"""Step 2a: map air-raid alert oblast/raion/hromada names to KATOTTH unit keys (k1/k2/k3).
Writes qgis/alert_unit_map.csv (one row per distinct alert place, with match scores)."""
import re, difflib
import pandas as pd
import geopandas as gpd

pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 55)

OB = {"Cherkaska oblast": "71", "Chernihivska oblast": "74", "Chernivetska oblast": "73", "Dnipropetrovska oblast": "12",
      "Donetska oblast": "14", "Ivano-Frankivska oblast": "26", "Kharkivska oblast": "63", "Khersonska oblast": "65",
      "Khmelnytska oblast": "68", "Kirovohradska oblast": "35", "Kyiv City": "80", "Kyivska oblast": "32",
      "Luhanska oblast": "44", "Lvivska oblast": "46", "Mykolaivska oblast": "48", "Odeska oblast": "51",
      "Poltavska oblast": "53", "Rivnenska oblast": "56", "Sumska oblast": "59", "Ternopilska oblast": "61",
      "Vinnytska oblast": "05", "Volynska oblast": "07", "Zakarpatska oblast": "21", "Zaporizka oblast": "23",
      "Zhytomyrska oblast": "18", "Autonomous Republic of Crimea": "01", "Sevastopol": "85"}
# renamed units and known misses: alert name -> unit key
RAION_OVERRIDE = {"Chervonohradskyi raion": "4612", "Krasnohradskyi raion": "6306", "Kupianskyi raion": "6308",
                  "Kamianskyi raion": "1204", "Kamianets-Podilskyi raion": "6802", "Volodymyr-Volynskyi raion": "0702"}
HROMADA_OVERRIDE = {("Mykolaivska oblast", "m. Yuzhnoukrainsk ta Yuzhnoukrainska terytorialna hromada"): "4804025",
                    ("Kharkivska oblast", "Zolochivska terytorialna hromada"): "6302005"}

TR = {"а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie", "ж": "zh", "з": "z", "и": "y",
      "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
      "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ю": "iu", "я": "ia",
      "ь": "", "ъ": "", "ы": "y", "э": "e", "ё": "io"}
INITIAL = {"я": "ya", "є": "ye", "ї": "yi", "ю": "yu", "й": "y"}
UK_DROP = r"\b(вся|територія|територіальна|територіальної|сільська|сільської|селищна|селищної|міська|міської|громада|громади|рада|ради|район|району|область|області)\b"
EN_DROP = r"\b(terytorialna|hromada|miska|silska|selyshchna|obiednana|raion)\b"
ADJ = r"(skyi|tskyi|zkyi|ska|tska|zka|ske|sk|kyi|ka)$"

def is_str(x):
    return isinstance(x, str) and bool(x)

def norm(s):
    s = str(s).lower().replace("зг", "zgh")
    s = re.sub(r"(?<![\w'’ʼ])([яєїюй])", lambda m: INITIAL[m.group(1)], s)
    s = "".join(TR.get(ch, ch) for ch in s)
    return re.sub(r"[^a-z]", "", s)

def uk_key(s):
    if not is_str(s):
        return None
    s = s.lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.split(r"\bза винятком\b", s)[0]
    s = re.sub(UK_DROP, " ", s)
    s = re.sub(r"ої\b", "а", s)            # genitive -> nominative feminine adjective
    return norm(s) or None

def en_key(s):
    s = str(s).strip()
    if " ta " in s:                        # "m. Pervomaisk ta Pervomaiska terytorialna hromada"
        s = s.split(" ta ")[-1]
    return norm(re.sub(EN_DROP, " ", s))

def stem(k):
    return re.sub(ADJ, "", k)

def best(cands, target):
    """cands: unit_id -> (official_key, centre_key). Returns (unit_id, score)."""
    tstem = stem(target)
    out = (None, 0.0)
    for k, (off, cen) in cands.items():
        off = off if is_str(off) else None
        cen = cen if is_str(cen) else None
        if off and off == target:
            return k, 1.0
        sc = 0.0
        if off:
            sc = 0.95 if stem(off) == tstem else difflib.SequenceMatcher(None, target, off).ratio()
        if cen:
            sc = max(sc, 0.95 if cen == tstem else difflib.SequenceMatcher(None, tstem, cen).ratio() * 0.9)
        if sc > out[1]:
            out = (k, sc)
    return out

rai = gpd.read_file("qgis/admin_units.gpkg", layer="raion", engine="pyogrio").drop(columns="geometry")
hro = gpd.read_file("qgis/admin_units.gpkg", layer="hromada", engine="pyogrio").drop(columns="geometry")
rai["off"] = [uk_key(n) for n in rai["name"]]
official = hro["name_src"].astype(str).str.startswith("KATOTTG") | (hro["name_src"] == "own level-3 row")
hro["off"] = [uk_key(n) if o else None for n, o in zip(hro["name"], official)]
hro["cen"] = [stem(norm(c)) if is_str(c) else None for c in hro["centre"]]
rai_name = rai.set_index("unit_id")["name"]
hro_name = hro.set_index("unit_id")["name"]
hro_k2 = hro.set_index("unit_id")["k2"]

a = pd.read_csv("../air_raid/official_data_en.csv", dtype=str)
a["k1"] = a["oblast"].str.strip().map(OB)
print("level counts:", a["level"].value_counts().to_dict())
print("unmatched oblast:", sorted(a.loc[a["k1"].isna(), "oblast"].unique().tolist()))
places = a.groupby(["oblast", "raion", "hromada", "level", "k1"], dropna=False).size().rename("n_rows").reset_index()
print(f"distinct alert places: {len(places)}  by level: {places['level'].value_counts().to_dict()}")

rows = []
for _, p in places.iterrows():
    r = {"oblast": p.oblast, "raion": p.raion, "hromada": p.hromada, "level": p.level, "k1": p.k1,
         "k2": None, "k3": None, "raion_match": None, "score_r": None, "hromada_match": None, "score_h": None,
         "src": None, "n_rows": p.n_rows}
    if p.level == "oblast" or not is_str(p.k1):
        rows.append(r); continue
    if p.k1 in ("80", "85"):
        r["k2"], r["k3"], r["score_r"], r["score_h"], r["src"] = p.k1 + "00", p.k1 + "00000", 1.0, 1.0, "special city"
        rows.append(r); continue
    if str(p.raion).strip() in RAION_OVERRIDE:
        k2, sr, src = RAION_OVERRIDE[str(p.raion).strip()], 1.0, "override"
    else:
        cr = rai[(rai["k1"] == p.k1) & (~rai["pseudo"])]
        k2, sr = best({u: (o, None) for u, o in zip(cr["unit_id"], cr["off"])}, en_key(p.raion))
        src = "match"
    r["k2"], r["score_r"], r["raion_match"], r["src"] = k2, round(sr, 2), rai_name.get(k2), src
    if p.level == "hromada":
        ok = (p.oblast, str(p.hromada).strip())
        if ok in HROMADA_OVERRIDE:
            k3, sh, src = HROMADA_OVERRIDE[ok], 1.0, "override"
        else:
            ch = hro[hro["k2"] == k2] if k2 is not None else hro.iloc[0:0]
            k3, sh = best({u: (o, c) for u, o, c in zip(ch["unit_id"], ch["off"], ch["cen"])}, en_key(p.hromada))
            src = "match"
            if sh < 0.95:                  # retry across the oblast in case the raion match was wrong
                ch2 = hro[hro["k1"] == p.k1]
                k3b, shb = best({u: (o, c) for u, o, c in zip(ch2["unit_id"], ch2["off"], ch2["cen"])}, en_key(p.hromada))
                if shb > sh:
                    k3, sh, src = k3b, shb, "match (oblast-wide)"
        if k3 is not None and hro_k2.get(k3) != r["k2"]:
            r["k2"] = hro_k2.get(k3)
            r["raion_match"] = f"{rai_name.get(r['k2'])} (via hromada)"
        r["k3"], r["score_h"], r["hromada_match"], r["src"] = k3, round(sh, 2), hro_name.get(k3), src
    rows.append(r)

m = pd.DataFrame(rows)
m.to_csv("qgis/alert_unit_map.csv", index=False)
rl = m[m["level"] == "raion"]; hl = m[m["level"] == "hromada"]
print(f"\nraion-level places: {len(rl)}; score 1.0: {(rl['score_r'] == 1).sum()}; unmatched: {rl['k2'].isna().sum()}")
print(rl[rl["score_r"] < 1].sort_values("score_r")[["oblast", "raion", "raion_match", "k2", "score_r", "n_rows"]].to_string())
dup = rl.groupby("k2").filter(lambda x: len(x) > 1).sort_values("k2")
print("\nraions hit by more than one alert name:")
print(dup[["k2", "raion_match", "raion", "score_r", "n_rows"]].to_string())
print(f"\nhromada-level places: {len(hl)}; score 1.0: {(hl['score_h'] == 1).sum()}; unmatched: {hl['k3'].isna().sum()}")
print(hl[hl["score_h"] < 1].sort_values("score_h")[["oblast", "raion", "hromada", "hromada_match", "k3", "score_h", "src", "n_rows"]].to_string())
dup = hl.groupby("k3").filter(lambda x: len(x) > 1).sort_values(["k3", "n_rows"], ascending=[True, False])
print("\nhromada keys hit by more than one alert name:")
print(dup[["k3", "hromada_match", "hromada", "score_h", "n_rows"]].to_string())
print("written: qgis/alert_unit_map.csv")
