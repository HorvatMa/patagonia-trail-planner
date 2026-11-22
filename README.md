# Patagonia Trail Planner

A small, dependency-free toolkit for planning **car-based hiking trips in Patagonia** (Chile and Argentina). Each trip is defined by a requirements file. The generator turns it into a static website with several alternative itineraries. Each plan gets:
- an interactive map (Leaflet + OpenStreetMap-based tiles) with the driving route and the trails;
- a day-by-day schedule and a card for every hike (SAC grade, distance, ascent, notes);
- budget estimates (per person and in total);
- advice on sleeping in the car;
- GPX downloads for offline navigation;
- an automatic **requirement check** of every plan against the trip's limits.

It was built with [Claude Code](https://claude.com/claude-code), and also includes the Claude Code setup used to research and maintain the plans: subagents, hooks and a `/plan-trip` skill.

> **Planning figures only.** Distances, ascents, times, fees and rules are estimates from research done in Nov 2026. Patagonian fees, closures and booking rules change every season. Check current conditions with park authorities (CONAF, APN, pasesparques.cl) before each hike.

## Viewing the plans
Open `index.html` in a browser: it's the overview of the trip in `trips/2027-balmaceda/`, five itineraries from Balmaceda (Aysén) for Jan 27 – Feb 21 2027. The pages work as local files. The map tiles need an internet connection; for offline use, load the `plan-*.gpx` files into OsmAnd, Maps.me or Gaia GPS.

## Requirements
- Python 3.9+ (standard library only).
- Internet access for routing and geocoding (`routing.openstreetmap.de`, Nominatim). Both are used sparingly and with rate limits.
- Optional: `pdftotext` (poppler) to extract the GPT manual text, and Firefox or Chrome for the headless page checks.

## Layout
| Path | What |
|---|---|
| `tools/build.py` | Generator: `python3 tools/build.py [trips/<id>/trip.json]` (no argument = all trips) |
| `tools/catalog.py` | Shared hike catalogue with SAC grades (T1–T6), hike kind (day / overnight / multi-day), hazard tags and camps |
| `tools/places.py` | Airports usable as start/end points (PMC, BBA, PUQ, PNT, FTE, BRC, USH, EQS) and named places |
| `tools/route.py`, `tools/drive.py` | Route trails on OSM footpaths and driving legs on OSM roads |
| `tools/new_trip.py` | `python3 tools/new_trip.py <id>` creates a trip from `trips/_template/` |
| `trips/<id>/trip.json` | A trip's requirements: dates, people, car pickup/dropoff, Argentina allowed, sleeping style, budget, max SAC grade, day-hike limits, excluded hazards, number of one-night trips and multi-day treks, flex days |
| `trips/<id>/plans.py` | The itineraries, budgets, sleeping notes and driving stops |
| `trips/<id>/gpt_opts.py` | Optional, switchable overlay of Greater Patagonian Trail options |
| `gpt-reports/` | Research reports from the scouting subagents |
| `CLAUDE.md`, `.claude/` | Claude Code project instructions, subagents, the `/plan-trip` skill, hooks |

## Planning a new trip
**With Claude Code:** start it in this folder and run `/plan-trip`. It asks for your requirements, writes `trip.json`, researches hikes in regions the catalogue doesn't cover (with the `hike-researcher` subagent), designs several itineraries, routes them, builds the site and checks it in a browser. It pauses for your approval at three checkpoints.

**By hand:**
```bash
python3 tools/new_trip.py 2028-my-trip   # then edit trips/2028-my-trip/trip.json and plans.py
python3 tools/drive.py trips/2028-my-trip/trip.json
python3 tools/build.py trips/2028-my-trip/trip.json   # prints the requirement check
```

## The Greater Patagonian Trail manual (not included)
Some research used the *Greater Patagonian Trail Hikers Manual* by Jan Dudeck. It is **not included** in this repository (copyright and file size). If you want the GPT features (`gpt-scout`), download the current manual from the GPT project ([wikiexplora.com/Greater_Patagonian_Trail](https://www.wikiexplora.com/Greater_Patagonian_Trail)), place the PDF in the project root, and extract its text:
```bash
pdftotext -layout "GPT Hikers Manual (20251015).pdf" gpt/gpt.txt
```
The reports in `gpt-reports/` summarise and cite it; please refer to the original for the routes themselves.

## Data and attribution
- Map data, routed trails and driving lines: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL). Routing by routing.openstreetmap.de, geocoding by Nominatim.
- Tiles: OpenTopoMap (CC-BY-SA), OSM France / HOT, CyclOSM, Esri World Imagery, Waymarked Trails.
- GPT route information: Jan Dudeck, Greater Patagonian Trail.
