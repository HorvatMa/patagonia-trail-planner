import json, sys, time, urllib.parse, urllib.request
UA = {"User-Agent": "trip-map-builder/1.0"}
for arg in sys.argv[1:]:
    q, bb = arg.split("@")
    s, w, n, e = bb.split(",")
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 6, "viewbox": f"{w},{n},{e},{s}", "bounded": 1})
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    print("##", q)
    for x in r: print("   ", round(float(x["lat"]),4), round(float(x["lon"]),4), x["class"], x["type"], "|", x["display_name"][:70])
    time.sleep(1.1)
