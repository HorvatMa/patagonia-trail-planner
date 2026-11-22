# Brief: GPT feasibility scouting for a Patagonia day-hiking trip

## The trip
- Two fit adults, Jan 27 – Feb 21 2027, rental 4x4 picked up and returned at Balmaceda (Chile), sleeping in the car.
- They want as many hikes as possible, mostly **day hikes**, can hike back-to-back days.
- Budget-conscious (max €1,500 per person on the ground, cheaper is better). They do NOT want guided trips.
- Safety rule: **no alpine/dangerous terrain**.
- Their current 5 itineraries (day by day) are in `plans_summary.txt` (same folder). Flex days ("buffer") can be replaced; other days can be swapped if a GPT option is clearly better.

## Source material
- **Greater Patagonian Trail (GPT) Hikers Manual**, Oct 2025, by Jan Dudeck.
  - Extracted text (layout preserved, 25k lines): `gpt.txt` (same folder). Page footers read like `Page 417 of 1345`.
  - Original PDF (for maps/elevation profiles where the text is unclear): `GPT Hikers Manual (20251015).pdf` in the project root — read only the specific pages you need (Read tool with `pages`, ≤20 pages per call). Do NOT modify or move it.
  - Useful places in `gpt.txt`: section commentary ≈ lines 9590–10010; per-section detail pages start ≈ line 14280 (e.g. `GPT32: Cerro Castillo` at 14628); general "dangers/right-of-way" notes ≈ lines 2900–3100. Grep for your section numbers (e.g. `GPT35`, `{35}`, `Option`) to find everything, including options/variants.
- You MAY use web search/fetch to check **current** conditions (2024–2026): closures, fees, permits, bridges out, access disputes, trail reports (Wikiloc, park sites, CONAF, APN, iOverlander, Andeshandbook, wikiexplora, recent blogs). Note the date of each source.
- Do not write or modify any files except your own notes in the scratchpad if needed. Do not publish anything.

## What to find
Stretches of the GPT (regular route, options, variants) in YOUR assigned area that could be walked by this couple as:
1. **Day hike** (preferred): start and end at a point reachable by their car (out-and-back or loop; a short car shuttle is NOT possible — one car).
2. **Optional one-night trip** (secondary): carry a tent for one night, return to the car next day. Only if clearly worth it.

### Hard limits (reject if violated)
- Day hike ≤ ~25 km and ≤ ~1,300 m total ascent.
- No scrambling, no exposed ridges/passes, no glacier travel, no Tyrolean traverses, no packrafting, no fords deeper than knee height (in normal Jan–Feb conditions).
- Easy open cross-country terrain (steppe, open valleys, gentle slopes) IS acceptable; dense bush-bashing or route-finding through tough terrain is not.
- Must not require permits that day hikers can't get, or trespass where the manual or recent reports say landowners object.

## Report format (your final message — be concise, no preamble)
For each candidate (best first, max ~6):
```
### <Name>  — verdict: ADD | MAYBE | NO
- GPT ref: GPTxx regular route / Option n (km a→b of section), manual page(s)
- Car access point: <place>, approx lat/lon if known; road type / 4x4 needed?
- Hike: out-and-back | loop | 1-night; distance ≈ km, ascent ≈ m, time ≈ h
- Terrain: trail / cross-country; fords; exposure; snow risk; navigation difficulty
- Fees / private land / permits:
- Current status (web, with dates):
- Why it's worth it (vs. what's already in the plans):
- Fits: Plan n, <date/day> (replace flex day | replace <hike> | add as option); extra driving
- Confidence: high | medium | low  (+ what's uncertain)
```
Then one short paragraph: anything in your area the couple should know even if not added (e.g. hazards, closures, fee changes affecting existing hikes in the plans), and anything in the existing plans for your area that the manual or web suggests is wrong.

If nothing qualifies, say so plainly — "no good candidates" is a valid, useful answer. Do not inflate.
