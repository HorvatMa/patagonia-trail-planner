import json, sys, time, urllib.parse, urllib.request
UA = {"User-Agent": "trip-map-builder/1.0"}
qs = sys.argv[1:]
for q in qs:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 4, "countrycodes": "cl,ar"})
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
    print("##", q)
    for x in r: print("   ", round(float(x["lat"]),4), round(float(x["lon"]),4), x["type"], "|", x["display_name"][:90])
    time.sleep(1.1)
