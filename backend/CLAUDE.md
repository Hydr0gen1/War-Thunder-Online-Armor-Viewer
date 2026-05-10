# CLAUDE.md — backend/

FastAPI service. Entry point: `main.py`. Run with:

```bash
DATA_DIR=backend/data PYTHONPATH=backend uvicorn main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

## Module layout

```
main.py                 App factory, CORS, static GLB mount at /api/models/
routers/
  vehicles.py           GET /api/vehicles, /api/vehicles/{id}, /api/vehicles/{id}/armor
  shells.py             GET /api/shells/{cannonId}
  armor.py              POST /api/penetration/check
services/
  penetration.py        Core calculation engine — touch this carefully
  armor_class.py        Loads armor_classes.json, returns ke/heat multiplier
models/
  schemas.py            All Pydantic request/response models
data/                   Volume-mounted; never import from code by relative path
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATA_DIR` | `/app/data` | Root of the data directory |

Always read data via `os.environ.get("DATA_DIR", "/app/data")` — never hardcode paths.

## Penetration engine (`services/penetration.py`)

This is the most sensitive file. The formula is:

```
effective = thickness × armor_class_multiplier × generic_armor_quality × LOS_multiplier
LOS_multiplier = 1 / cos(angle_deg)        # capped at 2.0 for variableThickness zones
total_effective = sum(layer.effective for each layer)
penetrated = shell_pen > total_effective
```

**Shell pen:**
- APFSDS and other KE: piecewise-linear interpolation over `penCurve` at `range_m`
- HEAT-FS / ATGM: `penetration_flat_mm` — no curve, no range factor

**Group zones (`_isGroup: true`):** recurse into `children`, collect layers sequentially. The group-level `armorThickness` is not used in calculations.

**Non-armor zones (`_isModule`, `_isCrew`):** return zero layers immediately — never contribute effective thickness.

**Key invariant:** `calculate_penetration()` in `penetration.py` is pure — it takes dicts, returns a `PenCheckResponse`. The router in `armor.py` handles all I/O and HTTP error mapping.

## Armor class multipliers (`services/armor_class.py`)

`_cache` is module-level — loaded once from `armor_classes.json` on first call. To force a reload in tests, set `_cache = None` directly.

Unknown armor classes fall back to multiplier `1.0` (treated as RHA). Log a warning if you add new classes rather than silently relying on the fallback.

## Adding a new endpoint

1. Add route to the appropriate router in `routers/`
2. Add Pydantic schema to `models/schemas.py`
3. Keep business logic in `services/`, not in routers
4. Include the router in `main.py` if it's a new file

## Adding a new armor class

Edit `backend/data/armor_classes.json`. No code changes. The loader is file-based — add the new entry, the fallback disappears automatically.

## Dependencies

`requirements.txt` is pinned. Update with care — Pydantic v1 and v2 have incompatible APIs; this codebase uses **v2**.

## Testing penetration logic locally

```bash
python3 -c "
import json, sys, os
sys.path.insert(0, 'backend')
os.environ['DATA_DIR'] = 'backend/data'
from services.penetration import calculate_penetration

with open('backend/data/vehicles/sw_t_72m1.json') as f: v = json.load(f)
with open('backend/data/shells/2a46m.json') as f: s = json.load(f)
r = next(x for x in s['rounds'] if x['bulletName'] == '125mm_3bm42')
print(calculate_penetration(v, 'hull_composite_armor', 30, r, 500, 'ke'))
"
```
