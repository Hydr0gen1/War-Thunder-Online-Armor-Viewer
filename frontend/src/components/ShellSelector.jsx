import React, { useEffect } from 'react'
import { useStore } from '../lib/store'
import { api } from '../lib/api'

function interpolatePen(round, range) {
  if (!round) return null
  const curve = round.penCurve
  if (!curve || curve.length === 0) return round.penetration_flat_mm ?? null
  if (range <= curve[0].range_m) return curve[0].pen_mm
  if (range >= curve[curve.length - 1].range_m) return curve[curve.length - 1].pen_mm
  for (let i = 0; i < curve.length - 1; i++) {
    const { range_m: r0, pen_mm: p0 } = curve[i]
    const { range_m: r1, pen_mm: p1 } = curve[i + 1]
    if (range >= r0 && range <= r1) {
      const t = (range - r0) / (r1 - r0)
      return Math.round(p0 + t * (p1 - p0))
    }
  }
  return curve[curve.length - 1].pen_mm
}

export default function ShellSelector() {
  const { vehicleData, allRounds, selectedRound, range_m, setAllRounds, selectRound, setRange } = useStore()

  useEffect(() => {
    if (!vehicleData) return
    const cannons = vehicleData.shells || []
    Promise.all(cannons.map((c) => api.getShells(c)))
      .then((results) => {
        const rounds = results.flatMap((r) => r.rounds)
        setAllRounds(rounds)
      })
      .catch(console.error)
  }, [vehicleData])

  const currentPen = interpolatePen(selectedRound, range_m)

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Ammunition</h2>

      {allRounds.length === 0 ? (
        <p className="text-gray-500 text-sm">Select a vehicle first</p>
      ) : (
        <>
          <select
            value={selectedRound?.bulletName || ''}
            onChange={(e) => {
              const r = allRounds.find((x) => x.bulletName === e.target.value)
              selectRound(r)
            }}
            className="bg-gray-700 border border-gray-600 rounded px-2 py-1.5 text-sm focus:outline-none focus:border-yellow-500"
          >
            {allRounds.map((r) => (
              <option key={r.bulletName} value={r.bulletName}>
                {r.displayName} ({r.bulletType})
              </option>
            ))}
          </select>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs text-gray-400">
              <span>Range: {range_m} m</span>
              {currentPen !== null && (
                <span className="text-yellow-400 font-semibold">{currentPen} mm pen</span>
              )}
            </div>
            <input
              type="range"
              min={0}
              max={3000}
              step={50}
              value={range_m}
              onChange={(e) => setRange(Number(e.target.value))}
              className="w-full accent-yellow-500"
            />
            <div className="flex justify-between text-xs text-gray-600">
              <span>0 m</span>
              <span>3000 m</span>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
