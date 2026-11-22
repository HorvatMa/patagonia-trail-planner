"""Shared places: airports usable as trip start/end points, and named places for driving routes.
Coordinates checked against OpenStreetMap (Nominatim), Nov 2026. Airport notes are general planning
hints, not verified rules: always confirm rental, ferry and border details for the actual dates."""

AIRPORTS = {
 "PMC": dict(name="Puerto Montt – El Tepual", country="CL", lat=-41.4436, lon=-73.0945,
             notes="Gateway to the northern Carretera Austral and Chiloé. Going south by car needs either the summer ferries Hornopirén → Leptepu and Fiordo Largo → Caleta Gonzalo (book well ahead in Jan–Feb) or a detour through Argentina (Futaleufú or Palena crossings). Large rental market."),
 "BBA": dict(name="Balmaceda (for Coyhaique)", country="CL", lat=-45.9164, lon=-71.6866,
             notes="Central Aysén: Carretera Austral north and south, Cerro Castillo 1.5 h away. Few rental agencies, so book 4x4s early; ask explicitly about the Argentina permit."),
 "PUQ": dict(name="Punta Arenas – Carlos Ibáñez del Campo", country="CL", lat=-53.0038, lon=-70.8465,
             notes="About 3 h to Puerto Natales and 4–5 h to Torres del Paine. Good rental choice. Argentina (El Calafate, El Chaltén) is reachable via the Cerro Castillo / Dorotea crossings."),
 "PNT": dict(name="Puerto Natales – Teniente Julio Gallardo", country="CL", lat=-51.6667, lon=-72.5291,
             notes="Mostly seasonal flights. Closest airport to Torres del Paine (≈1.5–2 h). Small rental market."),
 "FTE": dict(name="El Calafate – Comandante Armando Tola", country="AR", lat=-50.2808, lon=-72.0513,
             notes="For Perito Moreno Glacier and El Chaltén (≈3 h). Argentine rentals that may enter Chile need their own permit."),
 "BRC": dict(name="Bariloche – Teniente Luis Candelaria", country="AR", lat=-41.1526, lon=-71.1546,
             notes="Northern Patagonia lakes (Nahuel Huapi, refugio hikes). Paved roads; Chile via Cardenal Samoré."),
 "USH": dict(name="Ushuaia – Malvinas Argentinas", country="AR", lat=-54.8416, lon=-68.3086,
             notes="Tierra del Fuego. Reaching the mainland by car means a Strait of Magellan ferry and two border crossings (≈1 long day to Punta Arenas or Río Gallegos)."),
 "EQS": dict(name="Esquel – Brigadier General Antonio Parodi", country="AR", lat=-42.9043, lon=-71.1344,
             notes="For Los Alerces NP and the Futaleufú crossing into Chilean Aysén."),
}
# One-way rentals: dropping off a car in another country is usually impossible or very expensive,
# and even domestic one-way fees can be high. Plans with pickup != dropoff should say so.

PLACES = {
 "Balmaceda": (-45.9147,-71.6936), "Coyhaique": (-45.5712,-72.0685), "Puyuhuapi": (-44.3256,-72.5583),
 "Villa Cerro Castillo": (-46.1225,-72.1555), "Puerto Río Tranquilo": (-46.6247,-72.6747), "Puerto Guadal": (-46.8446,-72.7043),
 "PN Patagonia West Winds": (-47.1274,-72.5047), "Cochrane": (-47.2544,-72.5733), "Villa O'Higgins": (-48.4672,-72.56),
 "Caleta Tortel": (-47.7975,-73.5361), "Chile Chico": (-46.5416,-71.7238), "Puerto Ibáñez": (-46.2944,-71.9361),
 "Los Antiguos": (-46.55,-71.6278), "Paso Roballos": (-47.1577,-71.8544), "Bajo Caracoles": (-47.4442,-70.9283),
 "El Chaltén": (-49.3315,-72.8863), "El Calafate": (-50.3379,-72.2648), "Torres del Paine": (-50.9795,-72.8004),
 "Futaleufú": (-43.1854,-71.8669), "Chaitén": (-42.9167,-72.7083), "El Amarillo": (-43.0101,-72.483),
 # added for trip patagonia-new (Nominatim, bounded boxes, 2026-11-22)
 "Puerto Raúl Marín Balmaceda": (-43.7771,-72.9521), "La Junta": (-43.9721,-72.4053),
 "La Ascensión": (-46.6072,-71.4075), "Lago Posadas": (-47.5656,-71.7427),
 "PN Perito Moreno": (-47.8045,-72.0941), "Jeinimeni El Silencio": (-46.8382,-72.0120),
}

# every airport is also a place (by code)
for _c, _a in AIRPORTS.items():
    PLACES.setdefault(_c, (_a["lat"], _a["lon"]))
