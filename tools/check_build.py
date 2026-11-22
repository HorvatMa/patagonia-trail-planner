#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit): when generator code (tools/*.py) or trip data (trips/**/*.py,
trips/**/trip.json) changes, rebuild every trip and validate the output. A build failure or broken
output blocks and sends the error back to Claude; requirement-check problems are reported as context."""
import glob, json, os, subprocess, sys
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")

def out(obj):
    print(json.dumps(obj)); sys.exit(0)

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = payload.get("tool_input") or {}
tr = payload.get("tool_response") or {}
path = ti.get("file_path") or (tr.get("filePath") if isinstance(tr, dict) else None) or ""
path = os.path.abspath(path)
# only react to generator sources (not to the hook scripts themselves)
TRIPS = os.path.join(ROOT, "trips")
is_tool = path.startswith(TOOLS + os.sep) and path.endswith(".py") and os.path.basename(path) not in ("check_build.py", "save_scout_report.py")
is_trip = path.startswith(TRIPS + os.sep) and (path.endswith(".py") or path.endswith("trip.json")) and os.sep + "_" not in path[len(TRIPS):]
if not (is_tool or is_trip):
    sys.exit(0)

try:
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "build.py")], cwd=ROOT, capture_output=True, text=True, timeout=120)
except subprocess.TimeoutExpired:
    out({"decision": "block", "reason": "tools/build.py timed out after 120 s."})
if r.returncode != 0:
    out({"decision": "block", "reason": "tools/build.py failed after your edit:\n" + (r.stderr or r.stdout)[-2000:]})

problems = []
outs = []
for tj in sorted(glob.glob(os.path.join(ROOT, "trips", "*", "trip.json"))):
    if os.path.basename(os.path.dirname(tj)).startswith("_"): continue
    t = json.load(open(tj))
    outs.append(os.path.normpath(os.path.join(ROOT, t.get("output_dir", os.path.join("trips", t["id"], "site")))))
gpx_files, pages = [], []
for o in outs:
    gpx_files += glob.glob(os.path.join(o, "*.gpx")); pages += glob.glob(os.path.join(o, "plan-*.html"))
for f in sorted(gpx_files):
    try:
        xml.dom.minidom.parse(f)
    except Exception as e:
        problems.append(f"{os.path.basename(f)}: invalid XML ({e})")
if not pages:
    problems.append("no plan pages were generated")
for f in pages:
    s = open(f, encoding="utf-8").read()
    for needle in ("window.PLAN_MAP", 'id="gpttoggle"', "</html>"):
        if needle not in s:
            problems.append(f"{os.path.basename(f)}: missing {needle!r}")
if problems:
    out({"decision": "block", "reason": "Build ran but the output looks broken:\n- " + "\n- ".join(problems)})

req = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith(("ERROR:", "warn :"))]
msg = f"check_build hook: rebuilt {len(outs)} trip(s), validated {len(pages)} pages and {len(gpx_files)} GPX files."
if req:
    msg += f" Requirement check found {len(req)} issue(s) (full list in the build output / plan pages):\n" + "\n".join(req[:25])
out({"suppressOutput": True, "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}})
