const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

async function request(path, options = {}) {
  const token = sessionStorage.getItem('autodb-token')
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message = typeof body === 'object' && body
      ? body.message || body.error || body.detail
      : body
    throw new Error(message || `Request failed (${response.status})`)
  }
  return body
}

// Proposed API contract. Align these paths and payloads with the backend team's actual routes.
export const api = {
  register: (payload) => request('/auth/register', { method: 'POST', body: JSON.stringify({ name: payload.name, email: payload.email, password: payload.password }) }),
  login: (payload) => request('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  customerDashboard: () => request('/customer/dashboard'),
  myServices: () => request('/customer/services'),
  createAppointment: (payload) => request('/appointments', { method: 'POST', body: JSON.stringify({ vehicle: payload.vehicle, service_type: payload.serviceType, preferred_date: payload.date, preferred_time: payload.time, description: payload.description }) }),
  adminDashboard: () => request('/admin/dashboard'),
  updateAppointment: (id, payload) => request(`/admin/appointments/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),
}
