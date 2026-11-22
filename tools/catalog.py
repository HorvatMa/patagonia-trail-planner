"""Shared hike catalogue: every hike any trip can use.
H[id] = (name, area, distance, gain, time, grade_text, big, note); HP[id] = marker (lat, lon).
GRADE[id] = SAC grade, kind and hazard tags (see bottom). Corrections from research are applied via _upd/_add."""

# ---------------------------------------------------------------- hikes
# id: (name, area, distance, gain, time, grade, big, note)
H = {
 "coy": ("Reserva Nacional Coyhaique loop: Laguna Venus, Laguna Verde, Cerro Cinchao viewpoint", "Coyhaique", "≈10 km", "≈500 m", "4–5 h", "Easy–Moderate", True,
         "Right on the edge of town. A good first-day hike for jet-lagged legs, with views over Coyhaique and the Simpson valley."),
 "simpson": ("Reserva Nacional Río Simpson: Cascada La Virgen and short trails", "Coyhaique–north", "≈3 km", "≈150 m", "1–1.5 h", "Easy", False,
         "A stop by the road on the way north or on a spare afternoon."),
 "castillo": ("Laguna Cerro Castillo (day hike from Villa Cerro Castillo)", "PN Cerro Castillo", "≈16–20 km return", "≈1,100 m", "7–9 h", "Strenuous, non-technical", True,
         "The best day hike in Aysén. A steep forest climb, then moraine up to a turquoise lake under the castle-like spires. You register at the trailhead, pay a private-land access fee, and there is a latest start time. Go only as far as the lake and the moraine viewpoint. Do NOT continue onto the multi-day traverse's high pass (Portezuelo), which is the exposed and weather-dangerous part. Turn back if the wind on the upper moraine is extreme."),
 "paredon": ("Paredón de las Manos rock art", "Villa Cerro Castillo", "≈1 km", "–", "45 min", "Easy", False,
         "An ancient hand-stencil site just outside the village."),
 "ibanez": ("Salto del Río Ibáñez and Puerto Ibáñez", "Cerro Castillo area", "≈2 km", "–", "1–2 h", "Easy", False,
         "An easy rest-day outing: a powerful waterfall, plus the pottery village next to the ferry pier."),
 "marble": ("Capillas de Mármol (Marble Caves) by boat or kayak", "Puerto Río Tranquilo", "boat ≈2 h", "–", "2 h", "Easy", False,
         "OPTIONAL, but one of the two paid extras I would keep: the caves can only be seen from the water (about €20–25 per person for a shared boat). Go early in the morning while the lake is calm."),
 "explor_mirador": ("Mirador Glaciar Exploradores", "Valle Exploradores", "≈3 km return", "≈200 m", "1.5–2 h", "Easy–Moderate", False,
         "At about km 52 of the Exploradores valley road, which is gravel and takes about 1.5 h each way. It is a private trail with an entry fee, and you walk it on your own. The drive up the valley is a highlight in itself."),
 "explor_ice": ("Glaciar Exploradores guided ice trek (optional)", "Valle Exploradores", "full day", "≈300 m", "7–8 h", "Moderate, guided", False,
         "Not alpine climbing: a guided walk on the glacier surface with crampons and helmet. Skip it if you want to stay off ice entirely."),
 "confluencia": ("Confluencia Baker–Neff and Cascada Río Baker", "Puerto Bertrand", "≈2 km", "≈50 m", "1 h", "Easy", False,
         "Two short walks near the road. The colour of the Baker river is unreal."),
 "lagunas_altas": ("Lagunas Altas loop", "PN Patagonia (Valle Chacabuco)", "≈23 km loop", "≈900 m", "7–9 h", "Strenuous, non-technical", True,
         "Lakes on a high ridge, with views as far as Cerro San Lorenzo on clear days. Starts at the West Winds campground. Windy on top but no technical sections."),
 "aviles": ("Valle Aviles loop", "PN Patagonia (Valle Chacabuco)", "≈16 km loop", "≈500 m", "5–6 h", "Moderate", True,
         "Goes from steppe into forest, along a river with a suspension bridge. Guanacos almost guaranteed; huemul possible."),
 "tamango": ("Sector Tamango: Los Huemules / Lago Cochrane trails", "Cochrane", "8–16 km", "300–700 m", "3–6 h", "Easy–Moderate", True,
         "Pick your own length. One of the best chances anywhere to see the endangered huemul deer. Pay the fee at the CONAF ranger station."),
 "tortel": ("Caleta Tortel boardwalks and Cerro Vigía", "Caleta Tortel", "≈5 km", "≈150 m", "2–3 h", "Easy", False,
         "A car-free village built on cypress boardwalks."),
 "voh": ("Villa O'Higgins: Cerro Santiago trails and viewpoint", "Villa O'Higgins", "≈6–10 km", "≈400–600 m", "3–5 h", "Moderate", True,
         "Starts from the edge of town."),
 "banderas": ("Cerro de las Banderas viewpoint", "Chile Chico", "≈1 km", "≈80 m", "30 min", "Easy", False,
         "A sunset viewpoint over Lago General Carrera."),
 "piedra": ("Piedra Clavada, Cueva de las Manos, Valle Lunar", "PN Patagonia (Jeinimeni sector)", "≈10 km", "≈300 m", "4–5 h", "Easy–Moderate", True,
         "Desert badlands, a 40 m rock spire and rock art, totally unlike the rest of Aysén. Sun, wind and no shade, so carry plenty of water."),
 "jeinimeni": ("Lago Jeinimeni: Sendero Lago Verde", "PN Patagonia (Jeinimeni sector)", "≈10 km return", "≈250 m", "3–4 h", "Easy–Moderate", True,
         "Road X-753 has river fords. Drive it only with a high-clearance 4x4 and only when the rivers are low. Ask CONAF or locals in Chile Chico before going."),
 "queulat_colgante": ("Ventisquero Colgante viewpoint and Laguna Témpanos", "PN Queulat", "≈7 km return", "≈300 m", "3 h", "Moderate", True,
         "A hanging glacier spilling a waterfall over a cliff. This is very wet rainforest, so bring waterproofs even on sunny days."),
 "bosque": ("Sendero Bosque Encantado", "PN Queulat", "≈5 km return", "≈300 m", "2.5–3 h", "Moderate", True,
         "A muddy, rooty, magical forest leading to a glacial lagoon. It has been closed at times, so check with CONAF."),
 "chaiten": ("Volcán Chaitén crater rim", "PN Pumalín", "≈4.5 km return", "≈600 m", "3 h", "Moderate–Strenuous (short)", True,
         "Climb the volcano that erupted in 2008: a steaming dome, dead forest and huge views."),
 "tronador": ("Laguna Tronador", "PN Pumalín", "≈3 km return", "≈250 m", "2 h", "Moderate", False,
         "Wooden ladders and boardwalks through rainforest to a lake beneath Michinmahuida."),
 "alerces": ("Los Alerces and Cascadas Escondidas", "PN Pumalín (Caleta Gonzalo)", "≈5 km total", "≈200 m", "2.5 h", "Easy", False,
         "Alerce trees up to 3,000 years old and a chain of hidden waterfalls."),
 "amarillo": ("Ventisquero Amarillo", "PN Pumalín (El Amarillo)", "≈10 km return", "≈200 m", "4 h", "Easy–Moderate", True,
         "A mostly flat walk up a glacial riverbed to the snout of the Michinmahuida glacier."),
 "yelcho": ("Sendero Ventisquero Yelcho", "Lago Yelcho", "≈9 km return", "≈350 m", "4 h", "Moderate", True,
         "A forest trail to the glacier lagoon above Lago Yelcho. Fits well into the drive from Futaleufú to Chaitén."),
 "futa": ("Piedra del Águila and Reserva Nacional Futaleufú trails", "Futaleufú", "≈6–10 km", "300–500 m", "3–5 h", "Moderate", True,
         "Viewpoint hikes above the turquoise Futaleufú river."),
 "toro": ("Laguna Toro", "El Chaltén (AR)", "≈30 km return", "≈700 m", "9–10 h", "Long, non-technical", True,
         "The quietest of the big Chaltén hikes: a long valley-and-moraine walk to a glacier lake. Turn around at the lake; the route beyond it (Paso del Viento) is glacier terrain."),
 "torre": ("Laguna Torre", "El Chaltén (AR)", "≈19 km return", "≈350 m", "6–7 h", "Moderate", True,
         "A gentle valley walk from town to the lake below Cerro Torre."),
 "tres": ("Laguna de los Tres (Fitz Roy)", "El Chaltén (AR)", "≈22 km return", "≈1,000 m", "8–10 h", "Strenuous, non-technical", True,
         "THE Fitz Roy view. Strong hikers can add Laguna Sucia (a short detour, about +1 h). The last ≈1 km climbs about 400 m on a steep, loose path, but it is non-technical. If the wind is extreme, stop at Poincenot / Río Blanco. Come back down via Laguna Capri."),
 "pliegue": ("Loma del Pliegue Tumbado", "El Chaltén (AR)", "≈20 km return", "≈1,100 m", "7–8 h", "Strenuous, non-technical", True,
         "A panoramic viewpoint facing both Cerro Torre and Fitz Roy. Exposed to wind, so pick a calm day."),
 "capri": ("Laguna Capri plus Mirador de los Cóndores / Las Águilas", "El Chaltén (AR)", "≈10 km", "≈400 m", "3–4 h", "Easy–Moderate", False,
         "Shorter options for days when the weather is poor."),
 "desierto": ("Lago del Desierto / Glaciar Huemul and Chorrillo del Salto", "El Chaltén (AR)", "≈3–5 km", "≈350 m", "2–3 h + 37 km drive", "Moderate", False,
         "A drive north of Chaltén with a waterfall stop on the way. The Huemul trail crosses private land and charges a fee."),
 "pmoreno": ("Glaciar Perito Moreno walkways", "El Calafate (AR)", "≈4 km of balconies", "–", "3–4 h", "Easy", False,
         "Not a hike, but not to be missed. You walk the free-standing balconies yourself; the guided ice walks are not needed."),
 "cuevamanos": ("Cueva de las Manos (UNESCO)", "Río Pinturas (AR)", "≈2 km guided", "–", "1.5–2 h", "Easy", False,
         "OPTIONAL, the other paid extra worth it: hand stencils about 9,000 years old in a beautiful canyon. A guide is required, but the visit is short and cheap. It is a detour of about 90 km."),
 "base_torres": ("Base Las Torres", "Torres del Paine", "≈20 km return", "≈900 m", "8–10 h", "Strenuous, non-technical", True,
         "The famous towers. The last hour is a steep boulder moraine with no technical sections. Buy park tickets online in advance (they are not sold at the gate) and check the current booking rules for this trail."),
 "cuernos": ("Salto Grande and Mirador Cuernos", "Torres del Paine", "≈11 km return", "≈150 m", "3–4 h", "Easy", True,
         "Flat and very windy, with superb views of the Cuernos del Paine."),
 "grey": ("Lago Grey / Mirador Glaciar Grey, plus Laguna Azul or Mirador Cóndor", "Torres del Paine", "≈4–10 km", "100–300 m", "2–4 h", "Easy–Moderate", False,
         "Shorter hikes to combine as you like. Good for windy days."),
}

# ---------------------------------------------------------------- corrections from the Nov 2026 research (GPT scouting agents)
def _upd(h, **kw):
    n, area, dist, gain, t, grade, big, note = H[h]
    d = dict(n=n, area=area, dist=dist, gain=gain, t=t, grade=grade, big=big, note=note); d.update(kw)
    H[h] = (d["n"], d["area"], d["dist"], d["gain"], d["t"], d["grade"], d["big"], d["note"])
def _add(h, extra): _upd(h, note=H[h][7] + " " + extra)

_upd("amarillo", dist="≈20 km return", gain="≈500 m", t="6 h", grade="Moderate",
     note="A long walk up the glacial valley of the Río Amarillo to the snout of the Michinmahuida glacier. The last ≈3 km are boggy. Start in the morning: last trail entry in Pumalín is around 14:00. The Termas El Amarillo were closed for construction in 2025, so check before planning a soak.")
_upd("jeinimeni", n="Lago Jeinimeni: Costanera trail + Laguna Esmeralda", dist="≈12–16 km", gain="≈300 m", t="4–6 h",
     note="CONAF's trails at Lago Jeinimeni: Costanera Lago Jeinimeni (11.4 km), Laguna Esmeralda (5.8 km), the short Mirador and Escorial El Silencio. Combine them into a 12–16 km day. Open daily 09:00–18:00 in summer. The road X-753 has river fords near the lake. Drive it only with high clearance and when the rivers are low, and ask CONAF Jeinimeni or locals in Chile Chico the day before. Rental insurance usually excludes water damage.")
_upd("grey", n="Lago Grey beach and peninsula walk, plus Laguna Azul or Mirador Cóndor",
     note="Walk from the Lago Grey car park over the suspension bridge to the beach and peninsula, with icebergs and the distant Glaciar Grey (latest entry 16:00). The 'Mirador Glaciar Grey' beyond Refugio Grey can't be reached as a day hike. Combine it with Laguna Azul or Mirador Cóndor.")
_add("castillo", "Rules (2025/26): start between 08:00 and 12:00, or you are turned away. Ticket ≈21,000 CLP per person for foreigners, card only or online (senderospncc.cl / pasesparques.cl). Buy ahead because peak days sell out. Register via QR code at the ranger station. The last ≈1.5 km to the lake closes at short notice in bad weather.")
_add("base_torres", "Rules (2025/26): enter at Laguna Amarga by 10:00 (Dec–Feb) and leave the viewpoint by 16:00. No guide or extra booking is needed, only the park ticket. That ticket is sold ONLY online (pasesparques.cl) and there is no internet at the gate, so screenshot it.")
_add("queulat_colgante", "Buy tickets in advance on pasesparques.cl; daily places are limited.")
_add("coy", "Closed on Mondays; open 09:00–16:30 with last entry 14:00. Book on pasesparques.cl (no refunds).")
for _h in ("chaiten", "tronador", "alerces"): _add(_h, "Pumalín is free to enter; last trail entry is around 14:00.")
_add("piedra", "CONAF listed this circuit as 'closed' in Nov 2026, probably because the season hadn't started yet. Confirm before you go.")
_add("tamango", "Check the opening days: some CONAF units are closed on Mondays.")
_add("torre", "Scientists are monitoring a slope on Cerro Solo that is slowly sliding toward Lago Torre (2026). The trail is open, but ask at the park visitor centre for the current status.")
_add("pmoreno", "Entry ≈50,000 ARS per person per day (2026 rates); the Flexipass also covers El Chaltén.")
for _h in ("torre", "tres", "pliegue", "capri"): _add(_h, "Park entry is charged (≈50,000 ARS per person per day, or the 7-day Flexipass ≈175,500 ARS). Pay by card or online only (ventaweb.apn.gob.ar).")
_upd("toro", note="NOT a day hike within your limits: ≈32 km return on an unmarked, cairned route. It works as an OPTIONAL ONE-NIGHT trip, with free camping at the lake after you register with the park. Turn around at the lake. A fire near Cerro Huemul closed the area in Jan 2026, so ask the park office about the current status.")


# marker position for every hike (the destination / main point)
HP = {
 "coy": (-45.5365,-72.0165), "simpson": (-45.458,-72.3727), "castillo": (-46.0763,-72.1914), "paredon": (-46.1443,-72.1579),
 "ibanez": (-46.2578,-71.9949), "marble": (-46.6504,-72.615), "explor_mirador": (-46.5004,-73.1563), "confluencia": (-47.1208,-72.7754),
 "lagunas_altas": (-47.128,-72.4714), "aviles": (-47.1274,-72.5047), "tamango": (-47.2229,-72.5266), "tortel": (-47.7943,-73.5371),
 "voh": (-48.4661,-72.5477), "banderas": (-46.5367,-71.734), "piedra": (-46.7318,-71.7816), "jeinimeni": (-46.8502,-72.1061),
 "queulat_colgante": (-44.4608,-72.5391), "bosque": (-44.6257,-72.4522), "chaiten": (-42.8368,-72.6475), "tronador": (-42.6578,-72.595),
 "alerces": (-42.6788,-72.5828), "amarillo": (-42.9444,-72.4759), "yelcho": (-43.2787,-72.4396), "futa": (-43.1582,-71.8917),
 "torre": (-49.3232,-73.0024), "tres": (-49.2784,-72.9895), "pliegue": (-49.3594,-72.9675), "toro": (-49.386,-73.0508),
 "capri": (-49.3049,-72.9357), "desierto": (-49.0722,-72.9044), "pmoreno": (-50.469,-73.0299), "cuevamanos": (-47.1553,-70.656),
 "base_torres": (-50.9427,-72.9497), "cuernos": (-51.0483,-73.0123), "grey": (-51.0458,-73.1697),
}
POINT_NOTE = {"aviles": "Marker = trailhead at West Winds; the loop heads north into Valle Aviles.",
              "amarillo": "Marker = trailhead (Camping Ventisquero); the trail continues up to the glacier.",
              "yelcho": "Marker = trail start; the trail climbs to the glacier lagoon.",
              "explor_mirador": "Marker = viewpoint, at about km 52 of the Exploradores valley road."}


# ---------------------------------------------------------------- difficulty (SAC hiking scale T1–T6) and hazards
# sac:     T1 easy trail · T2 mountain trail · T3 demanding mountain trail (steep, loose, some hands for balance)
#          T4 alpine route (scrambling, exposure) · T5 demanding alpine · T6 difficult alpine
# kind:    day | overnight (1 night, back to the car) | multiday (trek of `nights` nights) | activity (boat, sight, walkway)
# hazards: exposure, scramble, glacier, tyrolean, packraft, ford, ford-deep (above knee), navigation (unmarked / GPS needed),
#          steep-loose, snow, boat, guided, private-land
# camps:   [(lat, lon), …] overnight spots for overnight/multiday hikes (drawn on the map)
# Grades below are planning estimates (Nov 2026) based on the descriptions, not official ratings.
def _g(sac, kind="day", nights=0, hazards=(), camps=()):
    return dict(sac=sac, kind=kind, nights=nights, hazards=list(hazards), camps=list(camps))

GRADE = {
 "coy": _g("T2"), "simpson": _g("T1"), "castillo": _g("T3", hazards=["steep-loose"]), "paredon": _g("T1", "activity"),
 "ibanez": _g("T1"), "marble": _g("T1", "activity", hazards=["boat"]), "explor_mirador": _g("T2", hazards=["private-land"]),
 "explor_ice": _g("T3", hazards=["glacier", "guided"]), "confluencia": _g("T1"), "lagunas_altas": _g("T2"),
 "aviles": _g("T2"), "tamango": _g("T2"), "tortel": _g("T1"), "voh": _g("T2"), "banderas": _g("T1"),
 "piedra": _g("T2"), "jeinimeni": _g("T2"), "queulat_colgante": _g("T2"), "bosque": _g("T2"), "chaiten": _g("T2"),
 "tronador": _g("T2"), "alerces": _g("T1"), "amarillo": _g("T2"), "yelcho": _g("T2"), "futa": _g("T2"),
 "toro": _g("T3", "overnight", 1, ["navigation"], [(-49.3852, -73.0405)]),
 "torre": _g("T2"), "tres": _g("T3", hazards=["steep-loose"]), "pliegue": _g("T2"), "capri": _g("T1"),
 "desierto": _g("T2", hazards=["private-land"]), "pmoreno": _g("T1", "activity"), "cuevamanos": _g("T1", "activity", hazards=["guided"]),
 "base_torres": _g("T3", hazards=["steep-loose"]), "cuernos": _g("T1"), "grey": _g("T1"),
}
_missing = set(H) - set(GRADE)
assert not _missing, f"hikes without GRADE: {_missing}"
