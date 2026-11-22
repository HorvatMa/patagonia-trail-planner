#!/usr/bin/env python3
"""Generate the trip website for one or more trips.

    python3 tools/build.py                      # build every trips/*/trip.json
    python3 tools/build.py trips/<id>/trip.json # build one trip

Shared data: tools/catalog.py (hikes, grades), tools/places.py (airports/places), tools/geo/*.json (routed trails).
Per trip (trips/<id>/): trip.json (requirements), plans.py (PLANS, BUDGET, SLEEP, DRIVE_STOPS, INDEX),
gpt_opts.py (optional GPT overlay), geo/drive.json (from tools/drive.py). Output goes to trip.json "output_dir"."""
import datetime as dt, glob, html, importlib.util, json, math, os, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GEO = os.path.join(HERE, "geo") + "/"
sys.path.insert(0, HERE)
from catalog import H, HP, POINT_NOTE, GRADE  # noqa: E402

TRAILS = json.load(open(GEO + "trails.json"))
GPT_TRAILS = json.load(open(GEO + "gpt_trails.json"))
PHOTOS = json.load(open(GEO + "photos.json")) if os.path.exists(GEO + "photos.json") else {}  # from tools/photos.py

# per-trip globals, set by load_trip()
TRIP = PLANS = BUDGET = SLEEP = DRIVE = GPT_OPTS = INDEX = START = OUT = REPORTS_REL = None
PEOPLE = NDAYS = 0

def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def load_trip(trip_json):
    global TRIP, PLANS, BUDGET, SLEEP, DRIVE, GPT_OPTS, INDEX, START, OUT, REPORTS_REL, PEOPLE, NDAYS
    tdir = os.path.dirname(os.path.abspath(trip_json))
    TRIP = json.load(open(trip_json, encoding="utf-8"))
    TRIP["_dir"] = tdir
    m = _load_module(os.path.join(tdir, "plans.py"), "trip_plans_" + TRIP["id"].replace("-", "_"))
    PLANS, BUDGET, SLEEP, DRIVE_STOPS_ = m.PLANS, m.BUDGET, m.SLEEP, getattr(m, "DRIVE_STOPS", {})
    INDEX = getattr(m, "INDEX", None) or default_index()
    gp = os.path.join(tdir, "gpt_opts.py")
    GPT_OPTS = _load_module(gp, "trip_gpt_" + TRIP["id"].replace("-", "_")).GPT_OPTS if os.path.exists(gp) else []
    dj = os.path.join(tdir, "geo", "drive.json")
    DRIVE = {int(k): v for k, v in json.load(open(dj)).items()} if os.path.exists(dj) else {}
    START = dt.date.fromisoformat(TRIP["start_date"])
    NDAYS = (dt.date.fromisoformat(TRIP["end_date"]) - START).days + 1
    PEOPLE = int(TRIP.get("people", 2))
    OUT = os.path.normpath(os.path.join(ROOT, TRIP.get("output_dir", os.path.join("trips", TRIP["id"], "site"))))
    REPORTS_REL = os.path.relpath(os.path.join(ROOT, "gpt-reports"), OUT)

def per_person(total):
    return round(total / PEOPLE / 10) * 10

def default_index():
    """Generic overview page for trips that don't define INDEX in plans.py."""
    t = TRIP
    eyebrow = f"{dt.date.fromisoformat(t['start_date']):%b %d} – {dt.date.fromisoformat(t['end_date']):%b %d %Y} · {t.get('people', 2)} people · max €{t['budget']['max_per_person']:,} per person"
    return dict(title=t["title"], desc=f"{len(PLANS)} itineraries: {t['title']}.",
                html=f"""<header class="hero"><p class="eyebrow">{html.escape(eyebrow)}</p><h1>{html.escape(t['title'])}</h1>
<p class="lede">{html.escape(t.get('lede', ''))}</p></header>
<div class="plancards">{{CARDS}}</div>
<h2>Side by side</h2>
<div class="tscroll"><table><thead><tr><th>Plan</th><th>Hike days</th><th>Flex days</th><th>Driving days</th><th>Hiking km</th><th>Hiking ascent</th><th>Driving km</th><th>Overnight spots</th><th>Argentina</th><th>Budget</th><th>Checks</th></tr></thead><tbody>{{ROWS}}</tbody></table></div>
""")

# ---------------------------------------------------------------- requirement checks
import re as _re
SAC = ["T1", "T2", "T3", "T4", "T5", "T6"]

def _nums(txt, unit):
    """Largest number written before `unit` in a text like '≈16–20 km return' or '≈1,100 m'."""
    vals = []
    for m in _re.finditer(r"(\d[\d,.]*)(?:\s*[–-]\s*(\d[\d,.]*))?\s*" + unit + r"\b", txt):
        for g in m.groups():
            if g:
                try: vals.append(float(g.replace(",", "")))
                except ValueError: pass
    return max(vals) if vals else None

def hike_km(h):
    km = _nums(H[h][2], "km")
    if km is not None and "each way" in H[h][2]: km *= 2
    return km

def hike_gain(h):
    return _nums(H[h][3], "m")

def hike_totals(p):
    """Combined distance (km) and ascent (m) of all hikes in a plan. Each hike counts once (a multi-day trek
    spans several days); activities (boat trips, viewpoints) are left out. Ranges count at their upper end."""
    used = plan_counts(p)[0]
    hikes = [h for h in used if GRADE[h]["kind"] != "activity"]
    return round(sum(hike_km(h) or 0 for h in hikes)), round(sum(hike_gain(h) or 0 for h in hikes))

def plan_counts(p):
    used = []
    for d in p["days"]:
        for h in d[2]:
            if h not in used: used.append(h)
    over = [h for h in used if GRADE[h]["kind"] == "overnight"]
    multi = [h for h in used if GRADE[h]["kind"] == "multiday"]
    return used, over, multi

def validate_plan(p):
    """Check one plan against trip.json. Returns [(level, message)], level = 'error' | 'warn'."""
    req, hk, out = TRIP, TRIP.get("hiking", {}), []
    car = req.get("car", {})
    if p.get("pickup", car.get("pickup")) != car.get("pickup") or p.get("dropoff", car.get("dropoff")) != car.get("dropoff"):
        out.append(("error", f"pickup/dropoff {p.get('pickup')}→{p.get('dropoff')} differs from trip.json ({car.get('pickup')}→{car.get('dropoff')})"))
    if p.get("argentina") and not car.get("argentina_allowed", False):
        out.append(("error", "the plan crosses into Argentina but the car isn't allowed to"))
    maxsac = hk.get("max_sac", "T6"); excl = set(hk.get("excluded_hazards", []))
    used, over, multi = plan_counts(p)
    for h in used:
        g, nm = GRADE[h], H[h][0]
        if SAC.index(g["sac"]) > SAC.index(maxsac):
            out.append(("error", f"{nm}: {g['sac']} is above your limit {maxsac}"))
        bad = excl & set(g["hazards"])
        if bad:
            out.append(("error", f"{nm}: has excluded hazard(s) {', '.join(sorted(bad))}"))
        if g["kind"] == "day":
            km, gain = hike_km(h), hike_gain(h)
            if km and hk.get("day_hike_max_km") and km > hk["day_hike_max_km"]:
                out.append(("error", f"{nm}: ≈{km:.0f} km is over the day-hike limit of {hk['day_hike_max_km']} km"))
            if gain and hk.get("day_hike_max_ascent_m") and gain > hk["day_hike_max_ascent_m"]:
                out.append(("error", f"{nm}: ≈{gain:.0f} m ascent is over the limit of {hk['day_hike_max_ascent_m']} m"))
    for label, lst, key in (("one-night trips", over, "overnight_trips"), ("multi-day treks", multi, "multiday_treks")):
        lim = hk.get(key, {})
        if lim.get("max") is not None and len(lst) > lim["max"]:
            out.append(("error", f"{len(lst)} {label}, but you asked for at most {lim['max']}"))
        if lim.get("min") and len(lst) < lim["min"]:
            out.append(("warn", f"only {len(lst)} {label}; you asked for at least {lim['min']}"))
    md = hk.get("multiday_treks", {}).get("max_days")
    for h in multi:
        n_days = sum(1 for d in p["days"] if h in d[2])
        if n_days != GRADE[h]["nights"] + 1:
            out.append(("warn", f"{H[h][0]}: {n_days} plan days but the trek has {GRADE[h]['nights']} nights ({GRADE[h]['nights'] + 1} days)"))
        if md and GRADE[h]["nights"] + 1 > md:
            out.append(("error", f"{H[h][0]}: {GRADE[h]['nights'] + 1} days is longer than your maximum of {md}"))
    flex = sum(1 for d in p["days"] if d[5] == "buffer")
    if flex < hk.get("flex_days_min", 0):
        out.append(("warn", f"{flex} flex days; you asked for at least {hk['flex_days_min']}"))
    if p["num"] in BUDGET:
        pp = per_person(budget_total(p["num"])); mx = req.get("budget", {}).get("max_per_person")
        if mx and pp > mx:
            out.append(("error", f"budget ≈€{pp} per person is over your maximum of €{mx:,}"))
        elif mx and pp > 0.9 * mx:
            out.append(("warn", f"budget ≈€{pp} per person is within 10 % of your maximum"))
    return out

def requirements_html(p):
    issues = validate_plan(p)
    used, over, multi = plan_counts(p)
    hk = TRIP.get("hiking", {})
    facts = (f"Hardest hike: {max((GRADE[h]['sac'] for h in used), key=SAC.index, default='–')} (your limit {hk.get('max_sac', '–')}) · "
             f"one-night trips: {len(over)} · multi-day treks: {len(multi)} · "
             f"car: {p.get('pickup', TRIP['car']['pickup'])} → {p.get('dropoff', TRIP['car']['dropoff'])}")
    if not issues:
        return f'<div class="reqbox ok"><b>✓ Meets all your requirements</b> <span>(trip.json)</span><div class="reqfacts">{esc(facts)}</div></div>'
    li = "".join(f"<li class='lv-{lv}'>{'✖' if lv == 'error' else '⚠'} {esc(m)}</li>" for lv, m in issues)
    lvl = "bad" if any(lv == "error" for lv, _ in issues) else "warn"
    return f'<div class="reqbox {lvl}"><b>Requirement check</b> <span>(trip.json)</span><ul class="clean">{li}</ul><div class="reqfacts">{esc(facts)}</div></div>'

def check_cell(p):
    issues = validate_plan(p)
    if not issues: return "✓"
    e = sum(1 for lv, _ in issues if lv == "error"); w = len(issues) - e
    return " ".join(x for x in (f"✖ {e}" if e else "", f"⚠ {w}" if w else "") if x)

# ---------------------------------------------------------------- GPT options (overlay, only behind the switch)
def gpt_for(p):
    return [g for g in GPT_OPTS if p["num"] in g["fits"]]
def gpt_line(g):
    if g["route"] == "toro": return ll(TRAILS["toro"], 0.00004), False
    if g["route"]: return ll(GPT_TRAILS[g["route"]], 0.00004), False
    if len(g["pts"]) > 1: return [[a, b] for a, b in g["pts"]], True
    return None, False


def rdp(pts, eps):
    if len(pts) < 3: return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1; n = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]; d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n
        if d > dmax: dmax, idx = d, i
    if dmax > eps: return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]

def ll(coords, eps):  # geojson [lon,lat] -> simplified [lat,lon] rounded
    return [[round(y, 5), round(x, 5)] for x, y in rdp(coords, eps)]

def hike_dates(p):
    m = {}
    for i, d in enumerate(p["days"]):
        for h in d[2]: m.setdefault(h, []).append(date_of(i)[0])
    return m

def map_data(p):
    dates = hike_dates(p)
    hikes = []
    for h, ds in dates.items():
        n, area, dist, gain, t, grade, big, note = H[h]
        line, gap = None, None
        if h in TRAILS:
            line = ll(TRAILS[h], 0.00004)
            end = HP[h]
            if math.hypot(line[-1][0] - end[0], line[-1][1] - end[1]) > 0.003:  # routing stopped short
                gap = [line[-1], [end[0], end[1]]]
        hikes.append(dict(id=h, name=n, area=area, dist=dist, gain=gain, time=t, grade=grade, big=big,
                          pt=HP[h], line=line, gap=gap, dates=ds, note=POINT_NOTE.get(h, ""), camps=GRADE[h]["camps"], sac=GRADE[h]["sac"]))
    dv = DRIVE[p["num"]]
    legs = [dict(type=l["type"], c=ll(l["coords"], 0.0015) if l["type"] == "car" else [[y, x] for x, y in l["coords"]]) for l in dv["legs"]]
    gpts = []
    for g in gpt_for(p):
        line, approx = gpt_line(g)
        gpts.append(dict(id=g["id"], name=g["name"], kind=g["kind"], verdict=g["verdict"], dist=g["dist"], gain=g["gain"], time=g["time"],
                         pt=list(g["pts"][-1]), line=line, approx=approx,
                         dates=[date_of(i)[0] + ": " + t for i, t in g["fits"][p["num"]]]))
    return dict(hikes=hikes, legs=legs, stops=[dict(name=n, pt=pt) for n, pt in dv["stops"]], gpt=gpts)

TOGGLE_JS = """<script>
(function(){
  let on = false; try { on = localStorage.getItem('showGpt') === '1'; } catch (e) {}
  const cb = document.getElementById('gpttoggle');
  window.setGpt = v => { document.body.classList.toggle('show-gpt', v); if (cb) cb.checked = v;
    try { localStorage.setItem('showGpt', v ? '1' : '0'); } catch (e) {}
    if (window.setGptLayer) window.setGptLayer(v); };
  if (cb) cb.addEventListener('change', () => setGpt(cb.checked));
  setGpt(on);
})();
</script>"""

MAP_JS = r"""
(function(){
const D = window.PLAN_MAP;
const map = L.map('map', {scrollWheelZoom: false});
const topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {maxZoom: 17, attribution: 'Map data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, SRTM | Style © <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)'});
const osm = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, tiles: <a href="https://www.hotosm.org/">HOT</a> / OSM France'});
const cyc = L.tileLayer('https://{s}.tile-cyclosm.openstreetmap.fr/cyclosm/{z}/{x}/{y}.png', {maxZoom: 18, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, style: <a href="https://www.cyclosm.org">CyclOSM</a>'});
const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {maxZoom: 18, attribution: 'Imagery © Esri'});
const wmt = L.tileLayer('https://tile.waymarkedtrails.org/hiking/{z}/{x}/{y}.png', {maxZoom: 18, opacity: 0.8, attribution: 'Hiking routes © <a href="https://hiking.waymarkedtrails.org">Waymarked Trails</a>'});
topo.addTo(map);
const css = getComputedStyle(document.documentElement);
const cRoute = '#3d6f99', cTrail = '#d9480f', cShort = '#6b7280';
const routeL = L.layerGroup(), trailL = L.layerGroup(), stopL = L.layerGroup();
const bounds = [];
D.legs.forEach(l => {
  const pl = L.polyline(l.c, l.type === 'ferry' ? {color: cRoute, weight: 3, dashArray: '6 8', opacity: .9} : {color: cRoute, weight: 4, opacity: .75});
  if (l.type === 'ferry') pl.bindTooltip('Car ferry Chile Chico ⇄ Puerto Ibáñez');
  pl.addTo(routeL); l.c.forEach(p => bounds.push(p));
});
D.stops.forEach(s => {
  L.circleMarker(s.pt, {radius: 5, color: '#fff', weight: 2, fillColor: '#1d2421', fillOpacity: 1})
   .bindTooltip(s.name, {direction: 'top', offset: [0, -4]}).addTo(stopL);
});
const markers = {};
D.hikes.forEach(h => {
  if (h.line) {
    L.polyline(h.line, {color: '#fff', weight: 7, opacity: .8}).addTo(trailL);
    L.polyline(h.line, {color: h.big ? cTrail : cShort, weight: 4}).addTo(trailL);
  }
  if (h.gap) L.polyline(h.gap, {color: h.big ? cTrail : cShort, weight: 3, dashArray: '4 6'}).bindTooltip('Last section not in the routing data, drawn as a straight line').addTo(trailL);
  const html = `<div class="pop"><b>${h.name}</b><div class="pa">${h.area}</div>
    <div>${h.dist} · ${h.gain} gain · ${h.time}</div><div class="pg">${h.grade} · SAC ${h.sac}</div>
    <div class="pd">In this plan: ${h.dates.join(', ')}</div>${h.note ? `<div class="pa">${h.note}</div>` : ''}
    <a href="#h-${h.id}">Details ↓</a></div>`;
  const m = L.circleMarker(h.pt, {radius: h.big ? 8 : 6, color: '#fff', weight: 2, fillColor: h.big ? cTrail : cShort, fillOpacity: 1})
    .bindPopup(html).bindTooltip(h.name.split(':')[0].split(' (')[0], {direction: 'top', offset: [0, -6]}).addTo(trailL);
  markers[h.id] = m; bounds.push(h.pt);
  (h.camps || []).forEach(c => L.marker(c, {icon: L.divIcon({className: 'camppin', html: '⛺', iconSize: [20, 20], iconAnchor: [10, 10]})}).bindTooltip('Camp: ' + h.name).addTo(trailL));
});
const gptL = L.layerGroup(); const gptMarkers = {};
(D.gpt || []).forEach(g => {
  if (g.line) L.polyline(g.line, {color: '#7c3aed', weight: 4, dashArray: g.approx ? '2 8' : '10 6', opacity: .95})
     .bindTooltip(g.approx ? 'GPT option (approximate line through key points)' : 'GPT option').addTo(gptL);
  const html = `<div class="pop"><b>GPT option: ${g.name}</b><div class="pa">${g.kind === 'overnight' ? 'Optional one-night trip' : 'Day hike'} · verdict ${g.verdict}</div>
    <div>${g.dist} · ${g.gain} · ${g.time}</div><div class="pd">${g.dates.join('<br>')}</div><a href="#g-${g.id}">Details ↓</a></div>`;
  gptMarkers[g.id] = L.marker(g.pt, {icon: L.divIcon({className: 'gptpin', html: '◆', iconSize: [20, 20], iconAnchor: [10, 10]})})
    .bindPopup(html).bindTooltip('GPT: ' + g.name, {direction: 'top', offset: [0, -8]}).addTo(gptL);
});
routeL.addTo(map); trailL.addTo(map); stopL.addTo(map);
window.setGptLayer = on => { if (on) gptL.addTo(map); else map.removeLayer(gptL); };
window.showGpt = id => { const g = (D.gpt || []).find(x => x.id === id); if (!g) return false;
  setGpt(true); document.getElementById('map').scrollIntoView({behavior: 'smooth', block: 'center'});
  map.fitBounds(L.latLngBounds([g.pt].concat(g.line || [])).pad(0.4), {maxZoom: 13}); setTimeout(() => gptMarkers[id].openPopup(), 400); return false; };
L.control.layers({'Topographic': topo, 'OpenStreetMap': osm, 'Paths & relief (CyclOSM)': cyc, 'Satellite': sat},
  {'Driving route': routeL, 'Hikes & trails': trailL, 'Overnight stops': stopL, 'GPT options (purple)': gptL, 'All marked hiking routes (Waymarked Trails)': wmt},
  {collapsed: window.innerWidth < 640}).addTo(map);
L.control.scale({imperial: false}).addTo(map);
map.fitBounds(bounds, {padding: [20, 20]});
document.getElementById('fitall').onclick = () => map.fitBounds(bounds, {padding: [20, 20]});
window.showHike = id => {
  const h = D.hikes.find(x => x.id === id); if (!h) return false;
  document.getElementById('map').scrollIntoView({behavior: 'smooth', block: 'center'});
  const b = L.latLngBounds([h.pt].concat(h.line || []));
  map.fitBounds(b.pad(0.4), {maxZoom: 14});
  setTimeout(() => markers[id].openPopup(), 400);
  return false;
};
if (document.body.classList.contains('show-gpt')) gptL.addTo(map);
map.on('focus', () => map.scrollWheelZoom.enable()); map.on('blur', () => map.scrollWheelZoom.disable());
})();
"""

def map_html(p):
    data = json.dumps(map_data(p), ensure_ascii=False, separators=(",", ":"))
    return f"""<h2>Map</h2>
<p style="color:var(--muted);font-size:14px;margin-top:0">Click a marker for details. <span style="color:#d9480f">●</span> orange = main hikes, with the trail drawn where OpenStreetMap has it; grey = short walks and sights; blue line = driving route (dashed = ferry); black dots = overnight stops. Use the layer button (top right) to switch to satellite, or to show every marked hiking route in the area. Click on the map to enable scroll-zoom.</p>
<div id="map" role="region" aria-label="Map of the route and hikes"></div>
<div class="mapbar"><button id="fitall" type="button">Show whole route</button><a class="btn ghost" href="plan-{p['num']}.gpx" download>⬇ Download GPX (trails + stops) for offline use</a></div>
<script>window.PLAN_MAP = {data};</script>"""

def gpx_gpt(p):
    x = lambda t: html.escape(str(t), quote=True)
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="patagonia-plans" xmlns="http://www.topografix.com/GPX/1/1">',
           f'<metadata><name>{x("Plan " + str(p["num"]) + " GPT options")}</name></metadata>']
    for g in gpt_for(p):
        for j, (a, b) in enumerate(g["pts"]):
            nm = g["name"] if j == len(g["pts"]) - 1 else g["name"] + (" (start)" if j == 0 else f" (via {j})")
            out.append(f'<wpt lat="{a}" lon="{b}"><name>{x("GPT: " + nm)}</name><desc>{x(g["dist"] + ", " + g["gain"] + " | " + g["verdict"])}</desc></wpt>')
        line, approx = gpt_line(g)
        if line:
            pts = "".join(f'<trkpt lat="{a}" lon="{b}"/>' for a, b in line)
            out.append(f'<trk><name>{x("GPT: " + g["name"] + (" (approximate)" if approx else ""))}</name><trkseg>{pts}</trkseg></trk>')
    out.append("</gpx>")
    return "\n".join(out)

def gpx(p):
    md = map_data(p)
    x = lambda t: html.escape(str(t), quote=True)
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<gpx version="1.1" creator="patagonia-plans" xmlns="http://www.topografix.com/GPX/1/1">',
           f'<metadata><name>{x("Plan " + str(p["num"]) + ": " + p["name"])}</name></metadata>']
    for h in md["hikes"]:
        out.append(f'<wpt lat="{h["pt"][0]}" lon="{h["pt"][1]}"><name>{x(h["name"])}</name><desc>{x(h["dist"] + ", " + h["gain"] + ", " + h["time"] + " | " + ", ".join(h["dates"]))}</desc><type>hike</type></wpt>')
    for s in md["stops"]:
        out.append(f'<wpt lat="{s["pt"][0]}" lon="{s["pt"][1]}"><name>{x(s["name"])}</name><type>overnight</type></wpt>')
    for h in md["hikes"]:
        if h["id"] in TRAILS:
            pts = "".join(f'<trkpt lat="{y:.6f}" lon="{xx:.6f}"/>' for xx, y in TRAILS[h["id"]])
            out.append(f'<trk><name>{x(h["name"])}</name><type>hiking</type><trkseg>{pts}</trkseg></trk>')
    for i, l in enumerate(md["legs"]):
        pts = "".join(f'<trkpt lat="{a}" lon="{b}"/>' for a, b in l["c"])
        out.append(f'<trk><name>Driving {i+1}{" (ferry)" if l["type"]=="ferry" else ""}</name><type>driving</type><trkseg>{pts}</trkseg></trk>')
    out.append("</gpx>")
    return "\n".join(out)

# ---------------------------------------------------------------- html
CSS = r"""
:root{--trek:#b45309;--gpt:#7c3aed;--gpt-soft:#f1ebfd;--bg:#f6f4ef;--surface:#ffffff;--ink:#1d2421;--muted:#5d6762;--line:#e1ddd3;--accent:#2f6f62;--accent-soft:#e3efe9;
--hike:#2f6f62;--travel:#8a6d3b;--buffer:#6a5f9e;--mix:#3d6f99;--warn:#9a4a2a;--warn-soft:#f7e9e1;--chip:#efece4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--trek:#f59e0b;--gpt:#a78bfa;--gpt-soft:#2a2140;--bg:#141816;--surface:#1c211f;--ink:#e7ece9;--muted:#a1aca6;--line:#2c3330;--accent:#7cc4b1;--accent-soft:#1f3530;
--hike:#7cc4b1;--travel:#d4b37a;--buffer:#b2a7e6;--mix:#8fbbe3;--warn:#e7a07f;--warn-soft:#3a271e;--chip:#252b28}}
:root[data-theme="dark"]{--trek:#f59e0b;--gpt:#a78bfa;--gpt-soft:#2a2140;--bg:#141816;--surface:#1c211f;--ink:#e7ece9;--muted:#a1aca6;--line:#2c3330;--accent:#7cc4b1;--accent-soft:#1f3530;
--hike:#7cc4b1;--travel:#d4b37a;--buffer:#b2a7e6;--mix:#8fbbe3;--warn:#e7a07f;--warn-soft:#3a271e;--chip:#252b28}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
a{color:var(--accent)}
header.hero{margin-bottom:28px}
.eyebrow{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 6px}
h1{font-size:clamp(28px,5vw,42px);line-height:1.1;margin:0 0 12px;letter-spacing:-.01em}
h2{font-size:22px;margin:40px 0 14px}
h3{font-size:17px;margin:0 0 6px}
.lede{font-size:18px;color:var(--muted);max-width:760px;margin:0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.stat b{display:block;font-size:24px;font-variant-numeric:tabular-nums}
.stat span{font-size:13px;color:var(--muted)}
.route{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0 10px}
.route .stop{background:var(--chip);border-radius:999px;padding:4px 12px;font-size:14px}
.route .arr{color:var(--muted)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px 20px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:720px){.grid2{grid-template-columns:1fr}}
ul.clean{margin:6px 0 0;padding-left:20px}
ul.clean li{margin:4px 0}
.days{display:flex;flex-direction:column;gap:8px}
.day{display:grid;grid-template-columns:92px 1fr;gap:14px;background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--k);border-radius:10px;padding:12px 16px}
.day .date{font-variant-numeric:tabular-nums}
.day .date b{display:block;font-size:17px}
.day .date small{color:var(--muted)}
.day .t{font-weight:600}
.day .meta{font-size:14px;color:var(--muted);margin-top:2px}
.day .note{font-size:14px;margin-top:6px}
.day .hk{margin-top:6px;display:flex;flex-wrap:wrap;gap:6px}
.pill{font-size:13px;border-radius:999px;padding:2px 10px;background:var(--accent-soft);color:var(--ink);text-decoration:none;border:1px solid transparent}
.pill.small{background:var(--chip)}
.k-trek{--k:var(--trek)}.k-hike{--k:var(--hike)}.k-travel{--k:var(--travel)}.k-buffer{--k:var(--buffer)}.k-mix{--k:var(--mix)}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--muted);margin-bottom:10px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
@media (max-width:520px){.day{grid-template-columns:1fr;gap:4px}.day .date b{display:inline;margin-right:6px}}
.hikes{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.hike .area{font-size:13px;color:var(--muted);margin-bottom:8px}
.hike dl{display:grid;grid-template-columns:repeat(4,auto);gap:2px 12px;margin:0 0 8px;font-size:13px}
.hike dt{color:var(--muted)}
.hike dd{margin:0;font-weight:600;font-variant-numeric:tabular-nums}
.hike p{margin:0;font-size:14px}
.grade{display:inline-block;font-size:12px;padding:1px 8px;border-radius:6px;background:var(--chip);margin-bottom:6px}
.warn{background:var(--warn-soft);border:1px solid var(--line);border-left:5px solid var(--warn);border-radius:10px;padding:14px 18px;margin:16px 0}
.btn{display:inline-block;background:var(--accent);color:var(--bg);text-decoration:none;padding:8px 14px;border-radius:8px;font-weight:600;font-size:14px}
nav.top{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:14px;margin-bottom:24px}
nav.top a{text-decoration:none}
nav.top a.cur{font-weight:700;color:var(--ink)}
table{border-collapse:collapse;width:100%;font-size:14px}
.tscroll{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600}
tr:last-child td{border-bottom:none}
.plancards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.plancard{display:flex;flex-direction:column;gap:8px}
.plancard .num{font-size:13px;color:var(--muted)}
.plancard p{margin:0;font-size:15px}
.plancard .spacer{flex:1}
#map{height:560px;border-radius:14px;border:1px solid var(--line);background:var(--surface);z-index:0}
@media (max-width:640px){#map{height:440px}}
.mapbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:10px}
.mapbar button{font:inherit;font-size:14px;font-weight:600;padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:var(--surface);color:var(--ink);cursor:pointer}
.btn.ghost{background:var(--surface);color:var(--accent);border:1px solid var(--line)}
.onmap{float:right;font-size:13px;text-decoration:none;margin-left:8px}
.leaflet-popup-content{font:14px/1.45 system-ui,sans-serif;color:#1d2421}
.pop .pa{color:#5d6762;font-size:12px;margin:2px 0 4px}.pop .pg{font-size:12px;margin:2px 0}.pop .pd{font-size:12px;margin:4px 0;font-weight:600}
small.muted{color:var(--muted)}
.reqbox{border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:0 0 14px;background:var(--surface)}
.reqbox.ok{border-left:5px solid var(--hike)}.reqbox.warn{border-left:5px solid var(--travel)}.reqbox.bad{border-left:5px solid var(--warn);background:var(--warn-soft)}
.reqbox span{color:var(--muted);font-size:13px}.reqbox ul{margin:6px 0}.reqfacts{font-size:13px;color:var(--muted);margin-top:4px}
.grade.sac{background:var(--accent-soft)}
.camppin{font-size:16px;line-height:20px;text-align:center}
.gptbar{display:flex;gap:14px;align-items:flex-start;background:var(--gpt-soft);border:1px solid var(--line);border-left:5px solid var(--gpt);border-radius:12px;padding:14px 16px;margin:14px 0}
.gptbar span{font-size:14px;color:var(--muted)}
.switch{position:relative;display:inline-block;width:46px;height:26px;flex:none;margin-top:2px}
.switch input{opacity:0;width:0;height:0}
.slider{position:absolute;inset:0;background:var(--line);border-radius:26px;cursor:pointer;transition:.2s}
.slider:before{content:"";position:absolute;width:20px;height:20px;left:3px;top:3px;background:#fff;border-radius:50%;transition:.2s}
.switch input:checked+.slider{background:var(--gpt)}
.switch input:checked+.slider:before{transform:translateX(20px)}
.switch input:focus-visible+.slider{outline:2px solid var(--gpt);outline-offset:2px}
.gpt-only{display:none}
body.show-gpt .gpt-only{display:block}
.gptalt{margin-top:8px;font-size:14px;background:var(--gpt-soft);border-left:3px solid var(--gpt);padding:6px 10px;border-radius:6px}
.gptalt a{color:var(--gpt)}
.gptcard{border-top:4px solid var(--gpt)}
.gptcard p{margin:6px 0}
.gptbadge{background:var(--gpt);color:#fff}
.gptwarn{background:var(--warn-soft);border-radius:6px;padding:6px 8px}
.gptpin{color:#7c3aed;font-size:20px;line-height:20px;text-align:center;text-shadow:0 0 3px #fff,0 0 3px #fff}
footer{margin-top:48px;font-size:13px;color:var(--muted)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.gitem{background:var(--surface);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin:0}
.gitem button{all:unset;cursor:zoom-in;display:block}
.gitem .main img{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;background:var(--chip)}
.gitem .thumbs{display:grid;grid-template-columns:1fr 1fr;gap:2px;margin-top:2px}
.gitem .thumbs img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;background:var(--chip)}
.gitem figcaption{padding:8px 12px 10px;font-size:14px}
.gitem figcaption small{display:block;color:var(--muted);font-size:12px}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;z-index:2000;align-items:center;justify-content:center;flex-direction:column}
.lb.open{display:flex}
.lb img{max-width:94vw;max-height:84vh;object-fit:contain}
.lb .cap{color:#eee;font-size:15px;margin-top:10px;text-align:center;padding:0 16px}
.lb button{position:absolute;background:rgba(255,255,255,.12);color:#fff;border:0;border-radius:999px;width:44px;height:44px;font-size:24px;cursor:pointer}
.lb .x{top:14px;right:14px}.lb .prev{left:10px;top:50%}.lb .next{right:10px;top:50%}
"""

def esc(s): return html.escape(s, quote=True)

def date_of(i):
    d = START + dt.timedelta(days=i)
    return d.strftime("%b %-d"), d.strftime("%a")

def maps_link(route):
    AR = {"El Chaltén", "El Calafate", "Los Antiguos"}
    def q(x):
        if "Argentina" in x: return x
        if x == "Parque Patagonia": x = "Parque Nacional Patagonia"
        return x + (", Argentina" if x in AR else ", Chile")
    return "https://www.google.com/maps/dir/" + "/".join(urllib.parse.quote_plus(q(x)) for x in ["Balmaceda"] + route + ["Balmaceda"])

def nav(cur):
    items = [("index.html", "Overview")] + [(p["slug"] + ".html", f'{p["num"]}. {p["name"]}') for p in PLANS]
    return '<nav class="top">' + "".join(f'<a href="{h}"{" class=cur" if h==cur else ""}>{esc(t)}</a>' for h, t in items) + "</nav>"

def page(title, body, desc, head="", tail=""):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="stylesheet" href="style.css">{head}</head>
<body><div class="wrap">{body}
<footer>All distances, elevation gains and times are approximate planning figures. Maps need an internet connection; download the GPX for offline use. Map data © OpenStreetMap contributors. Check trail conditions with CONAF / park rangers, and current rules (fees, bookings, closures) before each hike. {esc(TRIP.get('footer_note', ''))}</footer>
</div>{tail}</body></html>"""

def stats(p):
    big = sum(1 for d in p["days"] if any(H[h][6] for h in d[2]))
    buf = sum(1 for d in p["days"] if d[5] == "buffer")
    travel = sum(1 for d in p["days"] if d[5] == "travel")
    bases = len({d[4] for d in p["days"][:-1]})
    return big, buf, travel, bases

def hike_card(hid):
    n, area, dist, gain, t, grade, big, note = H[hid]
    g = GRADE[hid]
    return f"""<div class="card hike" id="h-{hid}"><span class="grade">{esc(grade)}</span> <span class="grade sac">SAC {g['sac']}{' · ' + ('1 night' if g['kind'] == 'overnight' else f"{g['nights'] + 1}-day trek") if g['kind'] in ('overnight', 'multiday') else ''}</span><h3>{esc(n)}</h3><div class="area">{esc(area)}</div>
<a class="onmap" href="#map" onclick="return showHike('{hid}')">📍 Show on map</a><dl><dt>Distance</dt><dt>Gain</dt><dt>Time</dt><dt></dt><dd>{esc(dist)}</dd><dd>{esc(gain)}</dd><dd>{esc(t)}</dd><dd></dd></dl><p>{esc(note)}</p></div>"""

def gpt_switch(p):
    gs = gpt_for(p)
    return f"""<div class="gptbar"><label class="switch"><input type="checkbox" id="gpttoggle"><span class="slider"></span></label>
<div><b>Show GPT options ({len(gs)})</b><br><span>Extra hikes from the Greater Patagonian Trail manual, checked against your limits and recent reports (Nov 2026). Turning this on only <i>adds</i> purple suggestions; the plan itself doesn't change. <a href="{REPORTS_REL}/README.md">Read the full scouting reports</a>.</span></div></div>"""

def gpt_section(p):
    cards = []
    for g in gpt_for(p):
        fits = "".join(f"<li><b>{date_of(i)[0]}</b>: {esc(t)}</li>" for i, t in g["fits"][p["num"]])
        badge = "One night (optional)" if g["kind"] == "overnight" else "Day hike"
        cards.append(f"""<div class="card hike gptcard" id="g-{g['id']}"><a class="onmap" href="#map" onclick="return showGpt('{g['id']}')">📍 Show on map</a>
<span class="grade gptbadge">{badge}</span> <span class="grade">Verdict: {esc(g['verdict'])}</span> <span class="grade">Confidence: {esc(g['conf'])}</span>
<h3>{esc(g['name'])}</h3><div class="area">{esc(g['area'])} · {esc(g['ref'])}</div>
<dl><dt>Distance</dt><dt>Gain</dt><dt>Time</dt><dt></dt><dd>{esc(g['dist'])}</dd><dd>{esc(g['gain'])}</dd><dd>{esc(g['time'])}</dd><dd></dd></dl>
<p>{esc(g['terrain'])}</p><p><b>Cost:</b> {esc(g['cost'])}</p><p class="gptwarn"><b>⚠ </b>{esc(g['caution'])}</p><p><b>Why:</b> {esc(g['why'])}</p>
<p><b>Fits this plan:</b></p><ul class="clean">{fits}</ul><p style="font-size:13px"><a href="{REPORTS_REL}/{g['report']}">Full scouting report →</a></p></div>""")
    return f"""<section class="gpt-only"><h2>GPT options for this plan</h2>
<p style="color:var(--muted);font-size:14px;margin-top:0">Verdicts: ADD = fits your limits; ADD* = fits, but one thing must be confirmed first; MAYBE = worth considering, with caveats. Dashed purple lines on the map are routed along OpenStreetMap paths; dotted ones only connect key points and are approximate. These options are not counted in the budget or stats above.</p>
<div class="hikes">{''.join(cards)}</div>
<p><a class="btn ghost" href="plan-{p['num']}-gpt.gpx" download>⬇ GPX of the GPT options</a></p></section>"""

def budget_total(num):
    return sum(BUDGET[num][:5])

def budget_html(p):
    f, fu, sl, fe, mi, note = BUDGET[p["num"]]
    tot = budget_total(p["num"])
    pp = per_person(tot)
    mx = TRIP["budget"]["max_per_person"]
    verdict = (f"≈€{pp} per person, well under your €{mx:,}-per-person maximum." if pp <= 0.8 * mx else
               f"≈€{pp} per person, close to your €{mx:,} maximum." if pp <= mx else
               f"≈€{pp} per person: OVER your €{mx:,}-per-person maximum.")
    rows = [("Food (self-catering, cooking in camp)", f), (f"Fuel (≈{p['km']} km, a diesel 4x4 using ≈10 L/100 km)", fu),
            ("Campgrounds (some free nights)", sl), ("Park and trail fees, ferries", fe), ("Miscellaneous: gas canisters, showers, laundry, SIM card", mi)]
    tr = "".join(f"<tr><td>{esc(a)}</td><td style='text-align:right'>€{b}</td></tr>" for a, b in rows)
    return f"""<h2>Budget estimate ({PEOPLE} people)</h2>
<div class="tscroll"><table><tbody>{tr}<tr><td><b>Total for {'both of you' if PEOPLE == 2 else f'all {PEOPLE} of you'}</b></td><td style='text-align:right'><b>≈€{tot}</b></td></tr><tr><td><b>Per person</b></td><td style='text-align:right'><b>≈€{per_person(tot)}</b></td></tr></tbody></table></div>
<p style="font-size:14px;color:var(--muted)"><b style="color:var(--ink)">{verdict}</b> {esc(note)} These are rough figures based on recent prices, not counting flights or the car.</p>"""

def sleep_html(p):
    bases = []
    for d in p["days"][:-1]:
        if d[4] not in bases: bases.append(d[4])
    li = "".join(f"<li><b>{esc(b)}:</b> {esc(SLEEP.get(b, ''))}</li>" for b in bases if SLEEP.get(b))
    return f"""<h2>Sleeping in the car on this route</h2><div class="card"><ul class="clean">{li}</ul>
<p style="font-size:14px;color:var(--muted);margin:10px 0 0">Between these places, <b>iOverlander</b> lists free and cheap spots. Most land along the Carretera is private and fenced, so ask before you park. Wild camping inside national parks is not allowed.</p></div>"""

def gallery_items(p):
    """Photo groups in day order: each hike when it first appears, and each overnight place the first night there."""
    sys.path.insert(0, HERE)
    from photos import place_for
    items, seen = [], set()
    for i, d in enumerate(p["days"]):
        date = date_of(i)[0]
        for h in d[2]:
            if h not in seen and PHOTOS.get(h):
                seen.add(h); items.append((date, H[h][0].split(":")[0], H[h][1], PHOTOS[h], f"#h-{h}"))
        pl = place_for(d[4])
        if pl and pl not in seen and PHOTOS.get(pl):
            seen.add(pl); items.append((date, pl, "Overnight: " + d[4], PHOTOS[pl], None))
    return items

def gallery_html(p):
    items = gallery_items(p)
    if not items: return ""
    figs, n = [], 0
    for date, name, sub, photos, link in items:
        cap = f"{date} · {name}"
        def img(ph, cls):
            nonlocal n
            n += 1
            return (f'<button type="button" data-i="{n - 1}" data-full="{esc(ph["full"])}" data-cap="{esc(cap + (" — " + ph["shows"] if ph.get("shows") else ""))}" aria-label="Enlarge photo: {esc(name)}">'
                    f'<img src="{esc(ph["thumb"])}" alt="{esc(name)}" loading="lazy" referrerpolicy="no-referrer"></button>')
        main = img(photos[0], "main")
        thumbs = "".join(img(ph, "t") for ph in photos[1:3])
        title = f'<a href="{link}">{esc(name)}</a>' if link else esc(name)
        figs.append(f'<figure class="gitem"><div class="main">{main}</div>{f"<div class=thumbs>{thumbs}</div>" if thumbs else ""}'
                    f'<figcaption><b>{esc(date)}</b> · {title}<small>{esc(sub)}</small></figcaption></figure>')
    return f"""<h2 id="gallery">What it looks like</h2>
<p style="color:var(--muted);font-size:14px;margin-top:0">Photos of the hikes and overnight stops, in the order you reach them. Click a photo to enlarge it; use ← → to browse. The photos come from Wikimedia Commons and load from the internet.</p>
<div class="gallery">{''.join(figs)}</div>
<div class="lb" role="dialog" aria-modal="true" aria-label="Photo viewer"><button class="x" type="button" aria-label="Close">×</button><button class="prev" type="button" aria-label="Previous">‹</button><img alt=""><div class="cap"></div><button class="next" type="button" aria-label="Next">›</button></div>"""

GALLERY_JS = """<script>(function(){
const bs=[...document.querySelectorAll('.gallery button[data-i]')], lb=document.querySelector('.lb'); if(!lb) return;
const im=lb.querySelector('img'), cap=lb.querySelector('.cap'); let cur=0;
function show(i){cur=(i+bs.length)%bs.length; const b=bs[cur]; im.src=b.dataset.full; cap.textContent=b.dataset.cap+'  ('+(cur+1)+' / '+bs.length+')'; lb.classList.add('open');}
function close(){lb.classList.remove('open'); im.removeAttribute('src'); bs[cur].focus();}
bs.forEach(b=>b.addEventListener('click',()=>show(+b.dataset.i)));
im.referrerPolicy='no-referrer';
lb.querySelector('.x').onclick=close; lb.querySelector('.prev').onclick=()=>show(cur-1); lb.querySelector('.next').onclick=()=>show(cur+1);
lb.addEventListener('click',e=>{if(e.target===lb) close();});
document.addEventListener('keydown',e=>{if(!lb.classList.contains('open')) return; if(e.key==='Escape') close(); else if(e.key==='ArrowLeft') show(cur-1); else if(e.key==='ArrowRight') show(cur+1);});
})();</script>"""

def plan_page(p):
    big, buf, travel, bases = stats(p)
    hkm, hgain = hike_totals(p)
    days_html = []
    galt = {}
    for g in gpt_for(p):
        for i, txt in g['fits'][p['num']]: galt.setdefault(i, []).append((g, txt))
    for i, (t, drive, hikes, note, sleep, kind) in enumerate(p["days"]):
        d, wd = date_of(i)
        gx = ''.join(f'<div class="gptalt gpt-only"><b>GPT option{" (1 night)" if g["kind"]=="overnight" else ""}:</b> <a href="#g-{g["id"]}">{esc(g["name"])}</a>, {esc(txt)}</div>' for g, txt in galt.get(i, []))
        pills = "".join(f'<a class="pill{"" if H[h][6] else " small"}" href="#h-{h}">{esc(H[h][0].split(":")[0] if len(H[h][0])>48 else H[h][0])}</a>' for h in hikes)
        days_html.append(f"""<div class="day k-{kind}"><div class="date"><b>{d}</b><small>{wd} · day {i+1}</small></div>
<div><div class="t">{esc(t)}</div><div class="meta">{("🚗 " + esc(drive) + " &nbsp;·&nbsp; ") if drive != "–" else ""}🚐 {esc(sleep)}</div>
{f'<div class="hk">{pills}</div>' if pills else ''}{f'<div class="note">{esc(note)}</div>' if note else ''}{gx}</div></div>""")
    seen = []
    for d in p["days"]:
        for h in d[2]:
            if h not in seen: seen.append(h)
    seen.sort(key=lambda h: not H[h][6])
    route = '<span class="arr">→</span>'.join(f'<span class="stop">{esc(s)}</span>' for s in ["Balmaceda"] + p["route"][1:] + ["Balmaceda"])
    arg = ('<div class="warn"><b>Argentina with a rental car.</b> You need written permission from the rental company and the cross-border insurance it supplies. Arrange it when you book: it usually costs a fixed extra fee and takes days to prepare. Not every Balmaceda agency allows it. Chile (SAG) and Argentina both confiscate fresh fruit, vegetables, meat and dairy at the border, so cross with none.</div>' if p["argentina"] else "")
    body = f"""{nav(p['slug'] + '.html')}
<header class="hero"><p class="eyebrow">{esc(TRIP['short_title'])} · Plan {p['num']} of {len(PLANS)}</p><h1>{esc(p['name'])}</h1><p class="lede">{esc(p['tag'])}</p></header>
<div class="stats">
<div class="stat"><b>{big}</b><span>days with a proper hike</span></div>
<div class="stat"><b>{buf}</b><span>flex / weather days</span></div>
<div class="stat"><b>{travel}</b><span>mainly driving days</span></div>
<div class="stat"><b>≈{hkm:,} km</b><span>hiking in total</span></div>
<div class="stat"><b>≈{hgain:,} m</b><span>total ascent on hikes</span></div>
<div class="stat"><b>{p['km']} km</b><span>total driving</span></div>
<div class="stat"><b>{bases}</b><span>different overnight spots</span></div>
<div class="stat"><b>{"Yes" if p["argentina"] else "No"}</b><span>crosses into Argentina</span></div>
</div>
{requirements_html(p)}
<div class="card"><h3>Best for</h3><p style="margin:0">{esc(p['who'])}</p>
<div class="route">{route}</div>
<a class="btn" href="{esc(maps_link(p['route'][1:]))}" target="_blank" rel="noopener">Open route in Google Maps</a></div>
{gpt_switch(p)}
{arg}
<div class="grid2" style="margin-top:14px"><div class="card"><h3>Why choose it</h3><ul class="clean">{''.join(f'<li>{esc(x)}</li>' for x in p['pros'])}</ul></div>
<div class="card"><h3>Trade-offs</h3><ul class="clean">{''.join(f'<li>{esc(x)}</li>' for x in p['cons'])}</ul></div></div>
{map_html(p)}
{gallery_html(p)}
{gpt_section(p)}
{budget_html(p)}
{sleep_html(p)}
<h2>Day by day</h2>
<div class="legend"><span><i style="background:var(--hike)"></i>Hiking day</span><span><i style="background:var(--mix)"></i>Drive and hike</span><span><i style="background:var(--travel)"></i>Mainly driving</span><span><i style="background:var(--buffer)"></i>Flex day (weather insurance)</span>{'<span><i style="background:var(--trek)"></i>Trek / overnight hike</span>' if any(d[5] == "trek" for d in p["days"]) else ""}</div>
<p style="color:var(--muted);font-size:14px;margin-top:0">{esc(TRIP.get('arrival_note', ''))}</p>
<div class="days">{''.join(days_html)}</div>
<h2>The hikes in this plan</h2>
<div class="hikes">{''.join(hike_card(h) for h in seen)}</div>
<p style="margin-top:28px"><a href="index.html">← Back to the overview, general safety tips and the comparison of all plans</a></p>"""
    head = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">'
    tail = TOGGLE_JS + '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script><script>' + MAP_JS + '</script>' + GALLERY_JS
    return page(f"Patagonia: {p['name']}", body, p["tag"], head, tail)

def index_page():
    rows = []
    cards = []
    for p in PLANS:
        big, buf, travel, bases = stats(p)
        hkm, hgain = hike_totals(p)
        rows.append(f"<tr><td><a href='{p['slug']}.html'><b>{p['num']}. {esc(p['name'])}</b></a></td><td>{big}</td><td>{buf}</td><td>{travel}</td><td>≈{hkm:,}</td><td>≈{hgain:,} m</td><td>{p['km']}</td><td>{bases}</td><td>{'Yes' if p['argentina'] else 'No'}</td><td>≈€{per_person(budget_total(p['num']))} pp<br><small class=muted>≈€{budget_total(p['num'])} {'for both' if PEOPLE == 2 else 'in total'}</small></td><td>{check_cell(p)}</td></tr>")
        cards.append(f"""<div class="card plancard"><div class="num">Plan {p['num']}{' · 🇦🇷 crosses into Argentina' if p['argentina'] else ' · Chile only'}</div><h3 style="font-size:20px">{esc(p['name'])}</h3>
<p>{esc(p['tag'])}</p><p style="color:var(--muted);font-size:14px"><b>Best for:</b> {esc(p['who'])}</p><div class="spacer"></div><a class="btn" href="{p['slug']}.html">Open plan {p['num']} →</a></div>""")
    body = f"""{nav('index.html')}
""" + INDEX["html"].replace("{CARDS}", "".join(cards)).replace("{ROWS}", "".join(rows)) 
    return page(INDEX["title"], body, INDEX["desc"])


# ---------------------------------------------------------------- build
def plans_summary():
    t = TRIP
    lines = [f"CURRENT PLANS for trip {t['id']} (generated by tools/build.py on {dt.date.today()}). {PEOPLE} people, car {t['car']['pickup']} → {t['car']['dropoff']}, sleeping: {t.get('sleeping')}, {START:%b %d %Y} – {START + dt.timedelta(days=NDAYS - 1):%b %d %Y} ({NDAYS} days).",
             "Requirements: see trip.json in the same folder.",
             "Kinds: hike / mix (drive+hike) / travel (mainly driving) / buffer (flex day, can be replaced) / trek (multi-day hike day).", ""]
    for p in PLANS:
        lines.append(f"=== PLAN {p['num']}: {p['name']} — {p['tag']}")
        for i, (t_, drive, hikes, note, sleep, kind) in enumerate(p["days"]):
            d, wd = date_of(i)
            lines.append(f"{d:7s} {wd} [{kind:6s}] {t_} | drive: {drive} | hikes: {', '.join(H[h][0] for h in hikes) or '-'} | sleep: {sleep}")
        lines.append("")
    return "\n".join(lines)

def build_trip(trip_json):
    t = json.load(open(trip_json, encoding="utf-8"))
    if str(t.get("start_date", "")).startswith("YYYY") or str(t.get("end_date", "")).startswith("YYYY"):
        print(f"[{t.get('id')}] skipped: fill in start_date/end_date in {os.path.relpath(trip_json, ROOT)} first"); return
    load_trip(trip_json)
    if not PLANS:
        print(f"[{TRIP['id']}] no plans yet in plans.py; nothing to build"); return
    os.makedirs(OUT, exist_ok=True)
    for p in PLANS:
        assert len(p["days"]) == NDAYS, (p["name"], len(p["days"]), NDAYS)
        with open(os.path.join(OUT, p["slug"] + ".html"), "w") as f: f.write(plan_page(p))
        with open(os.path.join(OUT, f"plan-{p['num']}.gpx"), "w") as f: f.write(gpx(p))
        with open(os.path.join(OUT, f"plan-{p['num']}-gpt.gpx"), "w") as f: f.write(gpx_gpt(p))
    with open(os.path.join(OUT, "index.html"), "w") as f: f.write(index_page())
    with open(os.path.join(OUT, "style.css"), "w") as f: f.write(CSS)
    print(f"[{TRIP['id']}] → {os.path.relpath(OUT, ROOT) or '.'}")
    for p in PLANS:
        issues = validate_plan(p)
        print(" ", p["num"], p["name"], stats(p), "hiking ≈%d km / ≈%d m" % hike_totals(p), "requirements OK" if not issues else "")
        for lv, msg in issues:
            print(f"      {'ERROR' if lv == 'error' else 'warn '}: {msg}")
    open(os.path.join(TRIP["_dir"], "plans_summary.txt"), "w").write(plans_summary())
    from photos import place_for
    need = []
    for p in PLANS:
        for d in p["days"]:
            for k in d[2] + [place_for(d[4])]:
                if k and k not in need: need.append(k)
    nophoto = [k for k in need if not PHOTOS.get(k) and k not in PHOTOS.get("_pinned", {})]
    if nophoto:
        print(f"  photos: no gallery photos for {', '.join(nophoto)} (run the photo-scout agent, then tools/photos.py --apply)")

def all_trips():
    return sorted(t for t in glob.glob(os.path.join(ROOT, "trips", "*", "trip.json")) if not os.path.basename(os.path.dirname(t)).startswith("_"))

if __name__ == "__main__":
    for tj in (sys.argv[1:] or all_trips()):
        build_trip(tj)
