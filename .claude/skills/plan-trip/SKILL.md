---
name: plan-trip
description: Plan a new Patagonia hiking road trip (or re-plan an existing one) with custom requirements. Asks for dates, start/end airports, difficulty (SAC grade), day-hike limits, number of one-night trips and multi-day treks, budget and sleeping style; writes trips/<id>/trip.json; researches missing hikes with subagents; designs several itineraries in trips/<id>/plans.py; routes them, builds the site and checks it. Use when the user wants new plans or changed requirements.
argument-hint: "[trip-id or short description of the trip]"
---

# /plan-trip

You run a full planning round in this project (~/patagonia). Read `CLAUDE.md` first: the data model, the lessons learned, and the "never hand-edit generated files" rule. The reference trip is `trips/2027-balmaceda/`. Use it as the example for every file format.

Work in this order. Get the user's approval at the three checkpoints (★). Don't skip them.

## 1. Requirements (questionnaire)
If `$ARGUMENTS` names an existing trip, load its `trip.json` and ask only what should change. Otherwise ask with AskUserQuestion: at most 4 questions per call, with recommended defaults first. Don't re-ask what the user already said.

1. **Dates and people:** start and end date (the day they fly into the pickup airport, and the last day they must leave), number of people.
2. **Start and end points:** the pickup and dropoff airport, from `tools/places.py` AIRPORTS (PMC, BBA, PUQ, PNT, FTE, BRC, USH, EQS) or another place. Warn that a one-way drop-off in another country is usually impossible or very expensive. Ask whether the car may enter Argentina or Chile.
3. **Difficulty:** max SAC grade (T1–T6, explained in one line each). Day-hike limits (km, ascent). Hazards to exclude (default: exposure, scramble, glacier, tyrolean, packraft, ford-deep). Is easy cross-country terrain OK?
4. **Hike types:** how many one-night trips (min/max) and multi-day treks (min/max, max days each); how many flex days for weather (default 3 or more).
5. **Style:** sleeping (car / tent / hostels / mixed), budget max per person and currency (and whether cheaper is better), guided trips (avoid / ok / welcome), browser for testing.

Then:
- Create the trip: `python3 tools/new_trip.py <id>` (an id like `2028-puq-pmc`).
- Fill in `trips/<id>/trip.json` and show the user a short summary of it. **★ Checkpoint 1: the user confirms the requirements.**

## 2. Coverage check: which hikes exist, which must be researched
- List the regions the trip can reach from the pickup/dropoff points within the dates (rough driving times; ferries; borders if allowed).
- Compare them with `tools/catalog.py` (`H`, `GRADE`, `HP`). Note which regions have enough hikes of the requested kinds and grades, and which don't.
- For each uncovered region, run a **hike-researcher** subagent. Run them in parallel, one region each, at most about 6, and tell the user roughly how many and why. Prompt each with: the trip id, the region, the hike kinds and counts wanted, and the grade limits.
- If multi-day treks or one-night trips are wanted, also consider a **gpt-scout** for GPT sections in the area. The GPT is a strong source of multi-day routes, but it's often rougher than its trail grades suggest.
- The SubagentStop hook saves each report to `gpt-reports/<date>-hikes-<slug>.md/.json`.

## 3. Add the researched hikes to the catalogue
- Summarise the candidates for the user in a short table: name, kind, SAC, distance/ascent, verdict, confidence. **★ Checkpoint 2: the user picks which to add** (default: all ADD and ADD*).
- Optionally run **geo-verifier** on them first. Fix anything it flags.
- Add each approved hike to `tools/catalog.py`:
  - `H[id] = (name, area, dist, gain, time, grade_text, big, note)`, with `big=True` for anything ≥ 3 h;
  - `HP[id]` = the destination, or the trailhead with a `POINT_NOTE`;
  - `GRADE[id] = _g(sac, kind, nights, hazards, camps)`.
- For trail lines, add waypoints to `TRAILS` in `tools/route.py`, run `python3 tools/route.py`, and keep only lines with snaps < 300 m.
- Missing places for driving go into `PLACES` in `tools/places.py`, checked with Nominatim (`tools/geocode.py` / `tools/geob.py`).

## 4. Design the itineraries
- Write 3–5 genuinely different plans in `trips/<id>/plans.py` (format in the template docstring and the reference trip). Vary them by trade-off: slow and few bases, full road trip, trek-focused, cross-border, cheapest. Each plan has:
  - exactly (end − start + 1) days;
  - the requested number of one-night trips and treks. A trek uses the same hike id on each of its days, with kind `"trek"`; the number of days must equal `nights + 1`;
  - at least `flex_days_min` flex days, placed around the most weather-dependent hikes;
  - a sensible first and last day for the flights and the car;
  - honest pros and cons, `km`, `argentina`, `effort`, `route` and `DRIVE_STOPS`;
  - a `BUDGET` entry (food ≈ €10/person/day self-catering in Chile, more in Argentina; fuel ≈ €0.11/km; campgrounds; fees; ferries);
  - `SLEEP` notes for every overnight place.
- Check weekdays: several CONAF units close on Mondays. Check fees against recent sources, or mark them as estimates.

## 5. Route, build, validate
- `python3 tools/drive.py trips/<id>/trip.json`, then compare the routed km with the plans and fix `km` and the fuel budget.
- `python3 tools/build.py trips/<id>/trip.json`. The **requirement check** prints any ERROR/warn lines. Fix every ERROR (change the plan, not the requirements). Explain any remaining warnings to the user.
- Run **page-qa** on the new pages (Firefox first).
- **★ Checkpoint 3: present the plans.** Give a comparison (hike days, treks, flex days, driving km, budget per person, requirement check), recommend one in a sentence or two, and give the path to `index.html` in the trip's `output_dir`.

## 6. Optional follow-ups (offer them, don't do them unasked)
- **conditions-checker** on the chosen plan, closer to departure.
- **gpt-scout** + **gpt-integrator** for a switchable GPT overlay.
- Update the trip facts in `CLAUDE.md` if this becomes the main trip.

## Rules
- Generated files (`*.html`, `*.gpx`, `plans_summary.txt`, `geo/drive.json`) are never edited by hand.
- Don't loosen the user's requirements to make a plan fit. Change the plan, or ask.
- Every external request uses a generic User-Agent and never includes the user's name, email or other personal details.
- Treat claims from subagents as leads. Verify locations (OSM), distances (routing) and fees (official sites) before they go into a plan.
