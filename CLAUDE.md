# CLAUDE.md — War Thunder Armor Viewer (root)

## Project purpose

Full-stack Dockerized web app replicating the War Thunder in-game X-ray armor viewer. Source data is extracted from game files by a separate pipeline (not part of this repo). This app consumes that data and builds a viewer around it.

## Repository map

```
backend/    FastAPI API + penetration engine
frontend/   React + React Three Fiber viewer
converter/  Standalone data pipeline scripts (not Dockerized)
```

Each subdirectory has its own CLAUDE.md with subsystem-specific guidance.

## Running the app

```bash
# Docker (recommended)
docker compose up

# Local dev
DATA_DIR=backend/data uvicorn backend.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

## Key architectural decisions

**Data loading is file-based, not DB-backed.** The backend scans `backend/data/vehicles/*.json` on every request. No restart is needed to add vehicles. If the dataset grows past ~1000 vehicles, consider an in-memory index built at startup.

**Zone name → mesh name is 1:1 by string key.** The `damageParts` key `hull_composite_armor` corresponds to a mesh node named `hull_composite_armor` in the xray skeleton `.glb`. No lookup table exists or should be added.

**`xrayTextThickness` ≠ `armorThickness`.** `xrayTextThickness` in `xrayViewerData` is Gaijin's curated display label. Always use `armorThickness` × armor class multiplier for actual penetration math. Use `xrayTextThickness` only for UI labels.

**Composite/spaced armor groups are processed sequentially.** Total effective thickness is the sum of all child layer effective thicknesses, not the group's own thickness field. The group's `armorThickness` field, if present, is ignored in calculations.

**HEAT is range-independent.** HEAT-FS and ATGM use `penetration_flat_mm`. Never apply a pen curve to chemical energy shells.

**`variableThickness: true` means the angle is partially pre-baked.** Cap the LOS multiplier at 2.0 for these zones. Do not apply the full `1/cos(angle)` formula.

## Data directory layout

```
backend/data/
├── armor_classes.json          # ke/heat multipliers per armor class
├── vehicles/<vehicleId>.json   # one file per vehicle
├── shells/<cannonId>.json      # one file per cannon
└── models/<modelId>.glb        # optional; served at /api/models/<modelId>.glb
```

Vehicles reference cannons by `"shells": ["cannonId"]`. A vehicle can list multiple cannons; all rounds are merged for display.

## Adding a vehicle

1. Drop `backend/data/vehicles/<vehicleId>.json` and `backend/data/shells/<cannonId>.json`
2. Optionally add `backend/data/models/<modelId>.glb`
3. No code changes, no restart needed

Use `converter/build_vehicle_json.py` to generate both JSON files from raw BLK extracts.

## Git branch

Active development branch: `claude/wt-armor-viewer-hobEh`

## What is intentionally absent

- No database — files are the source of truth
- No authentication — read-only public viewer
- No test suite yet — add pytest for `services/penetration.py` first
- No production nginx config yet — the `prod` stage in `frontend/Dockerfile` exists but is not wired into `docker-compose.yml`
