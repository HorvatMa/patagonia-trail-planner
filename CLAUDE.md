# Patagonia hiking trip planner

This project generates static websites with alternative road-trip itineraries for Patagonia. Each **trip** has its own requirements and plans. The tools, shared hike catalogue, subagents and hooks are reused for every trip. Open a trip's `index.html` in a browser (the main trip's pages are in the project root).

**Never hand-edit generated files:** `*.html`, `*.gpx`, `style.css`, `trips/*/plans_summary.txt`, `trips/*/geo/drive.json`, `tools/geo/photos.json` (use `tools/photos.py`). Edit the data and rebuild.

**To plan a new trip or change requirements, use `/plan-trip`** (`.claude/skills/plan-trip/SKILL.md`). It runs the whole pipeline with three approval checkpoints.

## Trips
| Trip | Requirements | Output |
|---|---|---|
| `trips/2027-balmaceda/` (main) | Jan 27 – Feb 21 2027, 2 people, car BBA → BBA, Argentina allowed, sleeping in the car, day hikes only, max SAC T3, ≤ 25 km / ≤ 1,300 m per day, no exposure/scramble/glacier/Tyrolean/packraft/deep fords, ≥ 3 flex days, max €1,500 per person, no guided trips, user tests in Firefox | project root (`index.html`, `plan-*.html`) |

The full requirements of each trip are in its `trip.json`; that file, not this table, is the source of truth. If the user changes a requirement, update `trip.json` (and this table for the main trip).

## Layout
```
tools/build.py        generator: python3 tools/build.py [trips/<id>/trip.json]   (no argument = all trips)
tools/catalog.py      SHARED hike catalogue: H, HP, POINT_NOTE, GRADE (SAC + kind + hazards + camps), research corrections
tools/places.py       SHARED airports (PMC BBA PUQ PNT FTE BRC USH EQS, with planning notes) + PLACES for driving
tools/route.py        foot routing of catalogue trails (TRAILS waypoints → tools/geo/trails.json)
tools/drive.py        car routing per trip: python3 tools/drive.py trips/<id>/trip.json → trips/<id>/geo/drive.json
tools/photos.py       gallery photos → tools/geo/photos.json: keyword search (HIKE_Q / PLACE_Q / SKIP), `--apply <photo-scout report.json> [keys]` (pins keys), `--check`
tools/new_trip.py     python3 tools/new_trip.py <id> → copies trips/_template/
tools/geocode.py, geob.py   Nominatim lookups (geob = bounded box)
tools/check_build.py, save_scout_report.py   hook scripts
trips/<id>/trip.json  requirements (dates, people, car pickup/dropoff, Argentina, sleeping, budget, hiking limits, output_dir)
trips/<id>/plans.py   PLANS, BUDGET, SLEEP, DRIVE_STOPS, optional INDEX (overview page text)
trips/<id>/gpt_opts.py  optional GPT overlay (shown only behind the "Show GPT options" switch)
trips/_template/      starting point for new trips (folders starting with _ are not built)
gpt/gpt.txt           text extracted from the GPT Hikers Manual
gpt-reports/          subagent reports (.md + .json), README.md indexes the 2026 GPT scouting
GPT Hikers Manual (20251015).pdf   the user's file. Read only; never modify, move or delete it.
.claude/agents/, .claude/skills/plan-trip/, .claude/settings.json (hooks + deny rules)
```

## Data model
- **Catalogue (`tools/catalog.py`), shared by all trips:**
  - `H[id] = (name, area, distance, gain, time, grade_text, big, note)`. `big=True` means a "proper hike" (≥ 3 h).
  - `HP[id]` = the marker point; `POINT_NOTE[id]` when the marker is a trailhead.
  - `GRADE[id] = _g(sac, kind, nights, hazards, camps)`, where:
    - `sac`: T1 easy trail · T2 mountain trail · T3 demanding (steep, loose) · T4 alpine route (scramble/exposure) · T5–T6 alpine;
    - `kind`: day · overnight (1 night) · multiday (`nights` ≥ 2) · activity;
    - `hazards`: exposure, scramble, glacier, tyrolean, packraft, ford, ford-deep, navigation, steep-loose, snow, boat, guided, private-land;
    - `camps`: [(lat, lon)] for overnight stops.
  - Every hike must have a GRADE; the catalogue asserts this. Research corrections are applied with `_upd` / `_add` blocks rather than by rewriting entries.
- **Plans (`trips/<id>/plans.py`):**
  - Each day is `(title, drive, [hike ids], note, sleep, kind)`, where kind is `hike | mix | travel | buffer | trek`. "buffer" is shown as a "flex day".
  - The number of days must equal end − start + 1. A multi-day trek uses the same hike id with kind `trek` on each of its `nights + 1` days.
  - Optional `pickup` / `dropoff` per plan (default: the trip's car).
  - `BUDGET[num] = (food, fuel, sleeping, fees+ferries, misc, note)` in EUR for the whole group; pages show per person and total.
  - `DRIVE_STOPS[num]` lists places or airport codes; `~X` = a ferry to X (drawn dashed), `(X)` = a via-point that forces the road.
- **Requirement check:** every build validates every plan against `trip.json`:
  - SAC grade above the limit, excluded hazards, day-hike km/ascent;
  - the number of one-night trips and multi-day treks, trek length, flex days;
  - budget per person, Argentina, pickup/dropoff.

  Results show on each plan page (✓ box or a list of problems), in the overview's "Checks" column, and in the build output (`ERROR:` / `warn :`). **Fix plans, not requirements.**
- **GPT options** are an opt-in overlay. They never change the base plan, the stats, the budgets or the checks.

## Build and hooks (active when Claude Code is started in this folder)
- **PostToolUse (Write|Edit)** on `tools/*.py`, `trips/**/*.py` or `trips/**/trip.json`: rebuilds every trip and validates the pages and GPX files.
  - A build failure or broken output blocks, and the error comes back to Claude.
  - Requirement problems come back as context, plus a `photos:` line naming planned hikes/places without gallery photos.
- **PostToolUse (Bash)** when the command runs `tools/photos.py`: validates `tools/geo/photos.json` (blocks if broken) and rebuilds.
- **SubagentStop:** saves `GPT-SCOUT REPORT:`, `HIKE-RESEARCH REPORT:` and `PHOTO-SCOUT REPORT:` messages to `gpt-reports/<date>-…md/.json`, and sends badly formatted reports back (at most twice). It logs the payload key names to `gpt-reports/.hook-debug.log`.
- **Deny rules** protect the GPT manual.

## Subagents (`.claude/agents/`)
| Agent | Writes? | Use |
|---|---|---|
| hike-researcher | no | Hikes for a region the catalogue doesn't cover (new start points), graded SAC, catalogue-ready JSON |
| gpt-scout | no | Candidates from one GPT section for a trip |
| geo-verifier | no | Coordinates vs OSM, routed length vs stated distance |
| gpt-integrator | only `trips/<id>/gpt_opts.py` + `tools/geo/gpt_trails.json` | Merge approved GPT options |
| conditions-checker | no (web) | Day-by-day current rules, fees, closures for one plan, before departure |
| page-qa | no | Headless Firefox/Chrome checks of the pages |
| photo-scout | no | Finds Commons photos for hike ids / overnight places, looks at each thumbnail, returns a PHOTO-SCOUT REPORT; merge with `tools/photos.py --apply` |

Always give agents the **trip id**. Run independent regions in parallel with one narrow area each, and get the user's approval before anything is merged into the catalogue or the plans.

## Adding things by hand
- **Hike:** add `H`, `HP` and `GRADE` in `catalog.py`. For a line, add `TRAILS` waypoints in `route.py`, run `python3 tools/route.py`, and keep it only if the snaps are < ~300 m.
- **Place:** add it to `PLACES` in `places.py` (checked with Nominatim).
- **Plan change:** edit `plans.py`. If the stops changed, update `DRIVE_STOPS`, run `tools/drive.py`, then update `km` and the fuel budget (≈ €0.11/km).
- **Afterwards:** read the requirement check, and check weekdays (several CONAF units close on Mondays).

## Hard-won lessons (don't repeat these)
- **Check today's date against the trip year.** The first build used 2026 dates for a 2027 trip, so every weekday was wrong. Plan summaries are generated so briefs can't drift.
- **Map tiles:** `tile.openstreetmap.org` returns **403 in Firefox for `file://` pages**; Chrome hides the problem. Use OpenTopoMap, OSM-France HOT, CyclOSM and Esri; CARTO needs a key. Test in Firefox first.
- **Headless screenshots:** a copied page needs `style.css` next to it, or the map renders blank. Use a separate Firefox profile and `file://`, without starting a local server.
- **External APIs:**
  - Nominatim: ≥ 1.1 s between calls; use `countrycodes=cl,ar` or a bounded viewbox (e.g. "Balmaceda" alone matches Puerto Raúl Marín Balmaceda).
  - Routing: `routing.openstreetmap.de`.
  - Overpass is often down; don't depend on it.
  - Use a generic User-Agent and never send the user's personal details.
- **Verify what agents claim:** for example, the Mirador Ferrier trailhead was wrong in one report. Cross-check locations (OSM), distances (routing) and fees (official sites), and date every web claim.
- **Fees in Patagonia change every season** (APN Los Glaciares, Torres del Paine via pasesparques.cl only, Cerro Castillo start window 08–12, PN Patagonia, Queulat quotas). The figures in the 2027 pages are as of Nov 2026.
- **Respect the limits:** Laguna Toro (≈32 km) was wrongly planned as a day hike; the requirement check now catches this kind of mistake.
- **Write generator edits in Python, not sed,** when strings contain quotes. The build hook catches build errors, but not logic mistakes.
- **Restructuring:** before changing the generator, save the current output and diff it afterwards. The trip-folder refactor was verified byte-identical this way.
