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

  register: (payload) =>
  request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      Name: payload.name ?? payload.Name,
      Phone: payload.phone ?? payload.Phone,
      Email: payload.email ?? payload.Email,
      Password: payload.password ?? payload.Password,
      ...(payload.address || payload.Address
        ? { Address: payload.address ?? payload.Address }
        : {}),
    }),
  }),

  login: (payload) =>
  request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({
      Email: payload.email ?? payload.Email,
      Password: payload.password ?? payload.Password,
    }),
  }),

  
customerDashboard: () => request('/customer/dashboard'),
nextAppointment: () => request('/customer/next-appointment'),
myServices: () => request('/customer/services'),
myVehicles: () => request('/customer/vehicles'),

// Customer invoices
myInvoices: () => request('/customer/invoices'),
myInvoiceDetails: (invoiceId) =>
  request(`/customer/invoices/${encodeURIComponent(invoiceId)}`),

createVehicle: (payload) =>
  request('/customer/vehicles', {
    method: 'POST',
    body: JSON.stringify({
      RegistrationNo: payload.registrationNo.trim().toUpperCase(),
      Brand: payload.brand.trim(),
      Model: payload.model.trim(),
      ManufactureYear: payload.manufactureYear
        ? Number(payload.manufactureYear)
        : null,
      FuelType: payload.fuelType || null,
    }),
  }),

mechanicServices: () => request('/mechanic/services'),

startService: (id) =>
  request(`/services/${encodeURIComponent(id)}/start`, {
    method: 'POST',
  }),

completeService: (id) =>
  request(`/services/${encodeURIComponent(id)}/complete`, {
    method: 'POST',
  }),
  
createAppointment: (payload) =>
  request('/appointments', {
    method: 'POST',
    body: JSON.stringify({
      vehicle_id: Number(payload.vehicle_id),
      appointment_date: `${payload.date}T${payload.time}`,
      complaint: payload.description || '',
    }),
  }),
  
adminDashboard: () => request('/admin/dashboard'),

adminAppointments: () => request('/admin/appointments'),

adminMechanics: () => request('/admin/mechanics'),

assignMechanic: (appointmentId, mechanicId) =>
  request(
    `/admin/appointments/${encodeURIComponent(appointmentId)}/assign`,
    {
      method: 'PATCH',
      body: JSON.stringify({ MechanicID: Number(mechanicId) }),
    }
  ),

updateAppointment: (id, payload) =>
  request(`/admin/appointments/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  }),


  
  createStaff: (payload) =>
    request('/admin/staff', {
      method: 'POST',
      body: JSON.stringify({
        Name: payload.name.trim(),
        Email: payload.email.trim().toLowerCase(),
        Phone: payload.phone.trim(),
        Role: 'Mechanic',
        Password: payload.password,
      }),
    }),


  // Invoice and payment APIs
  invoices: () => request('/invoices'),
  invoiceDetails: (invoiceId) =>
  request(`/invoices/${encodeURIComponent(invoiceId)}`),
  payments: () => request('/payments'),
  recordPayment: (invoiceId, payload) =>
    request(`/invoices/${encodeURIComponent(invoiceId)}/payments`, {
      method: 'POST',
      body: JSON.stringify({
        Amount: payload.amount,
        PaymentMethod: payload.paymentMethod,
      }),
    }),
}

