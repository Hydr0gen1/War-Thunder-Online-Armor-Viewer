# War Thunder Online Armor Viewer

A full-stack web app that replicates the War Thunder in-game X-ray armor viewer. Select a vehicle, pick an ammunition type, adjust range, and click any armor zone to see whether your shell penetrates — with a full layer-by-layer breakdown of composite and spaced armor.

![layout: left sidebar (vehicle + ammo) | 3D viewer | right sidebar (pen result)](docs/screenshot-placeholder.png)

---

## Features

- **3D armor viewer** — React Three Fiber canvas with zone-colored meshes (green / yellow / red by penetration margin)
- **Penetration calculator** — KE and HEAT shell types, pen curve interpolation, composite armor layer stacking, LOS angle multiplier with variable-thickness cap
- **Live range slider** — shell pen updates client-side as you drag; API is called on zone click
- **Composite armor breakdown** — all child layers shown with nominal and effective thickness
- **xrayTextThickness labels** — UI shows Gaijin's curated display values, math uses actual armor thickness
- **ERA / overlay toggle** — hide/show `hidableInViewer` and `hidableInXrayViewer` zones
- **Dockerized** — single `docker compose up` runs everything

---

## Quick Start

### With Docker (recommended)

```bash
git clone https://github.com/Hydr0gen1/War-Thunder-Online-Armor-Viewer
cd War-Thunder-Online-Armor-Viewer
docker compose up
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Without Docker

```bash
# Backend
pip install -r backend/requirements.txt
DATA_DIR=backend/data uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev          # http://localhost:3000
```

---

## Repository Layout

```
wt-armor-viewer/
├── docker-compose.yml
├── backend/
│   ├── main.py               # FastAPI app, CORS, static GLB mount
│   ├── routers/
│   │   ├── vehicles.py       # GET /api/vehicles[/{id}][/{id}/armor]
│   │   ├── shells.py         # GET /api/shells/{cannonId}
│   │   └── armor.py          # POST /api/penetration/check
│   ├── services/
│   │   ├── penetration.py    # pen calc engine (layer stacking, LOS, interpolation)
│   │   └── armor_class.py    # ke/heat multiplier loader (armor_classes.json)
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response models
│   └── data/                 # volume-mounted; add vehicles + shells here
│       ├── armor_classes.json
│       ├── vehicles/sw_t_72m1.json
│       ├── shells/2a46m.json
│       └── models/           # drop .glb files here (served at /api/models/)
├── frontend/
│   └── src/
│       ├── App.jsx            # three-panel layout
│       ├── components/
│       │   ├── VehicleSearch.jsx     # searchable vehicle list
│       │   ├── ArmorViewer3D.jsx     # R3F canvas + placeholder box model
│       │   ├── ArmorZoneOverlay.jsx  # 2D zone list, click to highlight + check
│       │   ├── ShellSelector.jsx     # ammo dropdown + range slider
│       │   └── PenResultHUD.jsx      # last pen result + layer breakdown
│       ├── hooks/usePenetrationCalc.js
│       └── lib/
│           ├── api.js         # fetch wrappers for all endpoints
│           └── store.js       # Zustand global state
└── converter/                 # standalone scripts, NOT in Docker
    ├── grp_to_gltf.py         # GRP2/DAG → glTF converter (needs DAG spec)
    └── build_vehicle_json.py  # assembles per-vehicle JSON from raw BLK extracts
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/vehicles` | List all vehicles (id, name, nation, BR, type) |
| `GET` | `/api/vehicles/{vehicleId}` | Full vehicle record |
| `GET` | `/api/vehicles/{vehicleId}/armor` | damageParts + xrayViewerData only |
| `GET` | `/api/shells/{cannonId}` | Shell list with pen curves |
| `POST` | `/api/penetration/check` | Penetration check (see below) |
| `GET` | `/api/models/{vehicleId}.glb` | Static GLB model file |
| `GET` | `/health` | Health check |

### Penetration check

```bash
curl -X POST http://localhost:8000/api/penetration/check \
  -H 'Content-Type: application/json' \
  -d '{
    "vehicleId": "sw_t_72m1",
    "zoneName": "hull_composite_armor",
    "impactAngle_deg": 30,
    "shellBulletName": "125mm_3bm42",
    "range_m": 500,
    "shellType": "ke"
  }'
```

`shellType` is `"ke"` for kinetic (APFSDS, APHE, etc.) or `"heat"` for chemical (HEAT-FS, ATGM).

---

## Adding Vehicles

Drop a `<vehicleId>.json` into `backend/data/vehicles/` and a corresponding `<cannonId>.json` into `backend/data/shells/`. The backend scans the directory on every request — no restart needed.

To generate these from raw game files use the converter scripts:

```bash
python converter/build_vehicle_json.py \
  --blk      extracted/sw_t_72m1.blk \
  --wpcost   extracted/wpcost.blk \
  --shop     extracted/shop.blk \
  --units    extracted/units.csv \
  --unittags extracted/unittags.blk \
  --cannon   extracted/2a46m.blk \
  --out-vehicles backend/data/vehicles \
  --out-shells   backend/data/shells
```

### Vehicle JSON schema (key fields)

```jsonc
{
  "vehicleId": "sw_t_72m1",
  "displayName": "T-72M1",
  "damageParts": {
    "hull": { "armorThickness": 60.0, "armorClass": "RHA_tank_modern", "variableThickness": true },
    "hull_composite_armor": {
      "_isGroup": true,
      "children": {
        "superstructure_front_dm": { "armorThickness": 60.0, "armorClass": "RHA_tank_modern" },
        "composite_armor_hull_01_dm": { "armorThickness": 100.0, "armorClass": "tank_textolite" }
      }
    }
  },
  "xrayViewerData": { ... },   // xrayTextThickness display labels
  "shells": ["2a46m"]          // cannon IDs to load
}
```

### Armor class multipliers (`armor_classes.json`)

| Class | KE | HEAT |
|-------|----|------|
| `RHA_tank_modern` | 1.00 | 1.00 |
| `tank_textolite` | 0.44 | 0.44 |
| `t_80b_composite_armor` | 0.07 | 0.30 |
| `ERA_tank` | 0.00 | 0.00 |
| `tank_traks` | 0.70 | 0.20 |

---

## Adding 3D Models

Place a `<modelId>.glb` in `backend/data/models/`. The frontend will load it from `/api/models/<modelId>.glb` automatically when the vehicle's `modelId` field is set. Mesh node names must match `damageParts` keys exactly.

To convert from game files:

```bash
python converter/grp_to_gltf.py path/to/vehicle.grp backend/data/models/
```

> The DAG binary parser in `grp_to_gltf.py` is a scaffold — the `dag_to_gltf_bytes()` function needs the Gaijin DAG format spec to be completed, or use Gaijin's own `dagor_sdk` toolchain to export glTF directly.

---

## Penetration Formula

```
effective_thickness = armor_thickness
                    × armor_class_multiplier[shell_type]
                    × generic_armor_quality
                    × LOS_multiplier(impact_angle)

LOS_multiplier = 1 / cos(angle)
               (capped at 2.0 for variableThickness zones — angle partially pre-baked)

total_effective = sum of all layer effective thicknesses (sequential, not parallel)
penetrated      = shell_pen > total_effective
```

HEAT-FS penetration is range-independent (`penetration_flat_mm`). APFSDS uses piecewise-linear interpolation over `penCurve` breakpoints.

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| Frontend | React 18, React Three Fiber, @react-three/drei, Zustand, Tailwind CSS |
| Build | Vite 6 |
| Container | Docker Compose (dev: hot-reload, prod: nginx static) |
| Data pipeline | Python 3, stdlib only |

---

## License

See [LICENSE](LICENSE).
