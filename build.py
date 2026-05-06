#!/usr/bin/env python3
"""
Build script — reads projects_data.json and bakes it into a self-contained
public/index.html. Run locally or in CI.

Also does a lightweight KRERA refresh when called with --fetch:
  python3 build.py --fetch
"""

import json, sys, re, math, time, urllib.request, urllib.parse
from pathlib import Path

BASE        = Path(__file__).parent
DATA_IN     = BASE / "projects_data.json"
DATA_TVM    = BASE / "tvm_projects_data.json"
TMPL        = BASE / "templates" / "index.html"
OUT_DIR     = BASE / "public"
OUT_FILE    = OUT_DIR / "index.html"

# ── phase 2 station set (for phase-assignment logic) ─────────────────────────
PH2_STATIONS = {
    "Palarivattom","Aalinchuvadu","Chembumukku","Kakkanad",
    "CSEZ","KINFRA Park","Rajagiri Vidyapeetham","Infopark",
    "SmartCity","Chittethukara","SEZ"
}

PH1_STATIONS_COORDS = {
    "Aluva":            (10.1104, 76.3523),
    "Pulinchodu":       (10.1003, 76.3491),
    "Companypady":      (10.0917, 76.3451),
    "Ambattukavu":      (10.0826, 76.3409),
    "Muttom":           (10.0734, 76.3367),
    "Kalamassery":      (10.0576, 76.3289),
    "CUSAT":            (10.0476, 76.3263),
    "Pathadipalam":     (10.0375, 76.3202),
    "Edapally":         (10.0201, 76.3075),
    "Changampuzha Park":(10.0153, 76.2985),
    "Palarivattom":     (10.0073, 76.2982),
    "JLN Stadium":      (9.9989,  76.2939),
    "Kaloor":           (9.9958,  76.2879),
    "Town Hall":        (9.9921,  76.2820),
    "MG Road":          (9.9894,  76.2784),
    "Maharajas":        (9.9868,  76.2758),
    "Ernakulam South":  (9.9825,  76.2783),
    "Kadavanthra":      (9.9777,  76.2825),
    "Elamkulam":        (9.9718,  76.2863),
    "Vyttila":          (9.9669,  76.2990),
    "Thykoodam":        (9.9594,  76.3080),
    "Pettah":           (9.9516,  76.3151),
    "Vadakkekotta":     (9.9469,  76.3208),
    "SN Junction":      (9.9442,  76.3247),
    "Tripunithura":     (9.9395,  76.3381),
}

PH2_STATIONS_COORDS = {
    "Palarivattom":          (10.0073, 76.2982),
    "Aalinchuvadu":          (10.0089, 76.3121),
    "Chembumukku":           (10.0112, 76.3235),
    "Kakkanad":              (10.0143, 76.3389),
    "CSEZ":                  (10.0166, 76.3521),
    "KINFRA Park":           (10.0185, 76.3634),
    "Rajagiri Vidyapeetham": (10.0203, 76.3712),
    "Infopark":              (10.0221, 76.3803),
    "SmartCity":             (10.0215, 76.3901),
    "Chittethukara":         (10.0195, 76.3989),
    "SEZ":                   (10.0178, 76.4067),
}

def haversine_m(lat1, lng1, lat2, lng2):
    R = 6_371_000
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df = math.radians(lat2-lat1)
    dl = math.radians(lng2-lng1)
    a = math.sin(df/2)**2 + math.cos(f1)*math.cos(f2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def geocode(address):
    q = urllib.parse.quote(address + ", Ernakulam, Kerala, India")
    url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "KochiMetroFlatFinder-CI/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None

def nearest_station(lat, lng, coords_dict):
    best = min(coords_dict.items(), key=lambda kv: haversine_m(lat, lng, kv[1][0], kv[1][1]))
    dist = haversine_m(lat, lng, best[1][0], best[1][1])
    return best[0], dist

def fetch_krera_new(existing_krera_nums, verbose=True):
    """Scan a sample of KRERA UserIDs and return newly discovered Ernakulam projects."""
    new_projects = []
    scan_ids = list(range(1, 101)) + list(range(300, 351)) + list(range(700, 726))
    found = 0
    for uid in scan_ids:
        url = f"https://rera.kerala.gov.in/api/projects?UserID={uid}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KochiMetroFlatFinder-CI/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                item = json.loads(r.read())
            if isinstance(item, dict) and str(item.get("District","")) == "601":
                found += 1
                kn = item.get("ProjectRegistrationNumber","") or ""
                if kn and kn not in existing_krera_nums:
                    proj = krera_to_project(item)
                    new_projects.append(proj)
        except Exception:
            pass
        time.sleep(0.07)
    if verbose:
        print(f"  Scanned {len(scan_ids)} IDs → {found} Ernakulam projects, {len(new_projects)} new")
    return new_projects

def krera_to_project(item):
    name      = (item.get("Name") or "").strip()
    developer = (item.get("PromotorName") or item.get("Promoter") or "").strip()
    location  = ", ".join(p for p in [
        item.get("Village",""), item.get("Taluka",""), item.get("District","601")
    ] if p and p != "601")
    krera_num = item.get("ProjectRegistrationNumber") or "Not found"
    status_raw = (item.get("ProjectStatus") or "").lower()
    status = "Completed" if ("complete" in status_raw or "finish" in status_raw) else "Ongoing"
    completion_year = None
    expected = None
    try:
        if status == "Completed":
            d = item.get("ProjectEndDate") or item.get("ActualDateOfCompletion") or ""
            if d: completion_year = int(str(d)[:4])
        else:
            d = item.get("ProposedDateOfCompletion") or ""
            if d: expected = str(d)[:4]
    except Exception:
        pass
    units = None
    try: units = int(item.get("NumberOfResidentialUnits") or 0) or None
    except Exception: pass

    return {
        "name": name, "developer": developer, "location": location,
        "nearest_metro_station": None, "walk_distance_meters": None,
        "walk_time_minutes": None, "distance_to_highway_km": None,
        "status": status, "completion_year": completion_year,
        "expected_completion": expected, "krera_number": krera_num,
        "total_units": units, "total_area_acres": None, "configurations": [],
        "price_per_sqft_listed": None, "price_range": None,
        "avg_sold_price_sqft": None, "rental_yield_percent": None,
        "monthly_rent_2bhk_approx": None, "google_rating": None,
        "google_reviews_count": None, "builder_reputation_score": 5,
        "amenities": [], "lat": None, "lng": None,
        "krera_source_url": "https://rera.kerala.gov.in/projects",
        "notes": "Auto-fetched from KRERA.", "phase": 1,
    }

def assign_station_and_phase(proj):
    """Geocode project if needed and assign nearest station + phase."""
    lat, lng = proj.get("lat"), proj.get("lng")
    if not lat or not lng:
        coords = geocode(proj.get("location") or proj.get("name") or "")
        if coords:
            lat, lng = coords
            proj["lat"], proj["lng"] = lat, lng
        else:
            return proj  # can't geolocate

    s1, d1 = nearest_station(lat, lng, PH1_STATIONS_COORDS)
    s2, d2 = nearest_station(lat, lng, PH2_STATIONS_COORDS)

    # Use Phase 2 if it's meaningfully closer and not just the interchange
    if d2 < d1 and d2 < 2000 and s2 != "Palarivattom":
        proj["nearest_metro_station"] = s2
        proj["phase"] = 2
        walk_m = int(d2 * 1.35)
    else:
        proj["nearest_metro_station"] = s1
        proj["phase"] = 1
        walk_m = int(d1 * 1.35)

    proj["walk_distance_meters"] = walk_m
    proj["walk_time_minutes"] = max(1, round(walk_m / 80))
    return proj

def load_projects():
    return json.loads(DATA_IN.read_text(encoding="utf-8"))

def load_tvm_projects():
    if not DATA_TVM.exists():
        return []
    projects = json.loads(DATA_TVM.read_text(encoding="utf-8"))
    for p in projects:
        p["city"] = "Trivandrum"
        if "phase" not in p or p["phase"] is None:
            p["phase"] = 1
    return projects

def save_projects(projects):
    DATA_IN.write_text(json.dumps(projects, ensure_ascii=False, indent=2), encoding="utf-8")

def do_fetch():
    print("Fetching new projects from KRERA...")
    projects = load_projects()
    existing = {p["krera_number"] for p in projects if p.get("krera_number") and p["krera_number"] != "Not found"}
    new_raw = fetch_krera_new(existing)
    added = 0
    for proj in new_raw:
        proj = assign_station_and_phase(proj)
        # Only keep if within 1500m of a station and has a name
        if proj.get("name") and proj.get("walk_distance_meters") is not None and proj["walk_distance_meters"] <= 1500:
            # Skip old completed projects
            if proj.get("status") == "Completed" and proj.get("completion_year") and proj["completion_year"] < 2019:
                continue
            projects.append(proj)
            existing.add(proj["krera_number"])
            added += 1
        time.sleep(0.1)
    print(f"  Added {added} new projects. Total: {len(projects)}")
    if added > 0:
        save_projects(projects)
    return projects

def build(projects=None):
    if projects is None:
        projects = load_projects()

    # Ensure phase and city fields exist for Kochi projects
    for p in projects:
        p.setdefault("city", "Kochi")
        if "phase" not in p:
            station = p.get("nearest_metro_station","")
            p["phase"] = 2 if (station in PH2_STATIONS and station != "Palarivattom") else 1

    tvm_projects = load_tvm_projects()
    all_projects = projects + tvm_projects

    tmpl = TMPL.read_text(encoding="utf-8")

    # Inject projects as a JS constant in the template
    js_data = json.dumps(all_projects, ensure_ascii=False).replace("</script>", "<\\/script>")
    tmpl = re.sub(
        r"// __PROJECTS_DATA__",
        f"const INITIAL_PROJECTS = {js_data};",
        tmpl
    )

    OUT_DIR.mkdir(exist_ok=True)
    OUT_FILE.write_text(tmpl, encoding="utf-8")
    print(f"Built {OUT_FILE} ({len(projects)} Kochi + {len(tvm_projects)} TVM = {len(all_projects)} total, {OUT_FILE.stat().st_size // 1024}KB)")

if __name__ == "__main__":
    if "--fetch" in sys.argv:
        projects = do_fetch()
        build(projects)
    else:
        build()
