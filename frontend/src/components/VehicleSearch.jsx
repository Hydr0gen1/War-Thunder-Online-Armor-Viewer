import React, { useEffect, useState } from 'react'
import { useStore } from '../lib/store'
import { api } from '../lib/api'

export default function VehicleSearch() {
  const [query, setQuery] = useState('')
  const { vehicles, setVehicles, selectVehicle, selectedVehicleId } = useStore()

  useEffect(() => {
    api.listVehicles().then(setVehicles).catch(console.error)
  }, [])

  const filtered = vehicles.filter(
    (v) =>
      v.displayName.toLowerCase().includes(query.toLowerCase()) ||
      v.vehicleId.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Vehicle</h2>
      <input
        type="text"
        placeholder="Search vehicle..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-yellow-500"
      />
      <div className="flex flex-col gap-1 max-h-48 overflow-y-auto">
        {filtered.map((v) => (
          <button
            key={v.vehicleId}
            onClick={() => selectVehicle(v.vehicleId)}
            className={`text-left px-3 py-1.5 rounded text-sm transition-colors ${
              selectedVehicleId === v.vehicleId
                ? 'bg-yellow-600 text-black font-semibold'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            <span className="font-medium">{v.displayName}</span>
            <span className="text-xs ml-2 opacity-60">
              {v.nation} · BR {v.battleRating.realistic}
            </span>
          </button>
        ))}
        {filtered.length === 0 && (
          <p className="text-gray-500 text-sm px-2">No vehicles found</p>
        )}
      </div>
    </div>
  )
}
