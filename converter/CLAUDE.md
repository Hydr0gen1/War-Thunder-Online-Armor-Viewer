# CLAUDE.md — converter/

Standalone data pipeline scripts. **Not Dockerized.** Run directly with Python 3.10+. No external dependencies — stdlib only.

These scripts are the bridge between raw War Thunder game file extracts and the JSON schema consumed by the backend.

## Scripts

### `build_vehicle_json.py`

Assembles `backend/data/vehicles/<vehicleId>.json` and `backend/data/shells/<cannonId>.json` from raw extracted files.

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

**Source mapping:**

| Output field | Source file | Notes |
|---|---|---|
| `battleRating` | `wpcost.blk` | `BR = 1.0 + economicRankHistorical / 3.0` |
| `rank`, `nation`, `branch` | `shop.blk` | |
| `displayName` | `units.csv` | Strip leading `■` (export/captured marker) |
| `type`, `operatorCountry`, `shopArmor` | `unittags.blk` | |
| `damageParts` | `<vehicle>.blk` | `DamageParts {}` block |
| `xrayViewerData` | `<vehicle>.blk` | `xrayViewerData {}` block |
| Shell pen curves | `<cannon>.blk` | `ArmorPower<N>m` fields → `penCurve` |

**BR formula verification:** Tiger IIh `economicRankHistorical=17` → `1.0 + 17/3.0 = 6.67` → rounds to `6.7` ✓

**BLK format note:** The parser in `build_vehicle_json.py` handles text-format BLK. Binary BLK files must first be converted to text using Gaijin's `blk2json` tool (or equivalent). Pass the text output path as `--blk`.

**Shell `bulletType` → `shellType` mapping for pen checks:**

| `bulletType` contains | Use `shellType` |
|---|---|
| `heat` | `heat` |
| `atgm` | `heat` |
| anything else | `ke` |

This mapping lives in `frontend/src/hooks/usePenetrationCalc.js` — keep it in sync if new bullet types are added.

### `grp_to_gltf.py`

Converts GRP2 container files to glTF 2.0 `.glb` for use in the 3D viewer.

```bash
python converter/grp_to_gltf.py path/to/vehicle.grp backend/data/models/
```

**Status:** The GRP2 container parser (magic bytes `GRP2`, asset name + size + bytes layout) is implemented. The `dag_to_gltf_bytes()` function that converts the extracted DAG geometry to glTF is a **stub** — it raises `NotImplementedError`.

To complete it you need either:
- The Gaijin DAG binary format spec, or
- Use Gaijin's `dagor_sdk` toolchain to export glTF directly, and skip this script entirely

**Critical constraint:** Mesh/node names in the output `.glb` must exactly match the `damageParts` zone keys in the vehicle JSON. The viewer maps zone names to meshes by string equality — no lookup table.

**Which sub-asset to use:** The `*_xray_skeleton` DAG inside the GRP2 is the low-poly mesh the in-game viewer uses. Do **not** use `*_collision` (physics mesh, wrong topology) or the main skeleton (full-quality render, too heavy).

## Data schema reference

Both scripts produce files conforming to the schemas in `backend/models/schemas.py`. If the schema changes, update the converter output to match. The canonical example files are:

- `backend/data/vehicles/sw_t_72m1.json`
- `backend/data/shells/2a46m.json`

## Testing converter output

After running `build_vehicle_json.py`, verify the output loads correctly:

```bash
DATA_DIR=backend/data PYTHONPATH=backend python3 -c "
from routers.vehicles import _load_vehicle
print(_load_vehicle('sw_t_72m1'))
"
```

Or just hit the running API:

```bash
curl http://localhost:8000/api/vehicles/sw_t_72m1 | python3 -m json.tool
```
