import React, { useEffect } from 'react'
import { useStore } from './lib/store'
import { api } from './lib/api'
import VehicleSearch from './components/VehicleSearch'
import ArmorViewer3D from './components/ArmorViewer3D'
import ArmorZoneOverlay from './components/ArmorZoneOverlay'
import ShellSelector from './components/ShellSelector'
import PenResultHUD from './components/PenResultHUD'

export default function App() {
  const { selectedVehicleId, setVehicleData, setArmorData, toggleHidable, showHidableZones } = useStore()

  useEffect(() => {
    if (!selectedVehicleId) return
    Promise.all([
      api.getVehicle(selectedVehicleId),
      api.getVehicleArmor(selectedVehicleId),
    ])
      .then(([vehicle, armor]) => {
        setVehicleData(vehicle)
        setArmorData(armor)
      })
      .catch(console.error)
  }, [selectedVehicleId])

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left sidebar */}
      <aside className="w-72 flex-shrink-0 bg-gray-850 border-r border-gray-700 flex flex-col gap-6 p-4 overflow-y-auto" style={{ background: '#111827' }}>
        <div className="flex items-center gap-2">
          <div className="w-2 h-6 bg-yellow-500 rounded" />
          <h1 className="text-base font-bold tracking-tight">WT Armor Viewer</h1>
        </div>

        <VehicleSearch />
        <ShellSelector />

        <div className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Display</h2>
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showHidableZones}
              onChange={toggleHidable}
              className="accent-yellow-500"
            />
            Show ERA / composite overlays
          </label>
        </div>

        <ArmorZoneOverlay />
      </aside>

      {/* 3D viewer */}
      <main className="flex-1 relative">
        <ArmorViewer3D />
      </main>

      {/* Right sidebar */}
      <aside className="w-72 flex-shrink-0 border-l border-gray-700 flex flex-col gap-6 p-4 overflow-y-auto" style={{ background: '#111827' }}>
        <PenResultHUD />
      </aside>
    </div>
  )
}
