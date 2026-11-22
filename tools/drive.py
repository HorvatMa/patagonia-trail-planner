"""Route the driving legs of a trip's plans on OSM roads (routing.openstreetmap.de).

    python3 tools/drive.py trips/<id>/trip.json

Reads DRIVE_STOPS from trips/<id>/plans.py and coordinates from tools/places.py (PLACES; airport codes work too).
"~X" = take a ferry to X (drawn as a dashed straight line); "(X)" = via-point only (forces the road, no marker).
Writes trips/<id>/geo/drive.json and prints km per plan (car only)."""
import importlib.util, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route import route
from places import PLACES as P

def name(s): return s.strip("~()")

def run(trip_json):
    tdir = os.path.dirname(os.path.abspath(trip_json))
    spec = importlib.util.spec_from_file_location("plans", os.path.join(tdir, "plans.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    missing = sorted({name(s) for stops in m.DRIVE_STOPS.values() for s in stops} - set(P))
    if missing:
        sys.exit(f"Unknown places (add them to tools/places.py PLACES): {missing}")
    out, cache = {}, {}
    for n, stops in m.DRIVE_STOPS.items():
        legs, total, cur = [], 0, [stops[0]]
        def flush():
            nonlocal total
            if len(cur) > 1:
                key = tuple(cur)
                if key not in cache:
                    cache[key] = route("car", [P[name(x)] for x in cur]); time.sleep(1)
                g, d, s = cache[key]
                legs.append({"type": "car", "coords": g}); total += d
                print(f"  plan{n}: {' > '.join(cur)}: {d/1000:.0f} km snaps={s}")
        for st in stops[1:]:
            if st.startswith("~"):
                flush()
                a, b = P[name(cur[-1])], P[name(st)]
                legs.append({"type": "ferry", "coords": [[a[1], a[0]], [b[1], b[0]]]})
                cur[:] = [st]
            else:
                cur.append(st)
                if not st.startswith("("):
                    flush(); cur[:] = [st]
        stopsm = []
        for x in stops:
            if not x.startswith("(") and name(x) not in [s[0] for s in stopsm]:
                stopsm.append((name(x), P[name(x)]))
        out[n] = {"legs": legs, "stops": stopsm, "km": round(total / 1000)}
        print(f"PLAN {n}: {total/1000:.0f} km by car (+ferry)")
    os.makedirs(os.path.join(tdir, "geo"), exist_ok=True)
    json.dump(out, open(os.path.join(tdir, "geo", "drive.json"), "w"))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run(sys.argv[1])
