import React from 'react'
import { useStore } from '../lib/store'

function PenBar({ shell, effective }) {
  const ratio = shell / (effective || 1)
  const pct = Math.min(ratio, 2) / 2 * 100
  const color = ratio > 1.1 ? 'bg-green-500' : ratio > 0.85 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="w-full bg-gray-700 rounded h-2 mt-1">
      <div className={`h-2 rounded ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function PenResultHUD() {
  const penResult = useStore((s) => s.penResult)

  if (!penResult) {
    return (
      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Penetration Result</h2>
        <p className="text-gray-500 text-sm">Click a zone to check penetration</p>
      </div>
    )
  }

  const { zoneName, nominalThickness_mm, effectiveThickness_mm, shellPen_mm, penetrated, marginMm, layers } = penResult
  const statusColor = penetrated ? 'text-green-400' : 'text-red-400'
  const statusText = penetrated ? 'PENETRATED' : 'NO PENETRATION'

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Penetration Result</h2>

      <div className="bg-gray-800 rounded p-3 flex flex-col gap-2">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-400 font-mono">{zoneName}</span>
          <span className={`text-sm font-bold ${statusColor}`}>{statusText}</span>
        </div>

        <PenBar shell={shellPen_mm} effective={effectiveThickness_mm} />

        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs mt-1">
          <span className="text-gray-400">Shell pen</span>
          <span className="text-right font-mono">{shellPen_mm} mm</span>
          <span className="text-gray-400">Effective armor</span>
          <span className="text-right font-mono">{effectiveThickness_mm} mm</span>
          <span className="text-gray-400">Nominal armor</span>
          <span className="text-right font-mono">{nominalThickness_mm} mm</span>
          <span className="text-gray-400">Margin</span>
          <span className={`text-right font-mono ${marginMm >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {marginMm >= 0 ? '+' : ''}{marginMm} mm
          </span>
        </div>
      </div>

      {layers.length > 1 && (
        <div className="flex flex-col gap-1">
          <h3 className="text-xs text-gray-400 uppercase tracking-wider">Layer Breakdown</h3>
          {layers.map((l, i) => (
            <div key={i} className="bg-gray-800 rounded px-3 py-2 text-xs flex justify-between items-center">
              <div>
                <div className="font-mono text-gray-200">{l.part}</div>
                <div className="text-gray-500">{l.armorClass}</div>
              </div>
              <div className="text-right">
                <div className="text-gray-200">{l.effective} mm eff</div>
                <div className="text-gray-500">{l.nominal} mm nom</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
