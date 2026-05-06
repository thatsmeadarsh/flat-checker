#!/usr/bin/env python3
"""Generate tvm_metro_flats.html from tvm_projects_data.json."""
import json, re

with open("tvm_projects_data.json", encoding="utf-8") as f:
    projects = json.load(f)

js_data = json.dumps(projects, ensure_ascii=False).replace("</script>", "<\\/script>")

STATIONS_JS = json.dumps([
    "Technocity","Pallipuram","Kaniyapuram","Kazhakuttam","Technopark",
    "Kariavattom","Gurumandiram","Pangapara","Sreekaryam","Ulloor",
    "Kesavadasapuram","Pattom","Plamoodu","Palayam","Secretariat",
    "Thampanoor","Killipalam","Karamana","Kaimanam","Pappanamcode",
    "Karakamandapam","Vellayani","Nemom","Pravachambalam","Pallichal",
])

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trivandrum Metro Phase 1 — Flat Finder</title>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #222536;
    --border: #2e3250;
    --accent: #7c3aed;
    --accent2: #22d3a5;
    --warn: #f59e0b;
    --danger: #ef4444;
    --text: #e2e8f0;
    --muted: #8892b0;
    --completed: #22d3a5;
    --ongoing: #f59e0b;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 13px; }}

  header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
  header h1 {{ font-size: 20px; font-weight: 700; color: #fff; }}
  header .subtitle {{ color: var(--muted); font-size: 12px; }}
  .stats-bar {{ display: flex; gap: 16px; margin-left: auto; flex-wrap: wrap; }}
  .stat {{ text-align: center; }}
  .stat .val {{ font-size: 22px; font-weight: 700; color: var(--accent); }}
  .stat .lbl {{ font-size: 11px; color: var(--muted); }}

  .controls {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 24px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
  .controls label {{ color: var(--muted); font-size: 11px; margin-right: 4px; }}
  select, input[type=range], input[type=text] {{
    background: var(--surface2); border: 1px solid var(--border); color: var(--text);
    border-radius: 6px; padding: 5px 8px; font-size: 12px; outline: none;
  }}
  select:focus, input:focus {{ border-color: var(--accent); }}
  .range-group {{ display: flex; align-items: center; gap: 6px; }}
  .range-val {{ color: var(--accent2); font-weight: 600; min-width: 48px; font-size: 11px; }}
  .btn {{ background: var(--accent); color: #fff; border: none; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-size: 12px; font-weight: 600; }}
  .btn:hover {{ opacity: 0.85; }}
  .btn.secondary {{ background: var(--surface2); color: var(--text); border: 1px solid var(--border); }}
  .sort-group {{ display: flex; align-items: center; gap: 6px; }}

  .main {{ display: flex; height: calc(100vh - 130px); min-height: 0; }}

  .sidebar {{ width: 280px; min-width: 260px; background: var(--surface); border-right: 1px solid var(--border); overflow-y: auto; padding: 12px; }}
  .sidebar h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin: 12px 0 8px; }}

  .legend-item {{ display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.15s; }}
  .legend-item:hover {{ background: var(--surface2); }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  .legend-item .name {{ font-size: 12px; flex: 1; }}
  .legend-item .count {{ color: var(--muted); font-size: 11px; }}

  .metro-line {{ position: relative; padding: 4px 0 4px 20px; }}
  .metro-line::before {{ content: ''; position: absolute; left: 5px; top: 0; bottom: 0; width: 2px; background: var(--accent); }}
  .station-item {{ display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; position: relative; }}
  .station-item::before {{ content: ''; position: absolute; left: -14px; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); border: 2px solid var(--bg); }}
  .station-item .s-name {{ font-size: 11px; color: var(--text); }}
  .station-item .s-count {{ font-size: 10px; color: var(--muted); margin-left: auto; }}
  .station-item.active .s-name {{ color: var(--accent2); font-weight: 700; }}

  .table-area {{ flex: 1; overflow: auto; padding: 16px; }}

  .result-info {{ color: var(--muted); font-size: 12px; margin-bottom: 10px; }}
  .result-info span {{ color: var(--text); font-weight: 600; }}

  table {{ width: 100%; border-collapse: collapse; }}
  thead th {{
    background: var(--surface); color: var(--muted); font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.5px; padding: 8px 10px; text-align: left; border-bottom: 2px solid var(--border);
    position: sticky; top: 0; z-index: 10; cursor: pointer; white-space: nowrap; user-select: none;
  }}
  thead th:hover {{ color: var(--accent2); }}
  thead th.sorted {{ color: var(--accent2); }}
  thead th .sort-icon {{ margin-left: 4px; opacity: 0.5; }}
  thead th.sorted .sort-icon {{ opacity: 1; }}
  tbody tr {{ border-bottom: 1px solid var(--border); transition: background 0.1s; }}
  tbody tr:hover {{ background: var(--surface2); }}
  tbody td {{ padding: 9px 10px; vertical-align: middle; white-space: nowrap; }}

  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 10px; font-weight: 700; text-transform: uppercase; }}
  .badge.completed {{ background: rgba(34,211,165,0.15); color: var(--completed); border: 1px solid rgba(34,211,165,0.3); }}
  .badge.ongoing {{ background: rgba(245,158,11,0.15); color: var(--ongoing); border: 1px solid rgba(245,158,11,0.3); }}

  .stars {{ color: #fbbf24; letter-spacing: -1px; }}
  .rating-num {{ color: var(--muted); font-size: 11px; margin-left: 3px; }}

  .walk-bar {{ display: flex; align-items: center; gap: 6px; }}
  .walk-pill {{ height: 6px; border-radius: 3px; min-width: 4px; }}

  .rep-score {{ font-weight: 700; }}
  .rep-9 {{ color: #22d3a5; }}
  .rep-8 {{ color: #6ee7b7; }}
  .rep-7 {{ color: var(--warn); }}
  .rep-6 {{ color: #fb923c; }}
  .rep-low {{ color: var(--danger); }}

  .yield-val {{ font-weight: 600; }}
  .yield-high {{ color: var(--completed); }}
  .yield-mid {{ color: var(--warn); }}
  .yield-low {{ color: var(--muted); }}

  .project-name {{ font-weight: 600; color: #fff; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }}
  .krera-link {{ color: var(--accent); text-decoration: none; font-size: 10px; }}
  .krera-link:hover {{ text-decoration: underline; }}
  .config-tags {{ display: flex; gap: 3px; flex-wrap: wrap; }}
  .config-tag {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 3px; padding: 1px 5px; font-size: 10px; color: var(--muted); }}

  .detail-row {{ display: none; background: var(--surface2); }}
  .detail-row.open {{ display: table-row; }}
  .detail-content {{ padding: 14px 16px; color: var(--muted); font-size: 12px; line-height: 1.7; }}
  .detail-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }}
  .detail-kv {{ display: flex; flex-direction: column; }}
  .detail-kv .k {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--muted); }}
  .detail-kv .v {{ font-size: 13px; color: var(--text); font-weight: 500; margin-top: 2px; }}

  .expand-btn {{ cursor: pointer; color: var(--accent); font-size: 14px; user-select: none; }}

  .no-results {{ text-align: center; padding: 60px; color: var(--muted); }}

  .score-cell {{ display: flex; align-items: center; gap: 6px; }}
  .score-bar-bg {{ width: 50px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }}
  .score-bar {{ height: 6px; border-radius: 3px; background: var(--accent); }}

  .disclaimer {{ background: rgba(124,58,237,0.08); border: 1px solid rgba(124,58,237,0.25); border-radius: 6px;
    padding: 8px 14px; margin: 0 24px 0; font-size: 11px; color: var(--muted); display: flex; align-items: center; gap: 8px; }}
  .disclaimer strong {{ color: var(--warn); }}

  .sidebar-toggle-btn {{
    display: none;
    width: 100%;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 10px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
  }}

  @media (max-width: 768px) {{
    body {{ font-size: 12px; }}
    header {{ padding: 10px 14px; gap: 8px; }}
    header h1 {{ font-size: 16px; }}
    .stats-bar {{ margin-left: 0; gap: 10px; }}
    .stat .val {{ font-size: 18px; }}
    .controls {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 10px 12px; align-items: start;
    }}
    .controls label {{ display: block; margin-right: 0; margin-bottom: 2px; }}
    .controls select {{ width: 100%; }}
    .controls input[type=text] {{ width: 100% !important; }}
    .controls input[type=range] {{ width: 100%; }}
    .controls .range-group {{ flex-direction: column; align-items: flex-start; gap: 4px; }}
    .controls .range-group input[type=range] {{ width: 100%; }}
    .controls .sort-group {{ grid-column: span 2; flex-wrap: wrap; }}
    .controls .sort-group select {{ flex: 1; min-width: 120px; }}
    .controls .search-group {{ grid-column: span 2; }}
    .controls > button.btn {{ grid-column: span 2; }}
    .main {{ flex-direction: column; height: auto; min-height: unset; }}
    .sidebar {{ width: 100%; min-width: unset; border-right: none; border-bottom: 1px solid var(--border); padding: 8px 12px; }}
    .sidebar-toggle-btn {{ display: block; margin-bottom: 4px; }}
    #sidebarContent {{ display: none; }}
    #sidebarContent.open {{ display: block; max-height: 280px; overflow-y: auto; }}
    .table-area {{ padding: 10px 8px; overflow-x: auto; -webkit-overflow-scrolling: touch; }}
    #mainTable th:nth-child(3), #mainTable td:nth-child(3),
    #mainTable th:nth-child(8), #mainTable td:nth-child(8),
    #mainTable th:nth-child(9), #mainTable td:nth-child(9),
    #mainTable th:nth-child(13), #mainTable td:nth-child(13),
    #mainTable th:nth-child(15), #mainTable td:nth-child(15),
    #mainTable th:nth-child(16), #mainTable td:nth-child(16) {{ display: none; }}
    .disclaimer {{ margin: 0 8px; }}
  }}
  @media (max-width: 480px) {{
    header .subtitle {{ display: none; }}
    .stat .val {{ font-size: 15px; }}
    .stat .lbl {{ font-size: 9px; }}
    .stats-bar {{ gap: 8px; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>Trivandrum Metro Phase 1 — Flat Finder</h1>
    <div class="subtitle">Technocity → Pallichal &nbsp;|&nbsp; 25 stations, ~27 km &nbsp;|&nbsp; KRERA-registered projects &nbsp;|&nbsp; Data as of May 2026</div>
  </div>
  <div class="stats-bar" id="statsBar"></div>
</header>

<div class="disclaimer">
  <strong>⚠ Proposed metro:</strong> Trivandrum Metro Phase 1 is in DPR/approval stage — not yet under construction. Station locations, walk distances, and prices are estimates. Verify all details independently before any investment decision.
</div>

<div class="controls">
  <div>
    <label>Status</label>
    <select id="fStatus">
      <option value="">All</option>
      <option value="Completed">Completed</option>
      <option value="Ongoing">Ongoing</option>
    </select>
  </div>
  <div>
    <label>Builder</label>
    <select id="fBuilder"><option value="">All Builders</option></select>
  </div>
  <div>
    <label>Config</label>
    <select id="fConfig">
      <option value="">Any</option>
      <option value="1BHK">1BHK</option>
      <option value="2BHK">2BHK</option>
      <option value="3BHK">3BHK</option>
      <option value="4BHK">4BHK</option>
    </select>
  </div>
  <div class="range-group">
    <label>Walk ≤</label>
    <input type="range" id="fWalk" min="200" max="2000" step="100" value="2000">
    <span class="range-val" id="fWalkVal">Any</span>
  </div>
  <div class="range-group">
    <label>Price ≤</label>
    <input type="range" id="fPrice" min="3000" max="12000" step="500" value="12000">
    <span class="range-val" id="fPriceVal">Any</span>
  </div>
  <div class="search-group">
    <label>Search</label>
    <input type="text" id="fSearch" placeholder="project / area / builder..." style="width:160px">
  </div>
  <div class="sort-group">
    <label>Sort by</label>
    <select id="sortCol">
      <option value="composite">Best Match (Composite)</option>
      <option value="rental_yield_percent">Rental Yield</option>
      <option value="walk_distance_meters">Walk Distance</option>
      <option value="price_per_sqft_listed">Price/sqft</option>
      <option value="total_units">Project Size</option>
      <option value="completion_year">Year</option>
      <option value="builder_reputation_score">Builder Score</option>
    </select>
    <select id="sortDir">
      <option value="desc">↓ Desc</option>
      <option value="asc">↑ Asc</option>
    </select>
  </div>
  <button class="btn secondary" onclick="resetFilters()">Reset</button>
</div>

<div class="main">
  <div class="sidebar">
    <button class="sidebar-toggle-btn" id="sidebarToggle" onclick="toggleSidebar()">▼ Stations &amp; Builders</button>
    <div id="sidebarContent">
      <h3>Metro Stations</h3>
      <div class="metro-line" id="stationList"></div>
      <h3 style="margin-top:20px">Builders</h3>
      <div id="builderList"></div>
    </div>
  </div>
  <div class="table-area">
    <div class="result-info" id="resultInfo"></div>
    <table id="mainTable">
      <thead>
        <tr>
          <th></th>
          <th data-col="name">Project <span class="sort-icon">⇅</span></th>
          <th data-col="developer">Builder <span class="sort-icon">⇅</span></th>
          <th data-col="nearest_metro_station">Station <span class="sort-icon">⇅</span></th>
          <th data-col="walk_distance_meters">Walk <span class="sort-icon">⇅</span></th>
          <th data-col="status">Status <span class="sort-icon">⇅</span></th>
          <th data-col="completion_year">Year <span class="sort-icon">⇅</span></th>
          <th data-col="total_units">Units <span class="sort-icon">⇅</span></th>
          <th data-col="total_area_acres">Acres <span class="sort-icon">⇅</span></th>
          <th data-col="price_per_sqft_listed">₹/sqft <span class="sort-icon">⇅</span></th>
          <th data-col="rental_yield_percent">Yield <span class="sort-icon">⇅</span></th>
          <th data-col="google_rating">Rating <span class="sort-icon">⇅</span></th>
          <th data-col="builder_reputation_score">Rep <span class="sort-icon">⇅</span></th>
          <th data-col="composite">Score <span class="sort-icon">⇅</span></th>
          <th>Config</th>
          <th>KRERA</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
    <div class="no-results" id="noResults" style="display:none">No projects match the current filters.</div>
  </div>
</div>

<script>
const RAW = {js_data};

const STATION_ORDER = {STATIONS_JS};

function computeScore(p) {{
  let s = 0;
  if (p.walk_distance_meters != null)
    s += Math.max(0, (1500 - p.walk_distance_meters) / 1500) * 25;
  if (p.rental_yield_percent != null)
    s += Math.min(p.rental_yield_percent / 5, 1) * 20;
  if (p.google_rating != null)
    s += (p.google_rating / 5) * 20;
  if (p.builder_reputation_score != null)
    s += (p.builder_reputation_score / 10) * 15;
  if (p.total_units != null)
    s += Math.min(p.total_units / 300, 1) * 10;
  if (p.total_area_acres != null)
    s += Math.min(p.total_area_acres / 5, 1) * 10;
  return Math.round(s * 10) / 10;
}}

const PROJECTS = RAW.map(p => ({{ ...p, composite: computeScore(p) }}));

let activeStation = null;
let activeBuilder = null;
let sortCol = 'composite';
let sortDir = 'desc';

function getFiltered() {{
  const status  = document.getElementById('fStatus').value;
  const builder = document.getElementById('fBuilder').value;
  const config  = document.getElementById('fConfig').value;
  const walk    = parseInt(document.getElementById('fWalk').value);
  const price   = parseInt(document.getElementById('fPrice').value);
  const search  = document.getElementById('fSearch').value.toLowerCase();

  return PROJECTS.filter(p => {{
    if (status && p.status !== status) return false;
    if (p.status === 'Completed' && p.completion_year && p.completion_year < 2019) return false;
    if (builder && p.developer !== builder) return false;
    if (config && !(p.configurations || []).includes(config)) return false;
    if (walk < 2000 && (p.walk_distance_meters == null || p.walk_distance_meters > walk)) return false;
    if (price < 12000 && (p.price_per_sqft_listed == null || p.price_per_sqft_listed > price)) return false;
    if (activeStation && p.nearest_metro_station !== activeStation) return false;
    if (activeBuilder && p.developer !== activeBuilder) return false;
    if (search) {{
      const hay = [p.name, p.developer, p.location, p.nearest_metro_station].join(' ').toLowerCase();
      if (!hay.includes(search)) return false;
    }}
    return true;
  }});
}}

function getSorted(arr) {{
  return [...arr].sort((a, b) => {{
    let av = a[sortCol], bv = b[sortCol];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (typeof av === 'string') {{ av = av.toLowerCase(); bv = (bv||'').toLowerCase(); }}
    if (sortDir === 'asc') return av > bv ? 1 : av < bv ? -1 : 0;
    return av < bv ? 1 : av > bv ? -1 : 0;
  }});
}}

function walkColor(m) {{
  if (m <= 400) return '#22d3a5';
  if (m <= 800) return '#6ee7b7';
  if (m <= 1200) return '#f59e0b';
  return '#ef4444';
}}

function stars(r) {{
  if (!r) return '<span style="color:var(--muted)">—</span>';
  const full = Math.floor(r), half = r % 1 >= 0.5;
  let s = '';
  for (let i=0;i<full;i++) s+='★';
  if (half) s+='½';
  return `<span class="stars">${{s}}</span><span class="rating-num">${{r.toFixed(1)}}</span>`;
}}

function repClass(s) {{
  if (s >= 9) return 'rep-9';
  if (s >= 8) return 'rep-8';
  if (s >= 7) return 'rep-7';
  if (s >= 6) return 'rep-6';
  return 'rep-low';
}}

function yieldClass(y) {{
  if (!y) return 'yield-low';
  if (y >= 3.5) return 'yield-high';
  if (y >= 2.8) return 'yield-mid';
  return 'yield-low';
}}

function renderTable() {{
  const filtered = getSorted(getFiltered());
  const tbody = document.getElementById('tableBody');
  const noRes = document.getElementById('noResults');
  document.getElementById('mainTable').style.display = filtered.length ? '' : 'none';
  noRes.style.display = filtered.length ? 'none' : '';
  document.getElementById('resultInfo').innerHTML =
    `Showing <span>${{filtered.length}}</span> of <span>${{PROJECTS.length}}</span> projects`;

  tbody.innerHTML = '';
  filtered.forEach((p, i) => {{
    const detId = `det_${{i}}`;
    const configHtml = (p.configurations||[]).map(c=>`<span class="config-tag">${{c}}</span>`).join('');
    const walkBarW = p.walk_distance_meters ? Math.min(p.walk_distance_meters/1500*100,100) : 50;
    const walkColor_ = p.walk_distance_meters ? walkColor(p.walk_distance_meters) : '#888';
    const priceStr = p.price_per_sqft_listed ? `₹${{p.price_per_sqft_listed.toLocaleString()}}` : '—';
    const yieldStr = p.rental_yield_percent ? `${{p.rental_yield_percent.toFixed(1)}}%` : '—';
    const yearStr = p.status==='Completed'
      ? (p.completion_year||'—')
      : (p.expected_completion ? `Est. ${{p.expected_completion}}` : 'TBD');
    const scoreW = Math.min(p.composite/90*100, 100);
    const kreraPart = p.krera_number && p.krera_number!=='Not found'
      ? `<a class="krera-link" href="https://rera.kerala.gov.in/projects?district=601" target="_blank" title="${{p.krera_number}}">${{p.krera_number.replace('K-RERA/PRJ/TVM/','TVM/').replace('K-RERA/PRJ/','').substring(0,16)}}</a>`
      : '<span style="color:var(--muted)">—</span>';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="expand-btn" onclick="toggleDetail('${{detId}}')">▶</span></td>
      <td><div class="project-name" title="${{p.name}}">${{p.name}}</div><div style="color:var(--muted);font-size:10px">${{p.location}}</div></td>
      <td style="max-width:130px;overflow:hidden;text-overflow:ellipsis">${{p.developer}}</td>
      <td>${{p.nearest_metro_station||'—'}}</td>
      <td>
        <div class="walk-bar">
          <div class="score-bar-bg"><div class="walk-pill" style="width:${{walkBarW}}%;background:${{walkColor_}}"></div></div>
          <span style="color:${{walkColor_}};font-size:11px;font-weight:600">${{p.walk_distance_meters ? p.walk_distance_meters+'m' : '—'}}</span>
        </div>
        <div style="color:var(--muted);font-size:10px">${{p.walk_time_minutes ? p.walk_time_minutes+'min' : ''}}</div>
      </td>
      <td><span class="badge ${{(p.status||'').toLowerCase()}}">${{p.status||'—'}}</span></td>
      <td>${{yearStr}}</td>
      <td>${{p.total_units||'—'}}</td>
      <td>${{p.total_area_acres != null ? p.total_area_acres+'ac' : '—'}}</td>
      <td style="font-weight:600;color:var(--accent2)">${{priceStr}}</td>
      <td><span class="yield-val ${{yieldClass(p.rental_yield_percent)}}">${{yieldStr}}</span></td>
      <td>${{stars(p.google_rating)}}</td>
      <td><span class="rep-score ${{repClass(p.builder_reputation_score)}}">${{p.builder_reputation_score||'—'}}</span>/10</td>
      <td>
        <div class="score-cell">
          <div class="score-bar-bg" style="width:60px"><div class="score-bar" style="width:${{scoreW}}%"></div></div>
          <span style="color:var(--accent2);font-size:11px;font-weight:700">${{p.composite}}</span>
        </div>
      </td>
      <td><div class="config-tags">${{configHtml}}</div></td>
      <td>${{kreraPart}}</td>
    `;
    tbody.appendChild(tr);

    const dtr = document.createElement('tr');
    dtr.className = 'detail-row';
    dtr.id = detId;
    const monthlyRent = p.monthly_rent_2bhk_approx ? `₹${{p.monthly_rent_2bhk_approx.toLocaleString()}}/mo` : '—';
    dtr.innerHTML = `<td colspan="16">
      <div class="detail-content">
        <div class="detail-grid">
          <div class="detail-kv"><span class="k">KRERA Number</span><span class="v">${{p.krera_number||'—'}}</span></div>
          <div class="detail-kv"><span class="k">Price Range</span><span class="v">${{p.price_range||'—'}}</span></div>
          <div class="detail-kv"><span class="k">Avg Sold ₹/sqft</span><span class="v">${{p.avg_sold_price_sqft ? '₹'+p.avg_sold_price_sqft.toLocaleString() : '—'}}</span></div>
          <div class="detail-kv"><span class="k">Monthly Rent (2BHK)</span><span class="v">${{monthlyRent}}</span></div>
          <div class="detail-kv"><span class="k">Google Reviews</span><span class="v">${{p.google_reviews_count ? p.google_reviews_count+' reviews' : '—'}}</span></div>
          <div class="detail-kv"><span class="k">Total Area</span><span class="v">${{p.total_area_acres ? p.total_area_acres+' acres' : '—'}}</span></div>
          <div class="detail-kv"><span class="k">Total Units</span><span class="v">${{p.total_units||'—'}}</span></div>
          <div class="detail-kv"><span class="k">Units Sold</span><span class="v">${{(p.notes||'').match(/Sold: (\\d+)/)? p.notes.match(/Sold: (\\d+)/)[1]+' units' : '—'}}</span></div>
        </div>
        ${{p.notes ? `<div style="margin-top:8px;color:var(--muted);font-size:11px;font-style:italic">${{p.notes}}</div>` : ''}}
      </div>
    </td>`;
    tbody.appendChild(dtr);
  }});

  updateSortHeaders();
}}

function toggleDetail(id) {{
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('open');
  const btn = el.previousElementSibling?.querySelector('.expand-btn');
  if (btn) btn.textContent = el.classList.contains('open') ? '▼' : '▶';
}}

function renderSidebar() {{
  const sl = document.getElementById('stationList');
  sl.innerHTML = `<div class="station-item ${{!activeStation?'active':''}}" onclick="setStation(null)" style="cursor:pointer">
    <span class="s-name">All Stations</span>
    <span class="s-count">${{PROJECTS.length}}</span>
  </div>`;
  STATION_ORDER.forEach(s => {{
    const cnt = PROJECTS.filter(p=>p.nearest_metro_station===s).length;
    if (!cnt) return;
    const item = document.createElement('div');
    item.className = `station-item${{activeStation===s?' active':''}}`;
    item.innerHTML = `<span class="s-name">${{s}}</span><span class="s-count">${{cnt}}</span>`;
    item.onclick = () => setStation(s);
    sl.appendChild(item);
  }});

  const builders = [...new Set(PROJECTS.map(p=>p.developer).filter(Boolean))].sort();
  const bl = document.getElementById('builderList');
  bl.innerHTML = `<div class="legend-item ${{!activeBuilder?'active':''}}" onclick="setBuilder(null)">
    <div class="legend-dot" style="background:var(--accent)"></div>
    <span class="name">All Builders</span>
    <span class="count">${{builders.length}}</span>
  </div>`;
  const colors=['#7c3aed','#22d3a5','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#84cc16','#f43f5e','#fb923c','#a78bfa'];
  builders.forEach((b,i) => {{
    const cnt = PROJECTS.filter(p=>p.developer===b).length;
    const item = document.createElement('div');
    item.className = `legend-item${{activeBuilder===b?' active':''}}`;
    item.innerHTML = `<div class="legend-dot" style="background:${{colors[i%colors.length]}}"></div><span class="name">${{b}}</span><span class="count">${{cnt}}</span>`;
    item.onclick = () => setBuilder(b);
    bl.appendChild(item);
  }});
}}

function renderStats() {{
  const filtered = getFiltered();
  const completed = filtered.filter(p=>p.status==='Completed').length;
  const ongoing   = filtered.filter(p=>p.status==='Ongoing').length;
  const withYield = filtered.filter(p=>p.rental_yield_percent);
  const avgYield  = withYield.length ? withYield.reduce((a,p)=>a+p.rental_yield_percent,0)/withYield.length : 0;
  const withPrice = filtered.filter(p=>p.price_per_sqft_listed);
  const avgPrice  = withPrice.length ? withPrice.reduce((a,p)=>a+p.price_per_sqft_listed,0)/withPrice.length : 0;
  document.getElementById('statsBar').innerHTML = `
    <div class="stat"><div class="val">${{filtered.length}}</div><div class="lbl">Projects</div></div>
    <div class="stat"><div class="val" style="color:var(--completed)">${{completed}}</div><div class="lbl">Completed</div></div>
    <div class="stat"><div class="val" style="color:var(--ongoing)">${{ongoing}}</div><div class="lbl">Ongoing</div></div>
    <div class="stat"><div class="val">${{avgYield.toFixed(1)}}%</div><div class="lbl">Avg Yield</div></div>
    <div class="stat"><div class="val">₹${{Math.round(avgPrice).toLocaleString()}}</div><div class="lbl">Avg ₹/sqft</div></div>
  `;
}}

function setStation(s) {{ activeStation = s; activeBuilder = null; renderSidebar(); renderTable(); renderStats(); }}
function setBuilder(b) {{ activeBuilder = b; activeStation = null; renderSidebar(); renderTable(); renderStats(); }}

function resetFilters() {{
  document.getElementById('fStatus').value = '';
  document.getElementById('fBuilder').value = '';
  document.getElementById('fConfig').value = '';
  document.getElementById('fWalk').value = 2000;
  document.getElementById('fPrice').value = 12000;
  document.getElementById('fSearch').value = '';
  document.getElementById('fWalkVal').textContent = 'Any';
  document.getElementById('fPriceVal').textContent = 'Any';
  document.getElementById('sortCol').value = 'composite';
  document.getElementById('sortDir').value = 'desc';
  sortCol = 'composite'; sortDir = 'desc';
  activeStation = null; activeBuilder = null;
  renderSidebar(); renderTable(); renderStats();
}}

function updateSortHeaders() {{
  document.querySelectorAll('thead th[data-col]').forEach(th => {{
    th.classList.toggle('sorted', th.dataset.col === sortCol);
    const icon = th.querySelector('.sort-icon');
    if (icon && th.dataset.col === sortCol) icon.textContent = sortDir==='asc'?'↑':'↓';
    else if (icon) icon.textContent = '⇅';
  }});
}}

// Builder dropdown
const builders_ = [...new Set(PROJECTS.map(p=>p.developer).filter(Boolean))].sort();
const bSel = document.getElementById('fBuilder');
builders_.forEach(b => {{ const o = document.createElement('option'); o.value=b; o.textContent=b; bSel.appendChild(o); }});

document.getElementById('fWalk').addEventListener('input', function() {{
  document.getElementById('fWalkVal').textContent = this.value >= 2000 ? 'Any' : this.value+'m';
  renderTable(); renderStats();
}});
document.getElementById('fPrice').addEventListener('input', function() {{
  document.getElementById('fPriceVal').textContent = this.value >= 12000 ? 'Any' : '₹'+parseInt(this.value).toLocaleString();
  renderTable(); renderStats();
}});

['fStatus','fBuilder','fConfig','fSearch','sortCol','sortDir'].forEach(id => {{
  document.getElementById(id).addEventListener('change', () => {{ renderTable(); renderStats(); }});
}});
document.getElementById('fSearch').addEventListener('input', () => {{ renderTable(); renderStats(); }});

document.querySelectorAll('thead th[data-col]').forEach(th => {{
  th.addEventListener('click', () => {{
    if (sortCol === th.dataset.col) {{
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    }} else {{
      sortCol = th.dataset.col;
      sortDir = 'desc';
    }}
    document.getElementById('sortCol').value = sortCol;
    document.getElementById('sortDir').value = sortDir;
    renderTable();
  }});
}});

function toggleSidebar() {{
  const content = document.getElementById('sidebarContent');
  const btn = document.getElementById('sidebarToggle');
  content.classList.toggle('open');
  btn.textContent = content.classList.contains('open') ? '▲ Stations & Builders' : '▼ Stations & Builders';
}}

renderSidebar();
renderTable();
renderStats();
</script>
</body>
</html>"""

with open("tvm_metro_flats.html", "w", encoding="utf-8") as f:
    f.write(HTML)

size_kb = len(HTML.encode()) / 1024
print(f"Written tvm_metro_flats.html ({size_kb:.0f} KB, {len(projects)} projects)")
