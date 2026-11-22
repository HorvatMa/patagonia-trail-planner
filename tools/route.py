import os
import json, time, urllib.request
UA = {"User-Agent": "trip-map-builder/1.0"}
def route(profile, pts):
    coords = ";".join(f"{lon},{lat}" for lat, lon in pts)
    url = f"https://routing.openstreetmap.de/routed-{profile}/route/v1/{profile}/{coords}?overview=full&geometries=geojson"
    for i in range(3):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60)); break
        except Exception as e:
            print("retry", e); time.sleep(3)
    rt = r["routes"][0]
    snaps = [round(w["distance"]) for w in r["waypoints"]]
    return rt["geometry"]["coordinates"], rt["distance"], snaps

# trail id -> waypoints (lat, lon); marker point = last meaningful destination
TRAILS = {
 "tamango_camp": [(-47.2229,-72.5266),(-47.18812,-72.52718)],
 "meseta_rincon": [(-46.6072,-71.4075),(-46.6544,-71.4171),(-46.7032,-71.4520)],
 "cerro_leon": [(-47.8045,-72.0941),(-47.7791,-72.1338)],
 "chucao": [(-43.76848,-72.95974),(-43.7771,-72.9521)],
 "dos_lagunas": [(-45.5298,-71.8535),(-45.5294,-71.8394),(-45.5291,-71.8217)],
 "coy": [(-45.5259,-72.0409),(-45.5365,-72.0165)],
 "castillo": [(-46.1114,-72.157),(-46.0763,-72.1914)],
 "lagunas_altas": [(-47.1274,-72.5047),(-47.128,-72.4714)],
 "tamango": [(-47.2425,-72.524),(-47.2229,-72.5266)],
 "voh": [(-48.4685,-72.5567),(-48.4661,-72.5477)],
 "piedra": [(-46.7318,-71.7816),(-46.7261,-71.7602)],
 "jeinimeni": [(-46.8606,-72.0193),(-46.8502,-72.1061)],
 "queulat_colgante": [(-44.4716,-72.5584),(-44.4608,-72.5391)],
 "chaiten": [(-42.8085,-72.6676),(-42.8368,-72.6475)],
 "alerces": [(-42.6788,-72.5828),(-42.6757,-72.5799)],
 "futa": [(-43.1609,-71.8929),(-43.1582,-71.8917)],
 "torre": [(-49.3313,-72.8947),(-49.3232,-73.0024)],
 "tres": [(-49.3211,-72.8946),(-49.3049,-72.9357),(-49.2784,-72.9895)],
 "pliegue": [(-49.3375,-72.8814),(-49.3594,-72.9675)],
 "toro": [(-49.3375,-72.8814),(-49.3852,-73.0405)],
 "capri": [(-49.3211,-72.8946),(-49.3049,-72.9357)],
 "base_torres": [(-50.9732,-72.875),(-50.9423,-72.9373)],
 "cuernos": [(-51.0614,-72.9898),(-51.0677,-73.0066),(-51.0483,-73.0123)],
}
if __name__ == '__main__':
    out = {}
    for k, pts in TRAILS.items():
        g, d, s = route("foot", pts)
        out[k] = g
        print(f"{k:18s} {d/1000:6.1f} km one-way  snaps={s}")
        time.sleep(1)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo", "trails.json"), "w"))
