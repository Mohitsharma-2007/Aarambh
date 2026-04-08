"""Geocoding service - maps country/city names to lat/lng coordinates (no external API)"""

# Major world capitals and cities with coordinates
CITY_COORDS = {
    "new delhi": (28.6139, 77.2090), "delhi": (28.6139, 77.2090), "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946), "kolkata": (22.5726, 88.3639), "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867), "washington": (38.9072, -77.0369), "washington dc": (38.9072, -77.0369),
    "new york": (40.7128, -74.0060), "los angeles": (34.0522, -118.2437), "chicago": (41.8781, -87.6298),
    "london": (51.5074, -0.1278), "paris": (48.8566, 2.3522), "berlin": (52.5200, 13.4050),
    "moscow": (55.7558, 37.6173), "beijing": (39.9042, 116.4074), "shanghai": (31.2304, 121.4737),
    "tokyo": (35.6762, 139.6503), "seoul": (37.5665, 126.9780), "sydney": (-33.8688, 151.2093),
    "dubai": (25.2048, 55.2708), "istanbul": (41.0082, 28.9784), "cairo": (30.0444, 31.2357),
    "riyadh": (24.7136, 46.6753), "tehran": (35.6892, 51.3890), "islamabad": (33.6844, 73.0479),
    "kabul": (34.5553, 69.2075), "baghdad": (33.3152, 44.3661), "jerusalem": (31.7683, 35.2137),
    "tel aviv": (32.0853, 34.7818), "ankara": (39.9334, 32.8597), "rome": (41.9028, 12.4964),
    "madrid": (40.4168, -3.7038), "brussels": (50.8503, 4.3517), "amsterdam": (52.3676, 4.9041),
    "zurich": (47.3769, 8.5417), "geneva": (46.2044, 6.1432), "vienna": (48.2082, 16.3738),
    "warsaw": (52.2297, 21.0122), "kyiv": (50.4501, 30.5234), "kiev": (50.4501, 30.5234),
    "minsk": (53.9045, 27.5615), "taipei": (25.0330, 121.5654), "hong kong": (22.3193, 114.1694),
    "singapore": (1.3521, 103.8198), "kuala lumpur": (3.1390, 101.6869), "jakarta": (6.2088, 106.8456),
    "bangkok": (13.7563, 100.5018), "hanoi": (21.0278, 105.8342), "manila": (14.5995, 120.9842),
    "nairobi": (-1.2921, 36.8219), "lagos": (6.5244, 3.3792), "johannesburg": (-26.2041, 28.0473),
    "cape town": (-33.9249, 18.4241), "addis ababa": (9.0250, 38.7469), "accra": (5.6037, -0.1870),
    "brasilia": (-15.7975, -47.8919), "sao paulo": (-23.5558, -46.6396), "buenos aires": (-34.6037, -58.3816),
    "bogota": (4.7110, -74.0721), "mexico city": (19.4326, -99.1332), "lima": (-12.0464, -77.0428),
    "ottawa": (45.4215, -75.6972), "toronto": (43.6532, -79.3832), "vancouver": (49.2827, -123.1207),
    "canberra": (-35.2809, 149.1300), "melbourne": (-37.8136, 144.9631),
    "pyongyang": (39.0392, 125.7625), "dhaka": (23.8103, 90.4125), "colombo": (6.9271, 79.8612),
    "kathmandu": (27.7172, 85.3240), "thimphu": (27.4728, 89.6393),
}

COUNTRY_COORDS = {
    "india": (20.5937, 78.9629), "united states": (37.0902, -95.7129), "usa": (37.0902, -95.7129),
    "us": (37.0902, -95.7129), "china": (35.8617, 104.1954), "russia": (61.5240, 105.3188),
    "japan": (36.2048, 138.2529), "germany": (51.1657, 10.4515), "france": (46.2276, 2.2137),
    "uk": (55.3781, -3.4360), "united kingdom": (55.3781, -3.4360), "britain": (55.3781, -3.4360),
    "brazil": (-14.2350, -51.9253), "australia": (-25.2744, 133.7751), "canada": (56.1304, -106.3468),
    "south korea": (35.9078, 127.7669), "korea": (35.9078, 127.7669), "north korea": (40.3399, 127.5101),
    "mexico": (23.6345, -102.5528), "indonesia": (-0.7893, 113.9213), "turkey": (38.9637, 35.2433),
    "saudi arabia": (23.8859, 45.0792), "iran": (32.4279, 53.6880), "iraq": (33.2232, 43.6793),
    "pakistan": (30.3753, 69.3451), "afghanistan": (33.9391, 67.7100), "israel": (31.0461, 34.8516),
    "palestine": (31.9522, 35.2332), "egypt": (26.8206, 30.8025), "south africa": (-30.5595, 22.9375),
    "nigeria": (9.0820, 8.6753), "kenya": (-0.0236, 37.9062), "ethiopia": (9.1450, 40.4897),
    "ukraine": (48.3794, 31.1656), "poland": (51.9194, 19.1451), "italy": (41.8719, 12.5674),
    "spain": (40.4637, -3.7492), "taiwan": (23.6978, 120.9605), "singapore": (1.3521, 103.8198),
    "thailand": (15.8700, 100.9925), "vietnam": (14.0583, 108.2772), "philippines": (12.8797, 121.7740),
    "malaysia": (4.2105, 101.9758), "myanmar": (21.9162, 95.9560), "bangladesh": (23.6850, 90.3563),
    "sri lanka": (7.8731, 80.7718), "nepal": (28.3949, 84.1240), "argentina": (-38.4161, -63.6167),
    "colombia": (4.5709, -74.2973), "peru": (-9.1900, -75.0152), "chile": (-35.6751, -71.5430),
    "venezuela": (6.4238, -66.5897), "cuba": (21.5218, -77.7812), "syria": (34.8021, 38.9968),
    "yemen": (15.5527, 48.5164), "libya": (26.3351, 17.2283), "sudan": (12.8628, 30.2176),
    "somalia": (5.1521, 46.1996), "congo": (-4.0383, 21.7587),
    "european union": (50.8503, 4.3517), "eu": (50.8503, 4.3517),
    "nato": (50.8745, 4.3221), "un": (40.7489, -73.9680), "united nations": (40.7489, -73.9680),
    "imf": (38.8990, -77.0434), "world bank": (38.8990, -77.0434),
}


def geocode_text(text: str) -> list:
    """Extract locations from text and return coordinates"""
    if not text:
        return []

    text_lower = text.lower()
    found = []
    seen = set()

    # Check cities first (more specific)
    for name, coords in CITY_COORDS.items():
        if name in text_lower and name not in seen:
            seen.add(name)
            found.append({"name": name.title(), "lat": coords[0], "lng": coords[1], "type": "city"})

    # Then countries
    for name, coords in COUNTRY_COORDS.items():
        if name in text_lower and name not in seen:
            seen.add(name)
            found.append({"name": name.title(), "lat": coords[0], "lng": coords[1], "type": "country"})

    return found


def geocode_entities(entities: list) -> list:
    """Geocode a list of entity names"""
    results = []
    for entity in entities:
        name_lower = entity.lower() if isinstance(entity, str) else ""
        if name_lower in COUNTRY_COORDS:
            c = COUNTRY_COORDS[name_lower]
            results.append({"name": entity, "lat": c[0], "lng": c[1], "type": "country"})
        elif name_lower in CITY_COORDS:
            c = CITY_COORDS[name_lower]
            results.append({"name": entity, "lat": c[0], "lng": c[1], "type": "city"})
    return results
