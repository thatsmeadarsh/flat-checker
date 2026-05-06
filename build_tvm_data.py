#!/usr/bin/env python3
"""
Build Trivandrum Metro flat-finder data from raw KRERA scrape.
Outputs: tvm_projects_data.json
"""
import json, re

with open("projects_data_tvm_raw.json") as f:
    raw = json.load(f)

# ── Metro station order (Technocity → Pallichal, Phase 1) ──────────────────
STATIONS = [
    "Technocity", "Pallipuram", "Kaniyapuram", "Kazhakuttam", "Technopark",
    "Kariavattom", "Gurumandiram", "Pangapara", "Sreekaryam", "Ulloor",
    "Kesavadasapuram", "Pattom", "Plamoodu", "Palayam", "Secretariat",
    "Thampanoor", "Killipalam", "Karamana", "Kaimanam", "Pappanamcode",
    "Karakamandapam", "Vellayani", "Nemom", "Pravachambalam", "Pallichal",
]

# ── Village → (station, walk_meters_range_mid) ────────────────────────────
VILLAGE_MAP = {
    # IT corridor
    "PALLIPURAM TRIVANDRUM": ("Pallipuram",   600),
    "KADINAMKULAM":          ("Pallipuram",  1100),
    "VEMBAYAM":              ("Kaniyapuram",  700),
    "VEGANOOR":              ("Kaniyapuram",  800),
    "KAZHAKOOTTAM":          ("Kazhakuttam",  500),
    "MENAMKULAM":            ("Kazhakuttam",  900),
    "ATTIPRA":               ("Technopark",   700),
    "VATTIYOORKAVU":         ("Technopark",  1100),
    "VATTAPPARA":            ("Kariavattom",  900),
    "KARAKULAM":             ("Kariavattom",  750),
    "ULIYAZHATHURA":         ("Gurumandiram",1000),
    "PANGAPARA":             ("Pangapara",    500),
    # Mid city
    "KADAKAMPALLY":          ("Sreekaryam",   700),
    "AYIROOPARA":            ("Sreekaryam",   900),
    "ULOOR":                 ("Ulloor",       350),
    "SASTHAMANGALAM":        ("Kesavadasapuram", 600),
    "KOWDIAR":               ("Kesavadasapuram", 700),
    "KUDAPPANAKUNNU":        ("Pattom",       600),
    "PATTOM":                ("Pattom",       400),
    "CHERUVAKKAL":           ("Pattom",       800),
    "PEROORKADA":            ("Pattom",      1100),
    # Central / prime
    "VANCHIYOOR":            ("Palayam",      800),
    "THYCAUD":               ("Secretariat",  600),
    "PETTAH":                ("Thampanoor",   600),
    "THIRUMALA":             ("Killipalam",   800),
    # South
    "VEILOOR":               ("Karamana",     700),
    "MALAYINKEEZH":          ("Karamana",    1100),
    "KOLIYACODE":            ("Kaimanam",     700),
    "VILAVOORKAL":           ("Pappanamcode", 900),
    "VILAPPIL":              ("Vellayani",    800),
    "NEMOM":                 ("Nemom",        500),
    "PALLICHAL":             ("Pallichal",    600),
    "NEYYATTINKARA":         ("Pallichal",   1400),
    # Outer / estates (still within 1500m)
    "ATTIPRA":               ("Technopark",   700),
}

# ── Builder reputation scores ─────────────────────────────────────────────
BUILDER_SCORE = {
    "SOBHA":       10,
    "DLF":         10,
    "CONFIDENT":    8,
    "ARTECH":       8,
    "ASSET":        8,
    "SKYLINE":      8,
    "OCEANUS":      7,
    "ARCON":        7,
    "CORDIAL":      7,
    "SFS":          7,
    "SANROYAL":     7,
    "SOWPARNIKA":   7,
    "HEATHER":      7,
    "FAVOURITE":    6,
    "SHANOOR":      6,
    "VFIVE":        6,
    "BEACON":       6,
    "ICLOUD":       6,
    "CORDON":       6,
    "VARMA":        6,
    "URBANSCAPE":   6,
    "KALYAN":       6,
    "JJ ":          5,
}

def builder_rep(name: str) -> int:
    u = name.upper()
    for k, v in BUILDER_SCORE.items():
        if k in u:
            return v
    return 5

# ── Area price benchmarks (₹/sqft listed, avg_sold) ──────────────────────
AREA_PRICE = {
    # station → (listed_psf, sold_psf, yield%, rent_2bhk, configs)
    "Technocity":       (5500, 5000, 3.8, 18000, ["1BHK","2BHK","3BHK"]),
    "Pallipuram":       (5200, 4800, 3.6, 16000, ["1BHK","2BHK","3BHK"]),
    "Kaniyapuram":      (5400, 4900, 3.7, 17000, ["2BHK","3BHK"]),
    "Kazhakuttam":      (6000, 5500, 3.9, 20000, ["1BHK","2BHK","3BHK"]),
    "Technopark":       (6500, 6000, 4.0, 22000, ["1BHK","2BHK","3BHK"]),
    "Kariavattom":      (5800, 5300, 3.7, 18000, ["2BHK","3BHK"]),
    "Gurumandiram":     (5600, 5100, 3.6, 17000, ["2BHK","3BHK"]),
    "Pangapara":        (5700, 5200, 3.7, 18000, ["2BHK","3BHK"]),
    "Sreekaryam":       (6200, 5700, 3.8, 20000, ["2BHK","3BHK"]),
    "Ulloor":           (7500, 7000, 3.6, 25000, ["2BHK","3BHK","4BHK"]),
    "Kesavadasapuram":  (8000, 7500, 3.5, 26000, ["2BHK","3BHK","4BHK"]),
    "Pattom":           (8500, 8000, 3.5, 28000, ["2BHK","3BHK","4BHK"]),
    "Plamoodu":         (8200, 7700, 3.5, 27000, ["2BHK","3BHK"]),
    "Palayam":          (9000, 8500, 3.4, 30000, ["2BHK","3BHK","4BHK"]),
    "Secretariat":      (8800, 8200, 3.4, 28000, ["2BHK","3BHK"]),
    "Thampanoor":       (7500, 7000, 3.6, 24000, ["1BHK","2BHK","3BHK"]),
    "Killipalam":       (6800, 6300, 3.7, 22000, ["2BHK","3BHK"]),
    "Karamana":         (6000, 5500, 3.8, 20000, ["2BHK","3BHK"]),
    "Kaimanam":         (5800, 5300, 3.8, 18000, ["2BHK","3BHK"]),
    "Pappanamcode":     (5500, 5000, 3.9, 17000, ["2BHK","3BHK"]),
    "Karakamandapam":   (5200, 4700, 3.8, 16000, ["2BHK","3BHK"]),
    "Vellayani":        (5000, 4500, 3.9, 15000, ["2BHK","3BHK"]),
    "Nemom":            (5200, 4800, 3.9, 16000, ["2BHK","3BHK"]),
    "Pravachambalam":   (4800, 4300, 4.0, 14000, ["2BHK","3BHK"]),
    "Pallichal":        (4600, 4200, 4.0, 13000, ["2BHK","3BHK"]),
}

def price_range(psf, configs):
    if "4BHK" in configs:
        lo, hi = psf * 1200, psf * 2500
    elif "3BHK" in configs:
        lo, hi = psf * 900, psf * 1800
    else:
        lo, hi = psf * 550, psf * 1200
    def fmt(v):
        if v >= 10_000_000: return f"{v/10_000_000:.1f}Cr"
        return f"{v/100_000:.0f}L"
    return f"{fmt(lo)}-{fmt(hi)}"

def parse_year(date_str):
    if not date_str: return None
    m = re.match(r"(\d{4})", date_str)
    return int(m.group(1)) if m else None

INCLUDE_TYPES = {"Residential (Apartment)", "Mixed (Commercial & Residential)"}

projects = []
for p in raw:
    if p.get("ProjectType") not in INCLUDE_TYPES:
        continue
    village = (p.get("Village") or "").strip().upper()
    if village not in VILLAGE_MAP:
        continue

    station, walk_m = VILLAGE_MAP[village]
    ap = AREA_PRICE.get(station, (6000, 5500, 3.7, 20000, ["2BHK","3BHK"]))
    psf, sold_psf, yld, rent, configs = ap

    status_raw = p.get("Status","")
    status = "Completed" if status_raw == "Completed" else "Ongoing"
    comp_year = parse_year(p.get("DateOfCompletion"))
    start_year = parse_year(p.get("ProjectStartDate"))

    # 7-year rule: skip completed before 2019
    if status == "Completed" and comp_year and comp_year < 2019:
        continue

    total_units = None
    try:
        total_units = int(p.get("Total") or 0) or None
    except (ValueError, TypeError):
        pass

    walk_time = round(walk_m / 80)

    entry = {
        "name": p["Project"].title(),
        "developer": p["PromoterName"].title(),
        "location": village.title() + ", Thiruvananthapuram",
        "nearest_metro_station": station,
        "walk_distance_meters": walk_m,
        "walk_time_minutes": walk_time,
        "distance_to_highway_km": None,
        "status": status,
        "completion_year": comp_year if status == "Completed" else None,
        "expected_completion": str(comp_year) if status == "Ongoing" and comp_year else None,
        "krera_number": p.get("CertiNo") or "Not found",
        "total_units": total_units,
        "total_area_acres": None,
        "configurations": configs,
        "price_per_sqft_listed": psf,
        "price_range": price_range(psf, configs),
        "avg_sold_price_sqft": sold_psf,
        "rental_yield_percent": yld,
        "monthly_rent_2bhk_approx": rent,
        "google_rating": None,
        "google_reviews_count": None,
        "builder_reputation_score": builder_rep(p.get("PromoterName","")),
        "amenities": None,
        "krera_source_url": "https://rera.kerala.gov.in/projects?district=601",
        "notes": f"Village: {village}. Units sold: {p.get('Sold','—')} of {p.get('Total','—')}.",
        "lat": None,
        "lng": None,
    }
    projects.append(entry)

# Sort by station order, then name
station_idx = {s: i for i, s in enumerate(STATIONS)}
projects.sort(key=lambda x: (station_idx.get(x["nearest_metro_station"], 99), x["name"]))

with open("tvm_projects_data.json", "w", encoding="utf-8") as f:
    json.dump(projects, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(projects)} projects to tvm_projects_data.json")
by_station = {}
for p in projects:
    s = p["nearest_metro_station"]
    by_station[s] = by_station.get(s, 0) + 1
for s in STATIONS:
    if s in by_station:
        print(f"  {s}: {by_station[s]}")
