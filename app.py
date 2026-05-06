"""
Kochi Metro Flat Finder — Flask backend
Serves the dashboard and provides:
  - /api/stations         : Phase 1 + Phase 2 station manifest
  - /api/projects         : cached/live project data per phase
  - /api/fetch-krera      : SSE stream — fetches KRERA + computes walk distances
"""

import json
import os
import time
import math
import re
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response, stream_with_context

app = Flask(__name__)
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── station manifests ─────────────────────────────────────────────────────────

PHASE1_STATIONS = [
    {"name": "Aluva",            "lat": 10.1104, "lng": 76.3523, "phase": 1, "status": "Operational"},
    {"name": "Pulinchodu",       "lat": 10.1003, "lng": 76.3491, "phase": 1, "status": "Operational"},
    {"name": "Companypady",      "lat": 10.0917, "lng": 76.3451, "phase": 1, "status": "Operational"},
    {"name": "Ambattukavu",      "lat": 10.0826, "lng": 76.3409, "phase": 1, "status": "Operational"},
    {"name": "Muttom",           "lat": 10.0734, "lng": 76.3367, "phase": 1, "status": "Operational"},
    {"name": "Kalamassery",      "lat": 10.0576, "lng": 76.3289, "phase": 1, "status": "Operational"},
    {"name": "CUSAT",            "lat": 10.0476, "lng": 76.3263, "phase": 1, "status": "Operational"},
    {"name": "Pathadipalam",     "lat": 10.0375, "lng": 76.3202, "phase": 1, "status": "Operational"},
    {"name": "Edapally",         "lat": 10.0201, "lng": 76.3075, "phase": 1, "status": "Operational"},
    {"name": "Changampuzha Park","lat": 10.0153, "lng": 76.2985, "phase": 1, "status": "Operational"},
    {"name": "Palarivattom",     "lat": 10.0073, "lng": 76.2982, "phase": 1, "status": "Operational"},
    {"name": "JLN Stadium",      "lat": 9.9989,  "lng": 76.2939, "phase": 1, "status": "Operational"},
    {"name": "Kaloor",           "lat": 9.9958,  "lng": 76.2879, "phase": 1, "status": "Operational"},
    {"name": "Town Hall",        "lat": 9.9921,  "lng": 76.2820, "phase": 1, "status": "Operational"},
    {"name": "MG Road",          "lat": 9.9894,  "lng": 76.2784, "phase": 1, "status": "Operational"},
    {"name": "Maharajas",        "lat": 9.9868,  "lng": 76.2758, "phase": 1, "status": "Operational"},
    {"name": "Ernakulam South",  "lat": 9.9825,  "lng": 76.2783, "phase": 1, "status": "Operational"},
    {"name": "Kadavanthra",      "lat": 9.9777,  "lng": 76.2825, "phase": 1, "status": "Operational"},
    {"name": "Elamkulam",        "lat": 9.9718,  "lng": 76.2863, "phase": 1, "status": "Operational"},
    {"name": "Vyttila",          "lat": 9.9669,  "lng": 76.2990, "phase": 1, "status": "Operational"},
    {"name": "Thykoodam",        "lat": 9.9594,  "lng": 76.3080, "phase": 1, "status": "Operational"},
    {"name": "Pettah",           "lat": 9.9516,  "lng": 76.3151, "phase": 1, "status": "Operational"},
    {"name": "Vadakkekotta",     "lat": 9.9469,  "lng": 76.3208, "phase": 1, "status": "Operational"},
    {"name": "SN Junction",      "lat": 9.9442,  "lng": 76.3247, "phase": 1, "status": "Operational"},
    {"name": "Tripunithura",     "lat": 9.9395,  "lng": 76.3381, "phase": 1, "status": "Operational"},
]

PHASE2_STATIONS = [
    {"name": "Palarivattom",       "lat": 10.0073, "lng": 76.2982, "phase": 2, "status": "Interchange — Phase 1"},
    {"name": "Aalinchuvadu",       "lat": 10.0089, "lng": 76.3121, "phase": 2, "status": "Under Construction"},
    {"name": "Chembumukku",        "lat": 10.0112, "lng": 76.3235, "phase": 2, "status": "Under Construction"},
    {"name": "Kakkanad",           "lat": 10.0143, "lng": 76.3389, "phase": 2, "status": "Under Construction"},
    {"name": "CSEZ",               "lat": 10.0166, "lng": 76.3521, "phase": 2, "status": "Under Construction"},
    {"name": "KINFRA Park",        "lat": 10.0185, "lng": 76.3634, "phase": 2, "status": "Under Construction"},
    {"name": "Rajagiri Vidyapeetham","lat": 10.0203,"lng": 76.3712, "phase": 2, "status": "Under Construction"},
    {"name": "Infopark",           "lat": 10.0221, "lng": 76.3803, "phase": 2, "status": "Under Construction"},
    {"name": "SmartCity",          "lat": 10.0215, "lng": 76.3901, "phase": 2, "status": "Under Construction"},
    {"name": "Chittethukara",      "lat": 10.0195, "lng": 76.3989, "phase": 2, "status": "Under Construction"},
    {"name": "SEZ",                "lat": 10.0178, "lng": 76.4067, "phase": 2, "status": "Under Construction"},
]

ALL_STATIONS = PHASE1_STATIONS + [s for s in PHASE2_STATIONS if s["name"] != "Palarivattom"]

# ── helpers ───────────────────────────────────────────────────────────────────

def haversine_m(lat1, lng1, lat2, lng2):
    """Straight-line distance in metres between two lat/lng points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_station_for_phase(lat, lng, phase):
    """Return (station_name, straight_line_meters) for closest station in phase."""
    candidates = PHASE1_STATIONS if phase == 1 else PHASE2_STATIONS
    best = min(candidates, key=lambda s: haversine_m(lat, lng, s["lat"], s["lng"]))
    dist = haversine_m(lat, lng, best["lat"], best["lng"])
    return best["name"], dist


def walk_estimate(straight_m):
    """Multiply straight-line by 1.35 detour factor; walk at 80 m/min."""
    walk_m = int(straight_m * 1.35)
    walk_min = max(1, round(walk_m / 80))
    return walk_m, walk_min


def geocode_address(address):
    """Nominatim geocode (no API key, OSM). Returns (lat, lng) or None."""
    try:
        q = urllib.parse.quote(address + ", Ernakulam, Kerala, India")
        url = f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "KochiMetroFlatFinder/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


def fetch_krera_projects_by_ids(id_range, district_code="601"):
    """
    KRERA's public /api/projects endpoint returns a single record keyed by UserID
    (not a paginated list). We iterate by project UserID to discover projects.
    district_code 601 = Ernakulam.
    Returns list of raw project dicts.
    """
    results = []
    for uid in id_range:
        url = f"https://rera.kerala.gov.in/api/projects?UserID={uid}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KochiMetroFlatFinder/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                item = json.loads(r.read())
                if isinstance(item, dict) and item.get("District") == district_code:
                    results.append(item)
        except Exception:
            pass
        time.sleep(0.05)
    return results


def map_krera_to_project(item, phase=1):
    """Convert a raw KRERA API record to our project schema."""
    name = (item.get("Name") or item.get("ProjectName") or "").strip()
    developer = (item.get("PromotorName") or item.get("Promoter") or "").strip()
    location_parts = [
        item.get("Village", ""), item.get("Taluka", ""), item.get("District", "")
    ]
    location = ", ".join(p for p in location_parts if p)
    krera_num = item.get("ProjectRegistrationNumber") or "Not found"

    status_raw = (item.get("ProjectStatus") or "").lower()
    if "complete" in status_raw or "finish" in status_raw:
        status = "Completed"
        completion_year = None
        expected = None
        try:
            d = item.get("ProjectEndDate") or item.get("ActualDateOfCompletion") or ""
            if d:
                completion_year = int(str(d)[:4])
        except Exception:
            pass
    else:
        status = "Ongoing"
        completion_year = None
        expected = None
        try:
            d = item.get("ProposedDateOfCompletion") or ""
            if d:
                expected = str(d)[:4]
        except Exception:
            pass

    units = None
    try:
        units = int(item.get("NumberOfResidentialUnits") or 0) or None
    except Exception:
        pass

    return {
        "name": name,
        "developer": developer,
        "location": location,
        "nearest_metro_station": None,
        "walk_distance_meters": None,
        "walk_time_minutes": None,
        "distance_to_highway_km": None,
        "status": status,
        "completion_year": completion_year,
        "expected_completion": expected,
        "krera_number": krera_num,
        "total_units": units,
        "total_area_acres": None,
        "configurations": [],
        "price_per_sqft_listed": None,
        "price_range": None,
        "avg_sold_price_sqft": None,
        "rental_yield_percent": None,
        "monthly_rent_2bhk_approx": None,
        "google_rating": None,
        "google_reviews_count": None,
        "builder_reputation_score": 5,
        "amenities": [],
        "lat": None,
        "lng": None,
        "krera_source_url": "https://rera.kerala.gov.in/projects",
        "notes": f"Auto-fetched from KRERA. Phase {phase} corridor.",
        "phase": phase,
    }


# ── cache layer ───────────────────────────────────────────────────────────────

def load_cached_projects():
    p = DATA_DIR / "projects_live.json"
    if p.exists():
        return json.loads(p.read_text())
    return None


def save_cached_projects(data):
    (DATA_DIR / "projects_live.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_base_projects():
    """Load the hand-curated projects_data.json as baseline."""
    p = BASE / "projects_data.json"
    if p.exists():
        raw = json.loads(p.read_text())
        # Assign phase based on station membership
        p2_names = {s["name"] for s in PHASE2_STATIONS}
        for proj in raw:
            proj.setdefault("lat", None)
            proj.setdefault("lng", None)
            station = proj.get("nearest_metro_station", "")
            if station in p2_names and station != "Palarivattom":
                proj["phase"] = 2
            else:
                proj["phase"] = 1
        return raw
    return []


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stations")
def api_stations():
    return jsonify({"phase1": PHASE1_STATIONS, "phase2": PHASE2_STATIONS})


@app.route("/api/projects")
def api_projects():
    live = load_cached_projects()
    if live:
        return jsonify(live)
    return jsonify(load_base_projects())


@app.route("/api/fetch-krera")
def fetch_krera_stream():
    """
    SSE endpoint — streams progress events then emits final data.
    Query params: phase (1 or 2, default both)
    """
    requested_phase = request.args.get("phase", "all")

    def generate():
        def sse(event, data):
            payload = json.dumps(data) if not isinstance(data, str) else data
            return f"event: {event}\ndata: {payload}\n\n"

        yield sse("progress", {"msg": "Starting KRERA data fetch...", "pct": 0})
        time.sleep(0.2)

        # Load existing curated data as baseline
        base = load_base_projects()
        existing_krera = {p["krera_number"] for p in base if p.get("krera_number") and p["krera_number"] != "Not found"}

        yield sse("progress", {"msg": f"Loaded {len(base)} curated projects as baseline.", "pct": 5})
        time.sleep(0.2)

        # Fetch KRERA projects by scanning UserID range
        # IDs are sequential; Ernakulam district code is 601.
        # We scan a window of ~200 IDs to find new projects within reasonable time.
        new_projects = []
        # Sample existing UserIDs from known KRERA numbers to find the current range
        # KRERA numbers like K-RERA/PRJ/ERN/xxx/20xx suggest IDs up to ~3000
        scan_ranges = list(range(1, 51)) + list(range(200, 251)) + list(range(500, 526))
        total_steps = len(scan_ranges)

        yield sse("progress", {"msg": f"Scanning {total_steps} KRERA project IDs for Ernakulam...", "pct": 8})

        found_raw = 0
        for i, uid in enumerate(scan_ranges):
            pct = 8 + int((i / total_steps) * 37)
            if i % 15 == 0:
                yield sse("progress", {"msg": f"Scanning KRERA ID {uid} ({i+1}/{total_steps})...", "pct": pct})
            url = f"https://rera.kerala.gov.in/api/projects?UserID={uid}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "KochiMetroFlatFinder/1.0"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    item = json.loads(r.read())
                    if isinstance(item, dict) and str(item.get("District", "")) == "601":
                        found_raw += 1
                        krera_num = item.get("ProjectRegistrationNumber") or ""
                        if krera_num and krera_num not in existing_krera:
                            proj = map_krera_to_project(item, phase=1)
                            new_projects.append(proj)
            except Exception:
                pass
            time.sleep(0.06)

        yield sse("progress", {"msg": f"Scanned {total_steps} IDs, found {found_raw} Ernakulam projects, {len(new_projects)} new.", "pct": 47})

        yield sse("progress", {"msg": f"Found {len(new_projects)} new projects from KRERA. Geocoding + distance calc...", "pct": 50})
        time.sleep(0.2)

        # Geocode and assign nearest station for new projects
        geocoded = 0
        p2_names = {s["name"] for s in PHASE2_STATIONS}

        for i, proj in enumerate(new_projects):
            pct = 50 + int((i / max(len(new_projects), 1)) * 30)
            if i % 5 == 0:
                yield sse("progress", {"msg": f"Geocoding project {i+1}/{len(new_projects)}...", "pct": pct})
            try:
                coords = geocode_address(proj["location"] or proj["name"])
                if coords:
                    proj["lat"], proj["lng"] = coords
                    # Find nearest station for Phase 1
                    s1, d1 = nearest_station_for_phase(coords[0], coords[1], 1)
                    # Find nearest station for Phase 2
                    s2, d2 = nearest_station_for_phase(coords[0], coords[1], 2)
                    # Assign phase by which corridor is closer
                    if d2 < d1 and d2 < 2000 and s2 != "Palarivattom":
                        proj["nearest_metro_station"] = s2
                        proj["phase"] = 2
                        wm, wt = walk_estimate(d2)
                    else:
                        proj["nearest_metro_station"] = s1
                        proj["phase"] = 1
                        wm, wt = walk_estimate(d1)
                    proj["walk_distance_meters"] = wm
                    proj["walk_time_minutes"] = wt
                    geocoded += 1
                time.sleep(0.1)
            except Exception:
                pass

        yield sse("progress", {"msg": f"Geocoded {geocoded}/{len(new_projects)} new projects.", "pct": 82})
        time.sleep(0.2)

        # Also recompute walk distances for base projects that lack lat/lng
        base_updated = 0
        for proj in base:
            if proj.get("lat") and proj.get("lng"):
                continue
            if proj.get("nearest_metro_station") and proj.get("walk_distance_meters"):
                continue
            station_name = proj.get("nearest_metro_station")
            if station_name:
                station = next((s for s in ALL_STATIONS if s["name"] == station_name), None)
                if station and not proj.get("walk_distance_meters"):
                    # assign approximate coords of the station as project proxy
                    proj["lat"] = station["lat"]
                    proj["lng"] = station["lng"]
                    base_updated += 1

        yield sse("progress", {"msg": f"Updated {base_updated} base projects with station coords.", "pct": 90})
        time.sleep(0.2)

        # Filter new projects to only those within 1500m of a station
        nearby = [p for p in new_projects if p.get("walk_distance_meters") is not None and p["walk_distance_meters"] <= 1500]

        # Filter to 2019+ completed only
        def keep(p):
            if p.get("status") == "Completed" and p.get("completion_year") and p["completion_year"] < 2019:
                return False
            if not p.get("name"):
                return False
            return True

        nearby = [p for p in nearby if keep(p)]

        # Merge: base + new (deduplicate by krera_number)
        merged = list(base)
        existing_krera_set = {p["krera_number"] for p in merged if p.get("krera_number") and p["krera_number"] != "Not found"}
        added = 0
        for p in nearby:
            if p.get("krera_number") and p["krera_number"] not in existing_krera_set:
                merged.append(p)
                existing_krera_set.add(p["krera_number"])
                added += 1

        save_cached_projects(merged)

        yield sse("progress", {"msg": f"Done! Added {added} new projects. Total: {len(merged)} projects.", "pct": 100})
        time.sleep(0.1)
        yield sse("complete", {"total": len(merged), "added": added})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050, threaded=True)
