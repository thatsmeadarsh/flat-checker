# Kochi Metro Flat Finder

**Live site → [flat-checker.pages.dev](https://flat-checker.pages.dev)**

An interactive dashboard for researching KRERA-registered apartment projects along the Kochi Metro corridors. Ranks projects by a composite investment score covering walk distance to metro, rental yield, builder reputation, Google rating, and project scale.

---

## What it covers

| | Phase 1 | Phase 2 |
|---|---|---|
| **Route** | Aluva → Tripunithura | Palarivattom → SEZ (Kakkanad) |
| **Stations** | 25 (fully operational) | 11 (under construction) |
| **Projects** | 67 | 20 |
| **Status** | Live | Planned — invest early |

### Phase 1 stations
Aluva · Pulinchodu · Companypady · Ambattukavu · Muttom · Kalamassery · CUSAT · Pathadipalam · Edapally · Changampuzha Park · Palarivattom · JLN Stadium · Kaloor · Town Hall · MG Road · Maharajas · Ernakulam South · Kadavanthra · Elamkulam · Vyttila · Thykoodam · Pettah · Vadakkekotta · SN Junction · Tripunithura

### Phase 2 stations (under construction, Kakkanad IT corridor)
Palarivattom *(interchange)* · Aalinchuvadu · Chembumukku · Kakkanad · CSEZ · KINFRA Park · Rajagiri Vidyapeetham · Infopark · SmartCity · Chittethukara · SEZ

---

## Features

- **Phase switcher** — toggle between Phase 1, Phase 2, or all corridors
- **Sidebar station list** — click any station to filter projects near it
- **Composite score** — weighted ranking formula (details below)
- **Filters** — status, builder, config (1/2/3/4BHK), walk distance, price/sqft, min rating, free search
- **Sortable columns** — click any column header to sort
- **Expandable rows** — click ▶ on any project for full detail (KRERA number, amenities, rental data, notes)
- **Responsive stats bar** — live avg yield, avg price, project counts

---

## Composite score weights

| Factor | Weight | Logic |
|--------|--------|-------|
| Walk distance to metro | 25% | Max at 0 m, zero at 1500 m+ |
| Rental yield | 20% | Max at 5%+ annual yield |
| Google rating | 20% | Linear, max at 5.0 |
| Builder reputation | 15% | Internal 1–10 scale (see below) |
| Project scale (units) | 10% | Max at 300+ units |
| Land area | 10% | Max at 5+ acres |

### Builder reputation scale
| Score | Meaning |
|-------|---------|
| 9–10 | Pan-India listed developer (Sobha, DLF, Puravankara) |
| 8 | Major Kerala developer, 10+ RERA projects, strong track record |
| 7 | Mid-size established builder, RERA-compliant |
| 6 | Smaller local builder, limited track record |
| ≤5 | Unknown, auto-fetched, or flagged builder |

---

## Project structure

```
flat-checker/
├── projects_data.json          # Source of truth — 87 curated projects
├── templates/index.html        # Dashboard template (HTML + CSS + JS)
├── build.py                    # Bakes projects_data.json into public/index.html
├── app.py                      # Local Flask server (dev only)
├── run.sh                      # Start local server
├── public/                     # Build output — served by Cloudflare Pages
├── .github/workflows/
│   └── deploy.yml              # Weekly KRERA refresh job
└── wrangler.toml               # Cloudflare Pages build config
```

---

## How deployment works

```
GitHub (projects_data.json + templates/index.html)
        │
        │  push to main
        ▼
Cloudflare Pages runs: python3 build.py
        │
        │  injects project data into template
        ▼
public/index.html  →  flat-checker.pages.dev
```

- **Every push to `main`** triggers a Cloudflare rebuild (free, ~1 min)
- **Every Sunday 2am IST** GitHub Actions runs `build.py --fetch`, which scans the KRERA API for new Ernakulam projects, geocodes them via OpenStreetMap, assigns the nearest metro station, and commits any new projects back to `projects_data.json` — which triggers another Cloudflare deploy

No server runs in production. Everything is static HTML on Cloudflare's global CDN.

---

## Running locally

```bash
./run.sh
# Opens at http://localhost:5050
```

The local version has a live **"Fetch Latest from KRERA"** button with a real-time SSE progress stream. The static deployed version has the data baked in at build time.

Requirements: Python 3.10+, Flask (auto-installed by `run.sh` into a `.venv`).

---

## Updating project data manually

Edit `projects_data.json` directly, then push:

```bash
git add projects_data.json
git commit -m "data: add new projects near Kakkanad"
git push
```

Cloudflare redeploys automatically within ~1 minute.

To add a project, follow the schema in `kochi_flats_docs.md`. Key fields:

```json
{
  "name": "PROJECT NAME",
  "developer": "Builder Name",
  "location": "Area, Taluk",
  "nearest_metro_station": "Edapally",
  "walk_distance_meters": 600,
  "walk_time_minutes": 8,
  "status": "Ongoing",
  "expected_completion": "2027",
  "krera_number": "K-RERA/PRJ/ERN/xxx/20xx",
  "configurations": ["2BHK", "3BHK"],
  "price_per_sqft_listed": 8000,
  "rental_yield_percent": 3.5,
  "builder_reputation_score": 7,
  "phase": 1
}
```

---

## Data sources

| Source | Used for |
|--------|---------|
| [KRERA Kerala](https://rera.kerala.gov.in) | Project registration numbers, status, unit counts |
| Builder websites | Prices, configurations, amenities |
| Google Maps (geometry) | Walking distance estimates to metro stations |
| Housing.com / 99acres | Area-level price benchmarks |
| OpenStreetMap Nominatim | Geocoding for auto-fetched projects |

Walking distances are geometry-estimated (straight-line × 1.35 detour factor). Always verify on Google Maps before making any decision.

---

## Caveats

- Completed projects older than 2019 are excluded (7-year rule — update cutoff annually)
- Phase 2 stations are under construction; expected completion ~2027–2028
- Listed prices are developer asking prices or area benchmarks, not transacted prices
- Rental yield = `(annual 2BHK rent / mid-range unit price) × 100` — actual yield varies
- Auto-fetched KRERA projects have `builder_reputation_score: 5` until manually reviewed

---

## License

Personal use. Data sourced from public KRERA registry and open map services.
