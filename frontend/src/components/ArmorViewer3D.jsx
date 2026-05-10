import React, { useRef, useMemo, Suspense, useEffect } from 'react'
import { Canvas, useThree, useFrame } from '@react-three/fiber'
import { OrbitControls, useGLTF, Html } from '@react-three/drei'
import * as THREE from 'three'
import { useStore } from '../lib/store'
import { usePenetrationCalc } from '../hooks/usePenetrationCalc'

// ---------------------------------------------------------------------------
// Color helpers
// ---------------------------------------------------------------------------

function penColor(shellPen, effective, isNonArmor) {
  if (isNonArmor) return new THREE.Color(0x555555)
  if (shellPen === null || effective === null) return new THREE.Color(0x888888)
  const ratio = shellPen / effective
  if (ratio > 1.1) return new THREE.Color(0x22c55e) // green
  if (ratio > 0.85) return new THREE.Color(0xeab308) // yellow
  return new THREE.Color(0xef4444) // red
}

// ---------------------------------------------------------------------------
// Placeholder cube model — colored zones matched to T-72M1 armor layout
// ---------------------------------------------------------------------------

const PLACEHOLDER_ZONES = [
  { name: 'hull',                  pos: [0, -0.3, 0],  scale: [2.4, 0.8, 3.2] },
  { name: 'hull_composite_armor',  pos: [0, -0.3, 1.4], scale: [2.2, 0.7, 0.3] },
  { name: 'turret',                pos: [0,  0.55, 0.1], scale: [1.8, 0.65, 1.6] },
  { name: 'turret_composite_armor',pos: [0,  0.55, 0.8], scale: [1.6, 0.55, 0.25] },
  { name: 'tracks_l',              pos: [-1.4, -0.5, 0], scale: [0.25, 0.5, 3.2] },
  { name: 'tracks_r',              pos: [ 1.4, -0.5, 0], scale: [0.25, 0.5, 3.2] },
  { name: 'crew_driver_dm',        pos: [-0.4, -0.1, 0.8], scale: [0.35, 0.35, 0.35] },
  { name: 'ammo_dm',               pos: [0,   -0.3, -0.5], scale: [0.5, 0.4, 0.6] },
  { name: 'fuel_tank_dm',          pos: [0,   -0.5, -1.2], scale: [0.7, 0.3, 0.7] },
]

function PlaceholderMesh({ zone, color, isHighlighted, onClick }) {
  const meshRef = useRef()

  useFrame(() => {
    if (meshRef.current) {
      const target = isHighlighted ? 1.0 : 0.0
      const current = meshRef.current.material.emissiveIntensity
      meshRef.current.material.emissiveIntensity = THREE.MathUtils.lerp(current, target, 0.1)
    }
  })

  return (
    <mesh
      ref={meshRef}
      position={zone.pos}
      scale={zone.scale}
      onClick={(e) => { e.stopPropagation(); onClick(zone.name) }}
    >
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial
        color={color}
        emissive={new THREE.Color(0xffd700)}
        emissiveIntensity={0}
        transparent
        opacity={0.85}
        roughness={0.4}
        metalness={0.3}
      />
    </mesh>
  )
}

function VehicleModel({ armorData, penResult }) {
  const { checkZone } = usePenetrationCalc()
  const { highlightedZone, setHighlightedZone, selectedRound } = useStore()
  const damageParts = armorData?.damageParts || {}

  // Pre-compute shell pen at current range (client-side, for coloring)
  const shellPen = penResult?.shellPen_mm ?? null

  function getZoneEffective(zoneName) {
    if (!penResult || penResult.zoneName !== zoneName) return null
    return penResult.effectiveThickness_mm
  }

  function isNonArmor(zoneName) {
    const z = damageParts[zoneName]
    return !z || z._isModule || z._isCrew
  }

  return (
    <group>
      {PLACEHOLDER_ZONES.map((zone) => {
        const effective = getZoneEffective(zone.name)
        const nonArmor = isNonArmor(zone.name)
        const color = penColor(
          nonArmor ? null : shellPen,
          nonArmor ? null : effective,
          nonArmor
        )
        return (
          <PlaceholderMesh
            key={zone.name}
            zone={zone}
            color={color}
            isHighlighted={highlightedZone === zone.name}
            onClick={(name) => {
              setHighlightedZone(name)
              checkZone(name, 0)
            }}
          />
        )
      })}
    </group>
  )
}

function Scene({ armorData }) {
  const penResult = useStore((s) => s.penResult)
  const vehicleData = useStore((s) => s.vehicleData)

  // If a real GLB model exists for the vehicle, try to load it
  const modelId = vehicleData?.modelId
  const glbUrl = modelId ? `/api/models/${modelId}.glb` : null

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[5, 8, 5]} intensity={1.2} castShadow />
      <directionalLight position={[-3, 2, -4]} intensity={0.4} />

      <VehicleModel armorData={armorData} penResult={penResult} />

      <OrbitControls makeDefault enableDamping dampingFactor={0.08} />
      <gridHelper args={[20, 20, '#374151', '#1f2937']} position={[0, -1.0, 0]} />
    </>
  )
}

// ---------------------------------------------------------------------------
// Public component
// ---------------------------------------------------------------------------

export default function ArmorViewer3D() {
  const armorData = useStore((s) => s.armorData)
  const vehicleData = useStore((s) => s.vehicleData)

  return (
    <div className="relative w-full h-full bg-gray-950 rounded-lg overflow-hidden">
      <Canvas
        camera={{ position: [4, 2.5, 6], fov: 50 }}
        shadows
        gl={{ antialias: true }}
      >
        <Suspense fallback={null}>
          <Scene armorData={armorData} />
        </Suspense>
      </Canvas>

      {!vehicleData && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-gray-600 text-lg">Select a vehicle to begin</p>
        </div>
      )}

      <div className="absolute top-3 right-3 flex gap-2 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-green-500" /><span>Penetrates</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-yellow-500" /><span>Marginal</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-red-500" /><span>No pen</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-gray-500" /><span>Module/crew</span>
        </div>
      </div>
    </div>
  )
}
