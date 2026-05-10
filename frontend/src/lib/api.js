const BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  return res.json()
}

export const api = {
  listVehicles: () => request('/api/vehicles'),
  getVehicle: (id) => request(`/api/vehicles/${id}`),
  getVehicleArmor: (id) => request(`/api/vehicles/${id}/armor`),
  getShells: (cannonId) => request(`/api/shells/${cannonId}`),

  checkPenetration: (body) =>
    request('/api/penetration/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
}
