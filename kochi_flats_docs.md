# Kochi Metro Flat Finder — Technical Documentation

> Last updated: May 2026  
> Dashboard: `kochi_metro_flats.html` · Data: `projects_data.json`

---

## 1. Project Overview

A single-file interactive HTML dashboard for researching apartment projects along the Kochi Metro corridor (Aluva → Thripunithura). Data sourced from KRERA, builder websites, and area-level price benchmarks.

**Goals:**
- Surface KRERA-registered projects near metro stations
- Rank by composite investment score (yield, walk distance, rating, builder reputation)
- Filter/sort by status, builder, price, configuration, and walk distance
- Show rental yield, avg sold price, and highway proximity per project

---

## 2. Architecture

```
projects_data.json          ← source of truth (edit this to update data)
        │
        ▼
Python embed script         ← injects JSON into HTML template as a JS const
        │
        ▼
kochi_metro_flats.html      ← self-contained: HTML + CSS + JS + data
```

The HTML file has **no external dependencies** — no CDN, no framework, no server. It runs entirely in the browser from a local file open.

### HTML internal structure

```
<header>                    stats bar (project count, avg yield, avg price)
<div.controls>              filter bar (status, builder, config, walk, price, rating, search, sort)
<div.main>
  <div.sidebar>             metro station list + builder list (click to filter)
  <div.table-area>          sortable/filterable results table
    <tbody>
      <tr>                  project row
      <tr.detail-row>       expandable detail panel per project
```

---

## 3. Data Schema (`projects_data.json`)

Each entry in the JSON array is one project. All fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Project name as registered in KRERA |
| `developer` | string | Builder / developer company name |
| `location` | string | Area and taluk (e.g. "Elamkulam, Kanayannur") |
| `nearest_metro_station` | string | Closest station on the Aluva–Thripunithura line |
| `walk_distance_meters` | int\|null | Estimated walking distance to metro station entrance |
| `walk_time_minutes` | int\|null | Estimated walk time (assume ~80m/min) |
| `distance_to_highway_km` | float\|null | Distance to nearest NH/state highway |
| `status` | string | `"Completed"` or `"Ongoing"` |
| `completion_year` | int\|null | Year completed (null if ongoing) |
| `expected_completion` | string\|null | Expected year string for ongoing projects (e.g. `"2026"`) |
| `krera_number` | string\|null | K-RERA registration number or `"Not found"` |
| `total_units` | int\|null | Total flats/units in the project |
| `total_area_acres` | float\|null | Total land area of the project |
| `configurations` | string[] | Unit types available: `["1BHK","2BHK","3BHK","4BHK"]` |
| `price_per_sqft_listed` | int\|null | Developer asking price per sqft (INR) |
| `price_range` | string\|null | Human-readable range e.g. `"75L-1.5Cr"` |
| `avg_sold_price_sqft` | int\|null | Average resale / sold price per sqft (INR) |
| `rental_yield_percent` | float\|null | Annual rental yield as % of purchase price |
| `monthly_rent_2bhk_approx` | int\|null | Approximate monthly rent for a 2BHK (INR) |
| `google_rating` | float\|null | Google Maps rating (1.0–5.0) |
| `google_reviews_count` | int\|null | Number of Google reviews |
| `builder_reputation_score` | int\|null | Internal score 1–10 (see scale below) |
| `amenities` | string[]\|null | List of amenities e.g. `["Pool","Gym","Clubhouse"]` |
| `krera_source_url` | string | URL used to source KRERA data |
| `notes` | string\|null | Free-text notes (units sold, context, caveats) |

### Builder reputation score scale
| Score | Meaning |
|-------|---------|
| 9–10 | Pan-India listed developer (Sobha, DLF, Puravankara) |
| 8 | Major Kerala developer, 10+ RERA projects, strong track record |
| 7 | Mid-size established builder, RERA-compliant |
| 6 | Smaller local builder, RERA-compliant, limited track record |
| ≤5 | Unknown or flagged builder |

---

## 4. Composite Score Formula

Computed in JavaScript at load time. Max possible score ≈ 90.

```js
function computeScore(p) {
  let s = 0;
  // Walk distance — closer is better (max 25 pts at 0m, 0 pts at 1500m+)
  if (p.walk_distance_meters != null)
    s += Math.max(0, (1500 - p.walk_distance_meters) / 1500) * 25;

  // Rental yield (max 20 pts at 5%+)
  if (p.rental_yield_percent != null)
    s += Math.min(p.rental_yield_percent / 5, 1) * 20;

  // Google rating (max 20 pts at 5.0)
  if (p.google_rating != null)
    s += (p.google_rating / 5) * 20;

  // Builder reputation (max 15 pts at score 10)
  if (p.builder_reputation_score != null)
    s += (p.builder_reputation_score / 10) * 15;

  // Project scale — total units (max 10 pts at 300+ units)
  if (p.total_units != null)
    s += Math.min(p.total_units / 300, 1) * 10;

  // Land area (max 10 pts at 5+ acres)
  if (p.total_area_acres != null)
    s += Math.min(p.total_area_acres / 5, 1) * 10;

  return Math.round(s * 10) / 10;
}
```

**To change weights:** Edit the multipliers in `computeScore()` inside `kochi_metro_flats.html`. The weights currently sum to 100.

---

## 5. Data Refresh Workflow

Follow this exact order when refreshing data:

### Step 1 — Fetch KRERA updates
```
URL: https://rera.kerala.gov.in/projects
Filter: District = Ernakulam
Pages: scroll through all (currently ~80 pages)
```
Export or scrape into a list. For each new/updated project, add/update an entry in `projects_data.json`.

Only include completed projects from **2019 onwards** (7-year rule, recalibrate annually — in 2027 the cutoff moves to 2020).

### Step 2 — Group by builder
Do NOT fetch each project's website individually. Identify all projects from the same builder and fetch the builder's website once:
```
Search: "[Builder Name] Kochi apartments official site"
Get: price per sqft, configurations, amenities for all their projects in one pass
```

### Step 3 — Walking distances
For each project, verify walking distance via Google Maps:
```
Query: "walking directions from [Project Address] to [Station] metro station Kochi"
```
Update `walk_distance_meters` and `walk_time_minutes` in `projects_data.json`.

### Step 4 — Price benchmarks (area-level only)
Use ONE search per area — do not scrape individual listings:
```
Search: "apartment resale price [Area] Kochi 2025"
```
Update `price_per_sqft_listed` and `avg_sold_price_sqft`.

### Step 5 — Regenerate the HTML
Run this Python snippet:

```python
import json

with open('projects_data.json') as f:
    projects = json.load(f)

# Read the current HTML
with open('kochi_metro_flats.html') as f:
    html = f.read()

# Replace the data payload
js_data = json.dumps(projects, ensure_ascii=False).replace('</script>', '<\\/script>')

# Find the line: const RAW = {...};
import re
html = re.sub(r'const RAW = \[.*?\];', f'const RAW = {js_data};', html, flags=re.DOTALL)

with open('kochi_metro_flats.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Updated: {len(projects)} projects")
```

---

## 6. Adding New Features — Step-by-Step

### 6.1 Add a new filter control

1. **Add the HTML control** in the `<div class="controls">` block:
```html
<div>
  <label>New Filter</label>
  <select id="fNewFilter">
    <option value="">All</option>
    <option value="ValueA">Value A</option>
  </select>
</div>
```

2. **Add the filter logic** in the `getFiltered()` function:
```js
const newFilter = document.getElementById('fNewFilter').value;
// ... inside the .filter() callback:
if (newFilter && p.some_field !== newFilter) return false;
```

3. **Wire up the change event** — add `'fNewFilter'` to the existing event-listener array:
```js
['fStatus','fBuilder','fConfig','fSearch','sortCol','sortDir','fNewFilter'].forEach(...)
```

4. **Add to `resetFilters()`**:
```js
document.getElementById('fNewFilter').value = '';
```

---

### 6.2 Add a new sortable column

1. **Add a `<th>` in `<thead>`** with a `data-col` attribute matching the JSON field name:
```html
<th data-col="distance_to_highway_km">Highway <span class="sort-icon">⇅</span></th>
```

2. **Add the `<td>` in `renderTable()`** — find the `tr.innerHTML = `` block and add your cell in the same position as the `<th>`:
```js
<td>${p.distance_to_highway_km != null ? p.distance_to_highway_km+'km' : '—'}</td>
```

3. **Add to the sort dropdown** in `<select id="sortCol">`:
```html
<option value="distance_to_highway_km">Highway Distance</option>
```

The `getSorted()` and column-click handler are generic — they work automatically for any `data-col`.

---

### 6.3 Add a new field to the data schema

1. Add the field to entries in `projects_data.json`
2. Add a row in the detail panel inside `renderTable()` (the `dtr.innerHTML` block):
```js
<div class="detail-kv">
  <span class="k">New Field Label</span>
  <span class="v">${p.new_field || '—'}</span>
</div>
```
3. Optionally surface it as a table column (see 6.2)
4. Update the schema table in this doc (Section 3)

---

### 6.4 Add a new composite score factor

Edit `computeScore()` in the HTML:
```js
// New factor — highway proximity (max 10 pts at 0.5km or closer)
if (p.distance_to_highway_km != null)
  s += Math.max(0, (2 - p.distance_to_highway_km) / 2) * 10;
```
Then rebalance other weights so they still sum to 100.

Update the weights table in `CLAUDE.md` and Section 4 of this doc.

---

### 6.5 Add a chart / visualization panel

The dashboard currently has no charts. To add one (e.g. yield by station):

1. Add a `<div id="chartArea">` below the controls bar
2. Include Chart.js via CDN or embed it inline:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```
3. After `renderTable()` calls, call a `renderChart()` function:
```js
function renderChart() {
  const filtered = getFiltered();
  const byStation = {};
  filtered.forEach(p => {
    if (!byStation[p.nearest_metro_station]) byStation[p.nearest_metro_station] = [];
    if (p.rental_yield_percent) byStation[p.nearest_metro_station].push(p.rental_yield_percent);
  });
  // ... Chart.js bar chart
}
```

---

### 6.6 Add a map view (Google Maps or Leaflet)

1. Add a toggle button: `<button class="btn secondary" onclick="toggleView()">Map View</button>`
2. Add a `<div id="mapArea" style="display:none;height:500px">` below the controls
3. Use Leaflet.js (no API key needed) with OpenStreetMap tiles:
```js
function initMap() {
  const map = L.map('mapArea').setView([10.02, 76.31], 12);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
  getFiltered().forEach(p => {
    if (p.lat && p.lng) {
      L.marker([p.lat, p.lng]).addTo(map)
        .bindPopup(`<b>${p.name}</b><br>${p.developer}<br>₹${p.price_per_sqft_listed}/sqft`);
    }
  });
}
```
4. **Required data change:** add `lat` and `lng` fields to `projects_data.json` for each project.

---

### 6.7 Export to CSV

Add this function and a button:
```html
<button class="btn secondary" onclick="exportCSV()">Export CSV</button>
```
```js
function exportCSV() {
  const fields = ['name','developer','nearest_metro_station','walk_distance_meters',
                  'status','completion_year','price_per_sqft_listed','rental_yield_percent',
                  'google_rating','builder_reputation_score','composite'];
  const rows = [fields.join(',')];
  getFiltered().forEach(p => {
    rows.push(fields.map(f => JSON.stringify(p[f] ?? '')).join(','));
  });
  const blob = new Blob([rows.join('\n')], {type: 'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'kochi_flats.csv';
  a.click();
}
```

---

### 6.8 Add a "compare" feature (side-by-side projects)

1. Add a checkbox column to the table
2. Track selected project IDs in a `Set`
3. Show a floating comparison panel at the bottom with selected projects side by side

---

## 7. Known Limitations & Caveats

| Item | Detail |
|------|--------|
| Walk distances | Geometry-estimated, not route-verified. Use Google Maps to confirm before any decision. |
| Google ratings | Many smaller projects have no Google presence — rating shown as `—`. |
| KRERA numbers | Some projects show "Not found" — cross-check directly at rera.kerala.gov.in |
| Prices | Listed prices are developer asking prices or area benchmarks, not transacted prices. |
| Rental yield | Calculated as `(annual 2BHK rent / mid-range unit price) × 100`. Actual yield varies by unit size and floor. |
| Completed cutoff | Currently 2019+. In 2027 update to 2020+. Adjust line in `getFiltered()`: `p.completion_year < 2019` |
| Phase 2 stations | Kakkanad and SN Junction–Tripunithura extension not yet fully operational — projects near those stations may have lower actual footfall. |

---

## 8. Planned Enhancements (Backlog)

- [ ] Add `lat`/`lng` to all projects and build Leaflet map view
- [ ] Add "Sold %" field (units sold / total units) from KRERA disclosures
- [ ] Fetch actual Google ratings via Places API or scrape
- [ ] Add price appreciation % (YoY) per area from Housing.com
- [ ] Export to CSV / Excel
- [ ] Side-by-side project comparison panel
- [ ] Phase 2 metro extension projects (Kakkanad corridor)
- [ ] Water Metro hub proximity (Vyttila, High Court, Vypeen) as an additional distance field
- [ ] Loan EMI calculator widget per project
- [ ] Annual data refresh reminder (set for May 2027)

---

## 9. File Manifest

```
/Users/MX936NE/personal/
├── kochi_metro_flats.html      ← live dashboard (open in any browser)
├── projects_data.json          ← master data file (edit to update)
├── kochi_flats_docs.md         ← this file
└── CLAUDE.md                   ← auto-loaded project context for Claude Code
```

---

## 10. Quick Reference — Editing the HTML

The HTML file has three logical sections separated by comments. Search for these anchors:

| What to find | Search for |
|---|---|
| CSS variables (theme) | `:root {` |
| Filter bar HTML | `<div class="controls">` |
| Sidebar HTML | `<div class="sidebar">` |
| Table headers | `<thead>` |
| Data constant | `const RAW =` |
| Composite score | `function computeScore` |
| Filter logic | `function getFiltered` |
| Sort logic | `function getSorted` |
| Table render | `function renderTable` |
| Sidebar render | `function renderSidebar` |
| Stats bar | `function renderStats` |
| Reset filters | `function resetFilters` |
| Column sort click | `querySelectorAll('thead th[data-col]')` |
