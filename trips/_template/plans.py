"""Plans for this trip. Read by tools/build.py together with trip.json.

PLANS: list of dicts, one per itinerary:
  dict(slug="plan-1-short-name", num=1, name="Short Name", tag="One-sentence summary.",
       who="Who this plan suits.", km="≈2,000", argentina=False, effort="Moderate",
       pickup="BBA", dropoff="BBA",            # optional; default = trip.json car
       route=["Balmaceda", "Place A", ...],    # names for the Google Maps link
       days=[...], pros=[...], cons=[...])
  days: exactly (end_date - start_date + 1) tuples:
       (title, drive, [hike ids from tools/catalog.py], note, sleep, kind)
       kind = hike | mix | travel | buffer | trek
       A multi-day trek uses the same hike id on each of its days with kind "trek"
       (GRADE kind "multiday", nights = days - 1). A one-night trip uses GRADE kind "overnight".
BUDGET[num] = (food, fuel, sleeping, fees+ferries, misc, "note") in EUR for the WHOLE group.
SLEEP[sleep name] = advice for sleeping at that place (shown on the plan page).
DRIVE_STOPS[num] = ["BBA", "Coyhaique", "~Chile Chico", "(Puerto Guadal)", ...] for tools/drive.py:
       names or airport codes from tools/places.py; "~X" = ferry to X; "(X)" = via-point only.
INDEX (optional): dict(title, desc, html) with {CARDS} and {ROWS} placeholders; omit it to use the generic overview.
"""
PLANS = []
BUDGET = {}
SLEEP = {}
DRIVE_STOPS = {}
