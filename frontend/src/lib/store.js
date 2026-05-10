import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // Vehicle
  vehicles: [],
  selectedVehicleId: null,
  vehicleData: null,
  armorData: null,

  // Shell selection
  allRounds: [],       // flat list across all cannons
  selectedRound: null,
  range_m: 500,

  // Viewer state
  highlightedZone: null,
  showHidableZones: true,
  penResult: null,

  setVehicles: (vehicles) => set({ vehicles }),
  selectVehicle: (id) => set({ selectedVehicleId: id, vehicleData: null, armorData: null, penResult: null }),
  setVehicleData: (d) => set({ vehicleData: d }),
  setArmorData: (d) => set({ armorData: d }),
  setAllRounds: (rounds) => set({ allRounds: rounds, selectedRound: rounds[0] || null }),
  selectRound: (round) => set({ selectedRound: round }),
  setRange: (r) => set({ range_m: r }),
  setHighlightedZone: (zone) => set({ highlightedZone: zone }),
  toggleHidable: () => set((s) => ({ showHidableZones: !s.showHidableZones })),
  setPenResult: (result) => set({ penResult: result }),
}))
