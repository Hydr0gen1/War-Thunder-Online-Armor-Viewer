import { useCallback } from 'react'
import { useStore } from '../lib/store'
import { api } from '../lib/api'

export function usePenetrationCalc() {
  const { selectedVehicleId, selectedRound, range_m, setPenResult } = useStore()

  const checkZone = useCallback(
    async (zoneName, impactAngle_deg = 0) => {
      if (!selectedVehicleId || !selectedRound) return

      // Determine shell type from bulletType string
      const bt = selectedRound.bulletType || ''
      const shellType = bt.includes('heat') ? 'heat' : 'ke'

      try {
        const result = await api.checkPenetration({
          vehicleId: selectedVehicleId,
          zoneName,
          impactAngle_deg,
          shellBulletName: selectedRound.bulletName,
          range_m,
          shellType,
        })
        setPenResult(result)
      } catch (e) {
        console.warn('Pen check failed:', e.message)
      }
    },
    [selectedVehicleId, selectedRound, range_m, setPenResult]
  )

  return { checkZone }
}
