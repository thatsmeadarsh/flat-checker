# Kochi Metro Flat Finder — Project Context for Claude Code

## What this project is
An interactive single-file HTML dashboard (`kochi_metro_flats.html`) listing KRERA-registered apartment projects along the Kochi Metro corridor from Aluva to Thripunithura. Built for investment/rental analysis.

## Key files
| File | Purpose |
|------|---------|
| `kochi_metro_flats.html` | The self-contained dashboard (HTML + CSS + JS, ~100KB) |
| `projects_data.json` | Source-of-truth data: 81 projects, all fields documented in `kochi_flats_docs.md` |
| `kochi_flats_docs.md` | Full architecture docs, data schema, and step-by-step enhancement guide |

## How to regenerate the HTML after data changes
```bash
python3 -c "
import json
with open('projects_data.json') as f:
    data = json.load(f)
js_data = json.dumps(data).replace('</script>', '<\\/script>')
# ... embed into HTML template
"
```
See `kochi_flats_docs.md` → Section 4 for the full regeneration script.

## Composite score weights (do not change without updating docs)
- Walk distance to metro: 25%
- Rental yield: 20%
- Google rating: 20%
- Builder reputation score: 15%
- Total units (project scale): 10%
- Total area in acres: 10%

## Data source workflow
1. KRERA website (https://rera.kerala.gov.in) — primary project registry
2. Builder websites — price, amenities, configurations (grouped per builder, not per project)
3. Housing.com / 99acres — area-level price benchmarks only (no individual listings)
4. Google Maps geometry — walking distance estimates to nearest metro station

## Metro stations in order (Aluva → Thripunithura)
Aluva, Pulinchodu, Companypady, Ambattukavu, Muttom, Kalamassery, CUSAT, Pathadipalam, Edapally, Changampuzha Park, JLN Stadium, Kaloor, Town Hall, MG Road, Maharajas, Ernakulam South, Kadavanthra, Elamkulam, Vyttila, Thykoodam, Pettah, SN Junction, Tripunithura

## Constraints to preserve
- Completed projects: only show 2019 or later (7-year rule)
- All projects must have a KRERA number or be explicitly marked "Not found"
- Walking distance is geometry-estimated — label as approximate in UI
- Do not scrape individual aggregator listing pages; use area-level benchmarks only
