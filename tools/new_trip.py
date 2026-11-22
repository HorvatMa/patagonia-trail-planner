#!/usr/bin/env python3
"""Create a new trip folder from trips/_template.

    python3 tools/new_trip.py <trip-id>

Copies trips/_template/ to trips/<trip-id>/ and sets "id" and "output_dir" in trip.json.
Then fill in trip.json (requirements) and plans.py (itineraries), run tools/drive.py and tools/build.py."""
import json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", sys.argv[1]):
        sys.exit("usage: python3 tools/new_trip.py <trip-id>   (lowercase letters, digits and dashes, e.g. 2028-puerto-montt)")
    tid = sys.argv[1]
    src, dst = os.path.join(ROOT, "trips", "_template"), os.path.join(ROOT, "trips", tid)
    if os.path.exists(dst):
        sys.exit(f"trips/{tid} already exists")
    shutil.copytree(src, dst)
    p = os.path.join(dst, "trip.json")
    t = json.load(open(p, encoding="utf-8"))
    t["id"] = tid
    t["output_dir"] = f"trips/{tid}/site"
    json.dump(t, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"created trips/{tid}/ (trip.json, plans.py, gpt_opts.py); pages will be written to trips/{tid}/site/")

if __name__ == "__main__":
    main()
