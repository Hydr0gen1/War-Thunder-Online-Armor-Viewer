import React from 'react'
import { useStore } from '../lib/store'
import { usePenetrationCalc } from '../hooks/usePenetrationCalc'

function flattenZones(damageParts) {
  const zones = []
  for (const [key, val] of Object.entries(damageParts)) {
    if (val._isModule || val._isCrew) continue
    zones.push({ name: key, isGroup: !!val._isGroup })
  }
  return zones
}

export default function ArmorZoneOverlay() {
  const { armorData, highlightedZone, setHighlightedZone } = useStore()
  const { checkZone } = usePenetrationCalc()

  if (!armorData) return null

  const zones = flattenZones(armorData.damageParts)

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Armor Zones</h2>
      <div className="flex flex-col gap-1 max-h-60 overflow-y-auto">
        {zones.map((z) => (
          <button
            key={z.name}
            onClick={() => {
              setHighlightedZone(z.name)
              checkZone(z.name, 0)
            }}
            className={`text-left px-3 py-1.5 rounded text-xs font-mono transition-colors ${
              highlightedZone === z.name
                ? 'bg-yellow-600 text-black'
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {z.isGroup && <span className="text-yellow-400 mr-1">[G]</span>}
            {z.name}
          </button>
        ))}
      </div>
    </div>
  )
}
