#!/usr/bin/env python3
"""Fetch gallery photos (Wikimedia Commons) for catalogue hikes and overnight places → tools/geo/photos.json.

    python3 tools/photos.py            # fetch only items missing from photos.json
    python3 tools/photos.py --refresh  # refetch everything
    python3 tools/photos.py castillo   # refetch these keys (hike ids or place names)
    python3 tools/photos.py --apply gpt-reports/<date>-photos-<slug>.json [keys]   # merge a photo-scout report (pins the keys)
    python3 tools/photos.py --check    # validate photos.json

Keys in "_pinned" were checked by eye (photo-scout agent); searches skip them unless --force is given.

Each key gets up to PER_ITEM photos. Photos whose Commons coordinates are far from the hike/place are skipped.
The pages hotlink the images (internet needed, like the map). To drop a bad photo, add its file title to SKIP."""
import json, math, os, re, sys, time, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from catalog import H, HP          # noqa: E402
from places import PLACES          # noqa: E402

OUT = os.path.join(HERE, "geo", "photos.json")
PER_ITEM, MAX_KM = 3, 40
UA = {"User-Agent": "trip-planner/1.0 (personal use)"}
SKIP = ["Huerquehue", "Finca El Toro", "pintoresca", "banner", "Cerca casco", "year 1993", "Coihuecaido"]  # title substrings to drop
BAD = re.compile(r"\b(map|mapa|plano|logo|sign|cartel|letrero|diagram|escudo|flag|bandera|cementerio|cemetery|bomberos|aerodrome|"
                 r"aeródromo|malvinas|memoria|feria|washboard|estación|calles|casa)\b|\bISS\d|\.svg$|\.tiff?$", re.I)

# search queries per hike id (tried in order until PER_ITEM photos are found)
HIKE_Q = {
    "coy": ["Reserva Nacional Coyhaique", "Laguna Verde Coyhaique"],
    "simpson": ["Cascada La Virgen Coyhaique", "Reserva Nacional Río Simpson"],
    "castillo": ["Laguna Cerro Castillo"],
    "paredon": ["Paredón de las Manos Cerro Castillo", "arte rupestre Aysén", "Cerro Castillo Aysén"],
    "ibanez": ["Salto Río Ibáñez", "Puerto Ingeniero Ibáñez"],
    "marble": ["Capillas de Mármol", "Marble Caves Chile"],
    "explor_mirador": ["Glaciar Exploradores"],
    "explor_ice": ["Exploradores glacier", "Glaciar Exploradores trekking", "Glaciar Exploradores Parque Nacional Laguna San Rafael"],
    "confluencia": ["Confluencia Baker Neff", "Río Baker"],
    "lagunas_altas": ["Lagunas Altas Parque Patagonia", "Valle Chacabuco"],
    "aviles": ["Valle Avilés Parque Nacional Patagonia", "Parque Nacional Patagonia Chile", "Valle Chacabuco guanacos"],
    "tamango": ["Reserva Nacional Tamango", "Lago Cochrane"],
    "tortel": ["Caleta Tortel"],
    "voh": ["Villa O'Higgins", "Lago O'Higgins"],
    "banderas": ["Chile Chico Lago General Carrera", "Chile Chico"],
    "piedra": ["Piedra Clavada Jeinimeni", "Valle Lunar Jeinimeni", "Reserva Nacional Lago Jeinimeni"],
    "jeinimeni": ["Lago Jeinimeni", "Reserva Nacional Lago Jeinimeni"],
    "queulat_colgante": ["Ventisquero Colgante"],
    "bosque": ["Bosque Encantado Queulat", "Parque Nacional Queulat"],
    "chaiten": ["Volcán Chaitén"],
    "tronador": ["Laguna Tronador Pumalín", "Parque Pumalín"],
    "alerces": ["Sendero Los Alerces Pumalín", "Caleta Gonzalo"],
    "amarillo": ["Ventisquero Amarillo", "Ventisquero Amarillo Pumalín", "El Amarillo Pumalín", "Parque Pumalín Douglas Tompkins"],
    "yelcho": ["Ventisquero Yelcho", "Lago Yelcho"],
    "futa": ["Futaleufú río", "Futaleufú"],
    "toro": [],  # Commons has no usable Laguna Toro photos (searches return other places)
    "torre": ["Laguna Torre Cerro Torre"],
    "tres": ["Laguna de los Tres"],
    "pliegue": ["Loma del Pliegue Tumbado"],
    "capri": ["Laguna Capri"],
    "desierto": ["Lago del Desierto", "Chorrillo del Salto"],
    "pmoreno": ["Glaciar Perito Moreno"],
    "cuevamanos": ["Cueva de las Manos"],
    "base_torres": ["Base Las Torres", "Torres del Paine towers"],
    "cuernos": ["Salto Grande Torres del Paine", "Cuernos del Paine"],
    "grey": ["Lago Grey Glaciar Grey", "Lago Grey"],
}
# overnight places: key = text matched inside a day's "sleep" field (first match wins, in this order)
PLACE_Q = {
    "Coyhaique": ["Coyhaique Cerro Mackay", "Coyhaique vista", "Coyhaique"],
    "Puyuhuapi": ["Puyuhuapi"],
    "Villa Cerro Castillo": ["Villa Cerro Castillo", "Cerro Castillo Aysén"],
    "Puerto Río Tranquilo": ["Lago General Carrera Puerto Río Tranquilo", "Puerto Río Tranquilo", "Lago General Carrera"],
    "Cochrane": ["Lago Cochrane", "Río Cochrane", "Cochrane Aysén"],
    "Villa O'Higgins": ["Villa O'Higgins"],
    "Caleta Tortel": ["Caleta Tortel"],
    "Chile Chico": ["Chile Chico"],
    "Los Antiguos": ["Los Antiguos Santa Cruz", "Los Antiguos"],
    "Bajo Caracoles": ["Bajo Caracoles", "Ruta 40 Santa Cruz"],
    "El Chaltén": ["El Chaltén", "Fitz Roy El Chaltén"],
    "El Calafate": ["El Calafate Lago Argentino", "El Calafate"],
    "Torres del Paine": ["Torres del Paine", "Cuernos del Paine"],
    "Futaleufú": ["Futaleufú"],
    "Chaitén": ["Chaitén"],
}
PLACE_PT = {"Bajo Caracoles": PLACES.get("Bajo Caracoles"), "Cochrane": PLACES.get("Cochrane")}

def place_for(sleep):
    for k in PLACE_Q:
        if k in sleep: return k
    return None

def point(key):
    if key in HP: return HP[key]
    return PLACE_PT.get(key) or PLACES.get(key)

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))

def search(q):
    params = dict(action="query", format="json", generator="search", gsrnamespace=6, gsrlimit=15,
                  gsrsearch=q + " filetype:bitmap", prop="imageinfo|coordinates", iiprop="url|size", iiurlwidth=960)
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for wait in (0, 10, 30, 60, 120):
        time.sleep(wait)
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)); break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
    else:
        raise RuntimeError("rate-limited (429) repeatedly; try again later")
    pages = sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = p["imageinfo"][0]
        c = p.get("coordinates", [{}])[0]
        out.append(dict(title=p["title"], w=ii["width"], h=ii["height"], thumb=ii.get("thumburl", ii["url"]),
                        full=ii["url"], page=ii["descriptionurl"], lat=c.get("lat"), lon=c.get("lon")))
    return out

def fetch(key, queries, used):
    pt, got = point(key), []
    for q in queries:
        try: cands = search(q)
        except Exception as e:
            print(f"  {key}: search failed ({e})"); cands = []
        time.sleep(3)
        good = []
        for c in cands:
            if any(x in c["title"] for x in SKIP) or c["title"] in used or BAD.search(c["title"]) or c["w"] < 800: continue
            if pt and c["lat"] is not None and km(pt, (c["lat"], c["lon"])) > MAX_KM: continue
            good.append(c)
        good.sort(key=lambda c: c["h"] > c["w"] * 1.05)  # landscape first, otherwise search order
        for c in good:
            if len(got) >= PER_ITEM: break
            if c["title"] not in {g["title"] for g in got}: got.append(c)
        if len(got) >= PER_ITEM: break
    for g in got:
        used.add(g["title"])
        if g["w"] > 1920 and "/960px-" in g["thumb"]: g["full"] = g["thumb"].replace("/960px-", "/1920px-")
        for k in ("lat", "lon"): g.pop(k)
    return got

HOSTS = ("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/")
PIN = "_pinned"  # {key: "report file, date"}: photos checked by eye (photo-scout); never overwritten by a search

def all_keys():
    return set(H) | set(PLACE_Q)

def validate(data):
    """Problems in photos.json (used by tools/check_build.py --photos)."""
    probs, seen = [], {}
    if not isinstance(data, dict): return ["photos.json must be an object"]
    for k, v in data.items():
        if k == PIN:
            probs += [f"pinned key {x!r} has no entry" for x in v if x not in data]; continue
        if k not in all_keys(): probs.append(f"unknown key {k!r} (not a hike id or PLACE_Q place)")
        if not isinstance(v, list): probs.append(f"{k}: must be a list"); continue
        for ph in v:
            for f in ("title", "thumb", "full", "page"):
                if not isinstance(ph.get(f), str) or not ph[f]: probs.append(f"{k}: photo missing {f!r}")
            for f in ("thumb", "full"):
                if isinstance(ph.get(f), str) and not ph[f].startswith(HOSTS):
                    probs.append(f"{k}: {f} is not on upload./thumb.wikimedia.org")
            t = ph.get("title")
            if t in seen and seen[t] != k: probs.append(f"{t} used by both {seen[t]} and {k}")
            seen[t] = k
    return probs

def apply_report(path, keys, data):
    rep = json.load(open(path, encoding="utf-8"))
    pins = data.setdefault(PIN, {})
    for o in rep:
        k = o.get("key")
        if keys and k not in keys: continue
        if k not in all_keys(): print(f"  skip {k!r}: not a hike id or place"); continue
        photos = [{f: ph[f] for f in ("title", "w", "thumb", "full", "page", "shows") if f in ph} for ph in o.get("photos", [])]
        for ph in photos:  # the viewer loads a 1920 px version, not a multi-MB original
            if ph.pop("w", 0) > 1920 and "/960px-" in ph.get("thumb", ""): ph["full"] = ph["thumb"].replace("/960px-", "/1920px-")
        data[k] = photos
        pins[k] = f"{os.path.basename(path)}"
        print(f"  {k}: {o.get('verdict')} → {len(photos)} photos (pinned)")
    probs = validate(data)
    if probs: sys.exit("not written, problems:\n- " + "\n- ".join(probs))

def main():
    args = sys.argv[1:]
    data = json.load(open(OUT)) if os.path.exists(OUT) else {}
    if "--apply" in args:
        i = args.index("--apply"); path = args[i + 1]
        apply_report(path, [a for a in args[i + 2:] if not a.startswith("--")], data)
        json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=0)
        print("→", os.path.relpath(OUT)); return
    if "--check" in args:
        probs = validate(data); print("\n".join(probs) or "photos.json OK"); sys.exit(1 if probs else 0)
    refresh, force = "--refresh" in args, "--force" in args
    only = [a for a in args if not a.startswith("--")]
    pins = data.get(PIN, {})
    items = {**HIKE_Q, **PLACE_Q}
    missing = [k for k in H if k not in HIKE_Q]
    if missing: print("no query for hikes (add to HIKE_Q):", ", ".join(missing))
    used = {p["title"] for k, v in data.items() if k != PIN and (k in pins or (k not in only and not refresh)) for p in v}
    for key, qs in items.items():
        if only and key not in only: continue
        if key in pins and not force:
            if only: print(f"  {key}: pinned (checked by photo-scout); use --force to overwrite")
            continue
        if not only and not refresh and data.get(key): continue
        data[key] = fetch(key, qs, used)
        pins.pop(key, None)
        print(f"  {key}: {len(data[key])} photos")
        json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=0)
    print("→", os.path.relpath(OUT))

if __name__ == "__main__":
    main()
