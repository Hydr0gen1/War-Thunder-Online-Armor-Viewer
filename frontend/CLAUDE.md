# CLAUDE.md — frontend/

React 18 + React Three Fiber SPA. Dev server:

```bash
npm install
npm run dev      # http://localhost:3000
```

Vite proxies `/api/*` to `http://localhost:8000` in dev mode (see `vite.config.js`). In Docker, `VITE_API_BASE` is set to `http://backend:8000`.

## Component map

```
src/
  App.jsx                      Three-panel layout: sidebar | canvas | sidebar
  components/
    VehicleSearch.jsx           Loads vehicle list on mount, searchable
    ArmorViewer3D.jsx           R3F canvas — placeholder box model, zone coloring
    ArmorZoneOverlay.jsx        2D zone list, click triggers pen check + highlight
    ShellSelector.jsx           Ammo dropdown + range slider with client-side interpolation
    PenResultHUD.jsx            Last pen result + layer breakdown table
  hooks/
    usePenetrationCalc.js       Calls POST /api/penetration/check, writes to store
  lib/
    api.js                      Thin fetch wrappers for all backend endpoints
    store.js                    Zustand store — all shared state lives here
```

## State management (`lib/store.js`)

All cross-component state is in a single Zustand store. Key slices:

| Field | Type | Purpose |
|-------|------|---------|
| `selectedVehicleId` | `string\|null` | Which vehicle is loaded |
| `vehicleData` | `object\|null` | Full vehicle record from `/api/vehicles/{id}` |
| `armorData` | `object\|null` | damageParts + xrayViewerData |
| `allRounds` | `Round[]` | Merged rounds from all vehicle cannons |
| `selectedRound` | `Round\|null` | Active shell |
| `range_m` | `number` | Current range slider value (0–3000) |
| `highlightedZone` | `string\|null` | Zone name selected in overlay or by 3D click |
| `showHidableZones` | `boolean` | ERA/composite overlay visibility toggle |
| `penResult` | `PenCheckResponse\|null` | Last penetration check result |

Do not add component-local state for anything that two or more components need to share. Put it in the store.

## 3D viewer (`components/ArmorViewer3D.jsx`)

Currently uses placeholder box geometry (`PLACEHOLDER_ZONES` array) that approximates the T-72M1 layout. When a real `.glb` model is available:

1. Add a `useGLTF("/api/models/<modelId>.glb")` call
2. Traverse the scene graph and map mesh names to `damageParts` zone keys (1:1 by string)
3. Apply `MeshStandardMaterial` color per zone based on `penColor()` helper
4. Wire the `onClick` raycaster to call `checkZone(mesh.name)` and `setHighlightedZone(mesh.name)`

The `penColor()` function maps penetration ratio to green / yellow / red:
- `ratio > 1.1` → green (clear pen)
- `ratio > 0.85` → yellow (marginal)
- else → red (no pen)
- non-armor (module/crew) → grey

Zone highlighting uses `emissiveIntensity` animated via `useFrame` — do not use React state for per-frame animation values.

## Shell pen interpolation (client-side)

`ShellSelector.jsx` interpolates the pen curve client-side for the live slider display. This mirrors the backend logic in `services/penetration.py`. If the formula changes in the backend, update both places. The server is authoritative — the client interpolation is display-only.

## API calls (`lib/api.js`)

All fetch calls go through `api.*` helpers. The base URL is `import.meta.env.VITE_API_BASE || ''` — the empty string means "same origin", which works because Vite proxies `/api` in dev.

Do not use `fetch` directly in components. Route through `api.js`.

## Adding a new component

1. Create `src/components/MyComponent.jsx`
2. Use `useStore()` for any state that other components touch
3. Import into `App.jsx` or the parent that owns the layout slot
4. Do not add prop drilling for store values — use the store directly

## Tailwind

Dark theme: `bg-gray-900` body, `bg-gray-800` / `bg-gray-700` for panels and cards, `text-yellow-500` for accent. Check `tailwind.config.js` — content scanning covers `src/**/*.{js,jsx}`.

## Build for production

```bash
npm run build        # outputs to dist/
```

The `prod` stage in `Dockerfile` copies `dist/` into an nginx image. Not yet wired into `docker-compose.yml` (dev target is used). To switch: change `target: dev` → `target: prod` in `docker-compose.yml`.
