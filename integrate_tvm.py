#!/usr/bin/env python3
"""
Integrate Trivandrum Metro data into kochi_metro_flats.html.
- Remaps TVM KRERA villages to correct 26 stations (Pappanamcode→Eanchakkal)
- Adds city:"Kochi"/"Trivandrum" to all projects
- Injects city-tab UI, disclaimer, and city-aware JS into the existing HTML
"""
import json, re

# ── 1. Correct TVM station order ──────────────────────────────────────────
TVM_STATIONS = [
    "Pappanamcode", "Kaimanam", "Karamana",
    "Thampanoor", "Secretariat", "Palayam", "Plamoodu", "Pattom",
    "Murinjapalam", "Medical College", "Ulloor", "Pongumoodu",
    "Sreekaryam", "Pangappara", "Gurumandiram", "Karyavattom",
    "Technopark Phase 1", "Technopark Phase 3", "Kulathoor",
    "Technopark Phase 2", "Akkulam Lake",
    "Kochuveli", "Venpalavattom", "Chaakka", "Airport", "Eanchakkal",
]

# ── 2. Village → (station, walk_m) ────────────────────────────────────────
# Corridor: south city → central → medical → university → Technopark → airport
VILLAGE_MAP = {
    "PAPPANAMCODE":          ("Pappanamcode",       400),
    "NEMOM":                 ("Pappanamcode",        900),
    "NEYYATTINKARA":         ("Pappanamcode",       1400),
    "KOLIYACODE":            ("Kaimanam",            600),
    "VILAVOORKAL":           ("Kaimanam",            700),
    "VILAPPIL":              ("Kaimanam",            800),
    "VEILOOR":               ("Karamana",            600),
    "MALAYINKEEZH":          ("Karamana",            900),
    "PETTAH":                ("Thampanoor",          600),
    "MANACAUD":              ("Thampanoor",          700),
    "MUTTATHARA":            ("Thampanoor",          800),
    "THYCAUD":               ("Secretariat",         500),
    "VANCHIYOOR":            ("Palayam",             600),
    "KOWDIAR":               ("Plamoodu",            500),
    "PATTOM":                ("Pattom",              400),
    "KUDAPPANAKUNNU":        ("Pattom",              600),
    "CHERUVAKKAL":           ("Pattom",              800),
    "PEROORKADA":            ("Murinjapalam",        700),
    "THIRUMALA":             ("Murinjapalam",        800),
    "SASTHAMANGALAM":        ("Medical College",     600),
    "ULOOR":                 ("Ulloor",              350),
    "KADAKAMPALLY":          ("Sreekaryam",          600),
    "AYIROOPARA":            ("Pangappara",          700),
    "PANGAPARA":             ("Pangappara",          400),
    "MELTHONACKAL":          ("Sreekaryam",          900),
    "ULIYAZHATHURA":         ("Gurumandiram",        800),
    "VATTAPPARA":            ("Karyavattom",         700),
    "KARAKULAM":             ("Karyavattom",         600),
    "ATTIPRA":               ("Technopark Phase 1",  600),
    "KAZHAKOOTTAM":          ("Technopark Phase 1",  700),
    "VATTIYOORKAVU":         ("Technopark Phase 3",  800),
    "VEMBAYAM":              ("Kulathoor",           700),
    "VEGANOOR":              ("Kulathoor",           900),
    "MENAMKULAM":            ("Akkulam Lake",        600),
    "PALLIPURAM TRIVANDRUM": ("Kochuveli",           700),
    "KADINAMKULAM":          ("Venpalavattom",       700),
    "THIRUVALLAM":           ("Venpalavattom",       800),
    "PALLICHAL":             ("Airport",             900),
}

# ── 3. Area price benchmarks per station ──────────────────────────────────
# (listed_psf, sold_psf, yield%, rent_2bhk, configs)
AREA_PRICE = {
    "Pappanamcode":       (4800, 4400, 4.2, 14000, ["2BHK","3BHK"]),
    "Kaimanam":           (5000, 4600, 4.0, 15000, ["2BHK","3BHK"]),
    "Karamana":           (5500, 5000, 3.9, 17000, ["2BHK","3BHK"]),
    "Thampanoor":         (7000, 6500, 3.6, 22000, ["1BHK","2BHK","3BHK"]),
    "Secretariat":        (8000, 7500, 3.4, 26000, ["2BHK","3BHK","4BHK"]),
    "Palayam":            (8500, 8000, 3.4, 28000, ["2BHK","3BHK","4BHK"]),
    "Plamoodu":           (7800, 7300, 3.5, 25000, ["2BHK","3BHK"]),
    "Pattom":             (8500, 8000, 3.5, 28000, ["2BHK","3BHK","4BHK"]),
    "Murinjapalam":       (6500, 6000, 3.6, 20000, ["2BHK","3BHK"]),
    "Medical College":    (7500, 7000, 3.6, 24000, ["2BHK","3BHK"]),
    "Ulloor":             (7500, 7000, 3.6, 24000, ["2BHK","3BHK"]),
    "Pongumoodu":         (6500, 6000, 3.7, 20000, ["2BHK","3BHK"]),
    "Sreekaryam":         (6000, 5500, 3.8, 19000, ["2BHK","3BHK"]),
    "Pangappara":         (5800, 5300, 3.8, 18000, ["2BHK","3BHK"]),
    "Gurumandiram":       (5500, 5000, 3.8, 17000, ["2BHK","3BHK"]),
    "Karyavattom":        (5700, 5200, 3.8, 18000, ["2BHK","3BHK"]),
    "Technopark Phase 1": (6500, 6000, 4.0, 22000, ["1BHK","2BHK","3BHK"]),
    "Technopark Phase 3": (6000, 5500, 4.0, 20000, ["1BHK","2BHK","3BHK"]),
    "Kulathoor":          (5800, 5300, 3.9, 18000, ["2BHK","3BHK"]),
    "Technopark Phase 2": (6200, 5700, 4.0, 21000, ["1BHK","2BHK","3BHK"]),
    "Akkulam Lake":       (5500, 5000, 3.9, 17000, ["2BHK","3BHK"]),
    "Kochuveli":          (5200, 4800, 3.9, 16000, ["2BHK","3BHK"]),
    "Venpalavattom":      (5000, 4600, 4.0, 15000, ["2BHK","3BHK"]),
    "Chaakka":            (4800, 4400, 4.1, 14000, ["2BHK","3BHK"]),
    "Airport":            (4600, 4200, 4.1, 14000, ["2BHK","3BHK"]),
    "Eanchakkal":         (4500, 4100, 4.2, 13000, ["2BHK","3BHK"]),
}

BUILDER_SCORE = {
    "SOBHA": 10, "DLF": 10,
    "CONFIDENT": 8, "ARTECH": 8, "ASSET": 8, "SKYLINE": 8,
    "OCEANUS": 7, "ARCON": 7, "CORDIAL": 7, "SFS": 7,
    "SANROYAL": 7, "SOWPARNIKA": 7, "HEATHER": 7,
    "FAVOURITE": 6, "SHANOOR": 6, "VFIVE": 6, "BEACON": 6,
    "ICLOUD": 6, "CORDON": 6, "VARMA": 6, "URBANSCAPE": 6,
    "KALYAN": 6, "JJ ": 5,
}

def builder_rep(name):
    u = name.upper()
    for k, v in BUILDER_SCORE.items():
        if k in u: return v
    return 5

def price_range(psf, configs):
    if "4BHK" in configs: lo, hi = psf*1200, psf*2500
    elif "3BHK" in configs: lo, hi = psf*900, psf*1800
    else: lo, hi = psf*550, psf*1200
    def fmt(v):
        if v >= 10_000_000: return f"{v/10_000_000:.1f}Cr"
        return f"{v/100_000:.0f}L"
    return f"{fmt(lo)}-{fmt(hi)}"

def parse_year(d):
    if not d: return None
    m = re.match(r"(\d{4})", d)
    return int(m.group(1)) if m else None

# ── 4. Build TVM projects ─────────────────────────────────────────────────
with open("projects_data_tvm_raw.json") as f:
    raw = json.load(f)

INCLUDE_TYPES = {"Residential (Apartment)", "Mixed (Commercial & Residential)"}
tvm_projects = []
for p in raw:
    if p.get("ProjectType") not in INCLUDE_TYPES:
        continue
    village = (p.get("Village") or "").strip().upper()
    if village not in VILLAGE_MAP:
        continue
    station, walk_m = VILLAGE_MAP[village]
    ap = AREA_PRICE.get(station, (6000, 5500, 3.7, 20000, ["2BHK","3BHK"]))
    psf, sold_psf, yld, rent, configs = ap
    status_raw = p.get("Status", "")
    status = "Completed" if status_raw == "Completed" else "Ongoing"
    comp_year = parse_year(p.get("DateOfCompletion"))
    if status == "Completed" and comp_year and comp_year < 2019:
        continue
    try:
        total_units = int(p.get("Total") or 0) or None
    except (ValueError, TypeError):
        total_units = None

    tvm_projects.append({
        "name": p["Project"].title(),
        "developer": p["PromoterName"].title(),
        "location": village.title() + ", Thiruvananthapuram",
        "nearest_metro_station": station,
        "walk_distance_meters": walk_m,
        "walk_time_minutes": round(walk_m / 80),
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
        "builder_reputation_score": builder_rep(p.get("PromoterName", "")),
        "amenities": None,
        "krera_source_url": "https://rera.kerala.gov.in/projects?district=601",
        "notes": f"Village: {village.title()}. Units sold: {p.get('Sold','—')} of {p.get('Total','—')}.",
        "lat": None,
        "lng": None,
        "city": "Trivandrum",
    })

tvm_station_idx = {s: i for i, s in enumerate(TVM_STATIONS)}
tvm_projects.sort(key=lambda x: (tvm_station_idx.get(x["nearest_metro_station"], 99), x["name"]))
print(f"TVM: {len(tvm_projects)} projects across {len({p['nearest_metro_station'] for p in tvm_projects})} stations")
by_station = {}
for p in tvm_projects:
    s = p["nearest_metro_station"]
    by_station[s] = by_station.get(s, 0) + 1
for s in TVM_STATIONS:
    if s in by_station:
        print(f"  {s}: {by_station[s]}")

# ── 5. Read existing HTML and extract Kochi RAW ───────────────────────────
with open("kochi_metro_flats.html", encoding="utf-8") as f:
    html = f.read()

# Extract existing Kochi projects
raw_match = re.search(r'const RAW = (\[.*?\]);', html, re.DOTALL)
kochi_raw = json.loads(raw_match.group(1))

# Tag with city
for p in kochi_raw:
    p["city"] = "Kochi"

# Combined dataset
all_projects = kochi_raw + tvm_projects
js_data = json.dumps(all_projects, ensure_ascii=False).replace("</script>", "<\\/script>")
print(f"Total combined: {len(all_projects)} projects ({len(kochi_raw)} Kochi + {len(tvm_projects)} TVM)")

# ── 6. Build JS station order constants ──────────────────────────────────
kochi_stations_js = json.dumps([
    "Aluva","Pulinchodu","Companypady","Ambattukavu","Muttom",
    "Kalamassery","CUSAT","Pathadipalam","Edapally","Changampuzha Park",
    "JLN Stadium","Kaloor","Town Hall","MG Road","Maharajas",
    "Ernakulam South","Kadavanthra","Elamkulam","Vyttila","Thykoodam",
    "Pettah","SN Junction","Tripunithura",
])
tvm_stations_js = json.dumps(TVM_STATIONS)

# ── 7. CSS additions ──────────────────────────────────────────────────────
css_additions = """
  .city-tabs { display: flex; gap: 6px; align-items: center; }
  .city-tab { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.15s; white-space: nowrap; }
  .city-tab:hover { border-color: var(--accent); color: var(--text); }
  .city-tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
  .tvm-disclaimer { background: rgba(245,158,11,0.07); border-bottom: 1px solid rgba(245,158,11,0.2); padding: 6px 24px; font-size: 11px; color: var(--muted); display: none; }
  .tvm-disclaimer.visible { display: block; }
  .tvm-disclaimer strong { color: var(--warn); }
"""

# ── 8. Apply HTML changes ─────────────────────────────────────────────────

# 8a. Inject CSS before closing </style>
html = html.replace("</style>", css_additions + "</style>", 1)

# 8b. Replace header block
old_header_inner = """  <div>
    <h1>Kochi Metro Corridor — Flat Finder</h1>
    <div class="subtitle">Aluva → Thripunithura &nbsp;|&nbsp; KRERA-registered projects &nbsp;|&nbsp; Data as of May 2026</div>
  </div>
  <div class="stats-bar" id="statsBar"></div>"""

new_header_inner = """  <div>
    <h1>Kerala Metro — Flat Finder</h1>
    <div class="subtitle" id="corridorSubtitle">Aluva → Thripunithura &nbsp;|&nbsp; KRERA-registered projects &nbsp;|&nbsp; Data as of May 2026</div>
  </div>
  <div class="city-tabs">
    <button class="city-tab active" id="tabKochi" onclick="setCity('Kochi')">🟦 Kochi Metro</button>
    <button class="city-tab" id="tabTrivandrum" onclick="setCity('Trivandrum')">🟨 Trivandrum Metro</button>
  </div>
  <div class="stats-bar" id="statsBar"></div>"""

html = html.replace(old_header_inner, new_header_inner, 1)

# 8c. Add TVM disclaimer after </header>
html = html.replace(
    "</header>",
    """</header>
<div class="tvm-disclaimer" id="tvmDisclaimer">
  <strong>⚠ Proposed metro:</strong> Trivandrum Metro Phase 1 is in DPR/approval stage — not yet under construction. Station-to-project walk distances are geometry estimates. Prices and yields are area benchmarks, not transaction data. Verify independently before any investment decision.
</div>""",
    1
)

# 8d. Replace RAW data
html = re.sub(
    r'const RAW = \[.*?\];',
    f'const RAW = {js_data};',
    html,
    flags=re.DOTALL
)

# 8e. Replace the entire script body (between const RAW and </script>)
# We'll inject new constants + modified functions

# Find the location of the existing stationOrder in renderSidebar and replace renderSidebar
old_render_sidebar = """function renderSidebar() {
  // Stations
  const stations = [...new Set(PROJECTS.map(p=>p.nearest_metro_station).filter(Boolean))];
  const stationOrder = ["Aluva","Pulinchodu","Companypady","Ambattukavu","Muttom","Kalamassery","CUSAT","Pathadipalam","Edapally","Changampuzha Park","JLN Stadium","Kaloor","Town Hall","MG Road","Maharajas","Ernakulam South","Kadavanthra","Elamkulam","Vyttila","Thykoodam","Pettah","SN Junction","Tripunithura"];
  const ordered = stationOrder.filter(s => stations.includes(s));
  const rest = stations.filter(s => !stationOrder.includes(s));
  const all = [...ordered, ...rest];

  const sl = document.getElementById('stationList');
  sl.innerHTML = `<div class="station-item ${!activeStation?'active':''}" onclick="setStation(null)">
    <span class="s-name">All Stations</span>
    <span class="s-count">${PROJECTS.length}</span>
  </div>`;
  all.forEach(s => {
    const cnt = PROJECTS.filter(p=>p.nearest_metro_station===s).length;
    const item = document.createElement('div');
    item.className = `station-item${activeStation===s?' active':''}`;
    item.innerHTML = `<span class="s-name">${s}</span><span class="s-count">${cnt}</span>`;
    item.onclick = () => setStation(s);
    sl.appendChild(item);
  });

  // Builders
  const builders = [...new Set(PROJECTS.map(p=>p.developer).filter(Boolean))].sort();
  const bl = document.getElementById('builderList');
  bl.innerHTML = `<div class="legend-item ${!activeBuilder?'active':''}" onclick="setBuilder(null)">
    <div class="legend-dot" style="background:var(--accent)"></div>
    <span class="name">All Builders</span>
    <span class="count">${builders.length}</span>
  </div>`;
  const colors = ['#5b6ef5','#22d3a5','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#84cc16','#f43f5e','#fb923c','#a78bfa'];
  builders.forEach((b,i) => {
    const cnt = PROJECTS.filter(p=>p.developer===b).length;
    const item = document.createElement('div');
    item.className = `legend-item${activeBuilder===b?' active':''}`;
    item.innerHTML = `<div class="legend-dot" style="background:${colors[i%colors.length]}"></div><span class="name">${b}</span><span class="count">${cnt}</span>`;
    item.onclick = () => setBuilder(b);
    bl.appendChild(item);
  });
}"""

new_render_sidebar = f"""const KOCHI_STATIONS = {kochi_stations_js};
const TVM_STATIONS_ORDER = {tvm_stations_js};

function stationOrderForCity() {{
  return activeCity === 'Trivandrum' ? TVM_STATIONS_ORDER : KOCHI_STATIONS;
}}

function renderSidebar() {{
  const cityProjects = PROJECTS.filter(p => p.city === activeCity);
  const stationOrder = stationOrderForCity();

  const sl = document.getElementById('stationList');
  sl.innerHTML = `<div class="station-item ${{!activeStation?'active':''}}" onclick="setStation(null)">
    <span class="s-name">All Stations</span>
    <span class="s-count">${{cityProjects.length}}</span>
  </div>`;
  stationOrder.forEach(s => {{
    const cnt = cityProjects.filter(p=>p.nearest_metro_station===s).length;
    if (!cnt) return;
    const item = document.createElement('div');
    item.className = `station-item${{activeStation===s?' active':''}}`;
    item.innerHTML = `<span class="s-name">${{s}}</span><span class="s-count">${{cnt}}</span>`;
    item.onclick = () => setStation(s);
    sl.appendChild(item);
  }});

  const builders = [...new Set(cityProjects.map(p=>p.developer).filter(Boolean))].sort();
  const bl = document.getElementById('builderList');
  bl.innerHTML = `<div class="legend-item ${{!activeBuilder?'active':''}}" onclick="setBuilder(null)">
    <div class="legend-dot" style="background:var(--accent)"></div>
    <span class="name">All Builders</span>
    <span class="count">${{builders.length}}</span>
  </div>`;
  const colors = ['#5b6ef5','#22d3a5','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#84cc16','#f43f5e','#fb923c','#a78bfa'];
  builders.forEach((b,i) => {{
    const cnt = cityProjects.filter(p=>p.developer===b).length;
    const item = document.createElement('div');
    item.className = `legend-item${{activeBuilder===b?' active':''}}`;
    item.innerHTML = `<div class="legend-dot" style="background:${{colors[i%colors.length]}}"></div><span class="name">${{b}}</span><span class="count">${{cnt}}</span>`;
    item.onclick = () => setBuilder(b);
    bl.appendChild(item);
  }});
}}"""

html = html.replace(old_render_sidebar, new_render_sidebar, 1)

# 8f. Add activeCity state + setCity function after "// State"
old_state = """// State
let activeStation = null;
let activeBuilder = null;
let sortCol = 'composite';
let sortDir = 'desc';"""

new_state = """// State
let activeCity = 'Kochi';
let activeStation = null;
let activeBuilder = null;
let sortCol = 'composite';
let sortDir = 'desc';

const SUBTITLES = {
  Kochi: 'Aluva → Thripunithura &nbsp;|  KRERA-registered projects &nbsp;|  Data as of May 2026',
  Trivandrum: 'Pappanamcode → Eanchakkal &nbsp;|  26 stations &nbsp;|  <strong style="color:var(--warn)">Proposed metro — DPR stage</strong> &nbsp;|  KRERA data May 2026',
};

function setCity(city) {
  activeCity = city;
  activeStation = null;
  activeBuilder = null;
  document.getElementById('tabKochi').classList.toggle('active', city === 'Kochi');
  document.getElementById('tabTrivandrum').classList.toggle('active', city === 'Trivandrum');
  document.getElementById('corridorSubtitle').innerHTML = SUBTITLES[city];
  const disc = document.getElementById('tvmDisclaimer');
  if (disc) disc.classList.toggle('visible', city === 'Trivandrum');
  rebuildBuilderDropdown();
  renderSidebar();
  renderTable();
  renderStats();
}"""

html = html.replace(old_state, new_state, 1)

# 8g. Add city filter to getFiltered()
old_getfiltered_start = """  return PROJECTS.filter(p => {
    if (status && p.status !== status) return false;
    if (p.status === 'Completed' && p.completion_year && p.completion_year < 2019) return false;"""

new_getfiltered_start = """  return PROJECTS.filter(p => {
    if (p.city !== activeCity) return false;
    if (status && p.status !== status) return false;
    if (p.status === 'Completed' && p.completion_year && p.completion_year < 2019) return false;"""

html = html.replace(old_getfiltered_start, new_getfiltered_start, 1)

# 8h. Replace builder dropdown init code with rebuildBuilderDropdown() function
old_builder_init = """// Builder dropdown
const builders = [...new Set(PROJECTS.map(p=>p.developer).filter(Boolean))].sort();
const bSel = document.getElementById('fBuilder');
builders.forEach(b => { const o = document.createElement('option'); o.value=b; o.textContent=b; bSel.appendChild(o); });"""

new_builder_init = """// Builder dropdown (city-aware)
function rebuildBuilderDropdown() {
  const cityProjects = PROJECTS.filter(p => p.city === activeCity);
  const builders = [...new Set(cityProjects.map(p=>p.developer).filter(Boolean))].sort();
  const bSel = document.getElementById('fBuilder');
  bSel.innerHTML = '<option value="">All Builders</option>';
  builders.forEach(b => { const o = document.createElement('option'); o.value=b; o.textContent=b; bSel.appendChild(o); });
}
rebuildBuilderDropdown();"""

html = html.replace(old_builder_init, new_builder_init, 1)

# 8i. Update resetFilters to not reset city
old_reset = """  activeStation = null; activeBuilder = null;
  renderSidebar(); renderTable(); renderStats();
}"""

new_reset = """  activeStation = null; activeBuilder = null;
  rebuildBuilderDropdown();
  renderSidebar(); renderTable(); renderStats();
}"""

# Only replace inside resetFilters (it's the last occurrence of this pattern)
html = html.replace(old_reset, new_reset, 1)

# ── 9. Write output ───────────────────────────────────────────────────────
with open("kochi_metro_flats.html", "w", encoding="utf-8") as f:
    f.write(html)

size_kb = len(html.encode()) / 1024
print(f"\nWrote kochi_metro_flats.html ({size_kb:.0f} KB)")
print(f"  Kochi: {len(kochi_raw)} projects | Trivandrum: {len(tvm_projects)} projects")
