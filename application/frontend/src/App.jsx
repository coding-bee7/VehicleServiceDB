import { useEffect, useRef, useState } from 'react'
import CarScene from './CarScene'
import './App.css'
import { api } from './services/api'

const services = [
  { number: '01', title: 'Routine Maintenance', description: 'Thoughtful care that keeps every journey running smoothly.', icon: '✳' },
  { number: '02', title: 'Engine & Diagnostics', description: 'Precision diagnostics for the details you cannot see.', icon: '⌁' },
  { number: '03', title: 'Premium Detailing', description: 'Restore the finish. Refine every surface.', icon: '◇' },
]

const initialBooking = { vehicle: '', serviceType: 'Routine Maintenance', date: '', time: '', description: '' }

function App() {
  const [page, setPage] = useState('home')
  const [authMode, setAuthMode] = useState('login')
  const [menuOpen, setMenuOpen] = useState(false)
  const [cursor, setCursor] = useState({ x: -30, y: -30 })
  const [user, setUser] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem('autodb-user') || 'null') } catch { return null }
  })
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [dashboard, setDashboard] = useState(null)
  const [appointments, setAppointments] = useState([])
  const [booking, setBooking] = useState(initialBooking)
  const cursorRef = useRef(null)

  const navigate = (nextPage) => {
    setPage(nextPage)
    setMenuOpen(false)
    setNotice('')
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const scrollTo = (id) => {
    if (page !== 'home') setPage('home')
    window.setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }), page === 'home' ? 0 : 60)
    setMenuOpen(false)
  }

  useEffect(() => {
    const finePointer = window.matchMedia('(pointer: fine)').matches
    if (!finePointer) return
    const moveCursor = (event) => {
      if (cursorRef.current) {
        cursorRef.current.style.left = `${event.clientX}px`
        cursorRef.current.style.top = `${event.clientY}px`
      }
    }
    window.addEventListener('pointermove', moveCursor)
    return () => window.removeEventListener('pointermove', moveCursor)
  }, [])

  useEffect(() => {
    if (!user || !['customer', 'admin'].includes(user.role)) return
    let active = true
    const load = async () => {
      try {
        const result = user.role === 'admin' ? await api.adminDashboard() : await api.customerDashboard()
        if (active) setDashboard(result)
      } catch (err) {
        if (active) setDashboard({ __error: err.message })
      }
    }
    load()
    return () => { active = false }
  }, [user])

  useEffect(() => {
    if (!user || user.role !== 'customer' || page !== 'my-services') return
    let active = true
    api.myServices().then((result) => {
      if (active) setAppointments(Array.isArray(result) ? result : result?.appointments || [])
    }).catch((err) => {
      if (active) setError(err.message)
    })
    return () => { active = false }
  }, [user, page])

  const handleAuth = async (event, form) => {
    event.preventDefault()
    setLoading(true); setError(''); setNotice('')
    try {
      const result = authMode === 'register' ? await api.register(form) : await api.login({ email: form.email, password: form.password })
      const token = result?.token || result?.access_token
      const account = result?.user || result?.account
      if (!account) throw new Error('The API response did not include a user object. Check the backend response contract.')
      if (token) sessionStorage.setItem('autodb-token', token)
      sessionStorage.setItem('autodb-user', JSON.stringify(account))
      setUser(account)
      navigate(account.role === 'admin' ? 'admin' : 'dashboard')
    } catch (err) { setError(err.message || 'Unable to authenticate. Please try again.') }
    finally { setLoading(false) }
  }

  const handleBooking = async (event) => {
    event.preventDefault(); setLoading(true); setError(''); setNotice('')
    try {
      const result = await api.createAppointment(booking)
      setNotice(result?.message || 'Your booking request was submitted.')
      setBooking(initialBooking)
    } catch (err) { setError(err.message || 'Could not submit your booking.') }
    finally { setLoading(false) }
  }

  const logout = () => {
    sessionStorage.removeItem('autodb-token')
    sessionStorage.removeItem('autodb-user')
    setUser(null); setDashboard(null); setAppointments([])
    navigate('home')
  }

  const requireCustomer = () => {
    if (!user) { setAuthMode('login'); navigate('auth'); return false }
    if (user.role !== 'customer') { navigate('admin'); return false }
    return true
  }

  if (page === 'home') return (
    <main className="autodb-home">
      <nav className="navbar">
        <a className="brand" href="#home" onClick={(e) => { e.preventDefault(); scrollTo('home') }} aria-label="AutoDB home">AUTO<span>DB</span><small>THE ART OF AUTOMOTIVE CARE</small></a>
        <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation" aria-expanded={menuOpen}>{menuOpen ? '✕' : '☰'}</button>
        <div className={`nav-links ${menuOpen ? 'nav-links-open' : ''}`}>
          <button onClick={() => scrollTo('services')}>OUR SERVICES</button>
          <button onClick={() => scrollTo('about')}>OUR PHILOSOPHY</button>
          <button className="nav-cta" onClick={() => { if (user) navigate('book'); else { setAuthMode('login'); navigate('auth') } }}>BOOK A SERVICE <span>↗</span></button>
          {user ? <button onClick={() => navigate(user.role === 'admin' ? 'admin' : 'dashboard')}>MY ACCOUNT</button> : <button onClick={() => { setAuthMode('login'); navigate('auth') }}>SIGN IN</button>}
        </div>
      </nav>

      <section className="hero" id="home">
        <div className="hero-image" aria-hidden="true" /><div className="hero-overlay" />
        <CarScene />
        <div className="hero-content">
          <p className="eyebrow hero-eyebrow"><span /> A HIGHER STANDARD OF CARE</p>
          <h1>Driven by<br /><em>excellence.</em></h1>
          <p className="hero-description">Exceptional vehicles deserve exceptional care. Discover a more considered approach to vehicle servicing and maintenance.</p>
          <div className="hero-actions"><button className="button button-light" onClick={() => scrollTo('services')}>EXPLORE OUR SERVICES <span>↗</span></button><button className="text-link" onClick={() => scrollTo('about')}>DISCOVER AUTODB <span>↓</span></button></div>
        </div>
        <div className="hero-caption"><span>CRAFTED FOR THE JOURNEY</span><span>01 / 03</span></div><div className="hero-side-note">PRECISION · CARE · CONFIDENCE</div>
      </section>

      <section className="intro section-pad" id="about"><div className="intro-label"><span className="section-index">01 — THE AUTODB APPROACH</span><span className="little-line" /></div><div className="intro-copy"><h2>More than maintenance.<br /><em>A standard of its own.</em></h2><div className="intro-bottom"><p>Your vehicle is more than a machine. It is engineering, craftsmanship and freedom in motion. We bring a considered, detail-first approach to keeping it at its best.</p><button className="round-link" onClick={() => scrollTo('services')} aria-label="Explore services">↘</button></div></div><div className="intro-watermark" aria-hidden="true">A.</div></section>

      <section className="services section-pad" id="services"><div className="section-heading"><div><span className="section-index">02 — WHAT WE DO</span><h2>Care, without<br /><em>compromise.</em></h2></div><p>The right expertise. The right attention. A seamless experience from booking to handover.</p></div><div className="service-grid">{services.map((service) => <article className="service-card" key={service.number}><div className="service-card-top"><span>{service.number}</span><span className="service-icon">{service.icon}</span></div><div><h3>{service.title}</h3><p>{service.description}</p></div><button className="service-arrow" onClick={() => { if (user) navigate('book'); else { setAuthMode('login'); navigate('auth') } }} aria-label={`Book ${service.title}`}>↗</button></article>)}</div><div className="services-cta"><p>Ready to give your vehicle the attention it deserves?</p><button className="button button-dark" onClick={() => { if (user) navigate('book'); else { setAuthMode('login'); navigate('auth') } }}>BOOK A SERVICE <span>↗</span></button></div></section>

      <section className="quote-section" id="contact"><div className="quote-mark">“</div><p>Great journeys begin with<br /><em>exceptional care.</em></p><span>YOUR VEHICLE. OUR ATTENTION.</span><button className="button button-dark" onClick={() => { if (user) navigate('book'); else { setAuthMode('login'); navigate('auth') } }}>ENQUIRE WITH AUTODB <span>↗</span></button></section>
      <Footer scrollTo={scrollTo} navigate={navigate} />
      <div className="custom-cursor" ref={cursorRef} aria-hidden="true"><span /></div>
    </main>
  )

  return (
    <main className="app-page">
      <AppNavbar user={user} navigate={navigate} logout={logout} menuOpen={menuOpen} setMenuOpen={setMenuOpen} />
      <div className="page-wrap">
        {page === 'auth' && <AuthPage mode={authMode} setMode={setAuthMode} onSubmit={handleAuth} loading={loading} error={error} />}
        {page === 'dashboard' && <CustomerDashboard user={user} data={dashboard} navigate={navigate} />}
        {page === 'book' && <BookService user={user} booking={booking} setBooking={setBooking} onSubmit={handleBooking} loading={loading} error={error} notice={notice} requireCustomer={requireCustomer} />}
        {page === 'my-services' && <MyServices appointments={appointments} error={error} navigate={navigate} />}
        {page === 'admin' && <AdminDashboard user={user} data={dashboard} navigate={navigate} />}
      </div>
      <Footer navigate={navigate} scrollTo={scrollTo} />
      <div className="custom-cursor" ref={cursorRef} aria-hidden="true"><span /></div>
    </main>
  )
}

function AppNavbar({ user, navigate, logout, menuOpen, setMenuOpen }) {
  return <nav className="app-navbar"><button className="brand app-brand" onClick={() => navigate('home')}>AUTO<span>DB</span><small>THE ART OF AUTOMOTIVE CARE</small></button><button className="menu-toggle app-menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">{menuOpen ? '✕' : '☰'}</button><div className={`app-nav-links ${menuOpen ? 'app-nav-links-open' : ''}`}><button onClick={() => navigate('home')}>HOME</button>{user?.role === 'customer' && <><button onClick={() => navigate('dashboard')}>DASHBOARD</button><button onClick={() => navigate('my-services')}>MY SERVICES</button><button className="nav-cta" onClick={() => navigate('book')}>BOOK A SERVICE ↗</button></>}{user?.role === 'admin' && <button onClick={() => navigate('admin')}>ADMIN OVERVIEW</button>}{user ? <button onClick={logout}>SIGN OUT</button> : <button onClick={() => navigate('auth')}>SIGN IN</button>}</div></nav>
}

function AuthPage({ mode, setMode, onSubmit, loading, error }) {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [localError, setLocalError] = useState('')
  const submit = (event) => {
    if (mode === 'register' && form.password !== form.confirmPassword) { event.preventDefault(); setLocalError('Your passwords do not match.'); return }
    setLocalError(''); onSubmit(event, form)
  }
  return <section className="auth-layout"><div className="auth-editorial"><span className="section-index">AUTODB MEMBERSHIP</span><h1>Care that<br /><em>knows your car.</em></h1><p>Manage your vehicle care with the same attention to detail that defines every AutoDB service.</p><div className="auth-rule" /><span className="auth-footnote">PRECISION · CARE · CONFIDENCE</span></div><div className="auth-card"><span className="section-index">{mode === 'login' ? 'WELCOME BACK' : 'BEGIN YOUR JOURNEY'}</span><h2>{mode === 'login' ? 'Sign in.' : 'Create your account.'}</h2><p className="muted">{mode === 'login' ? 'Access your appointments and service history.' : 'Set up your customer profile to book services.'}</p><form onSubmit={submit} className="form-stack">{mode === 'register' && <Field label="Full name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} placeholder="Your full name" required /> }<Field label="Email address" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} placeholder="you@example.com" required /><Field label="Password" type="password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} placeholder="Enter your password" required minLength={8} />{mode === 'register' && <Field label="Confirm password" type="password" value={form.confirmPassword} onChange={(v) => setForm({ ...form, confirmPassword: v })} placeholder="Repeat your password" required minLength={8} />}<p className="form-note">New accounts are registered as customers. Admin access is assigned by an administrator.</p>{(error || localError) && <p className="form-error" role="alert">{localError || error}</p>}<button className="button button-dark form-submit" disabled={loading}>{loading ? 'PLEASE WAIT…' : mode === 'login' ? 'SIGN IN' : 'CREATE ACCOUNT'} <span>↗</span></button></form><p className="auth-switch">{mode === 'login' ? 'New to AutoDB?' : 'Already have an account?'} <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login') }}> {mode === 'login' ? 'Create an account' : 'Sign in'}</button></p></div></section>
}

function CustomerDashboard({ user, data, navigate }) {
  const stats = data && !data.__error ? data : {}
  return <section className="dashboard-page"><PageHeading eyebrow="YOUR AUTODB" title={<>A considered approach<br /><em>to every journey.</em></>} description={`Welcome back${user?.name ? `, ${user.name.split(' ')[0]}` : ''}. Here's your vehicle care at a glance.`} action={<button className="button button-dark" onClick={() => navigate('book')}>BOOK A SERVICE <span>↗</span></button>} />
    {data?.__error && <ApiNotice text={`Dashboard data could not be loaded: ${data.__error}`} />}
    <div className="stat-grid"><Stat label="UPCOMING APPOINTMENTS" value={stats.upcomingAppointments ?? stats.upcoming_count ?? '—'} note="Your next scheduled visits"/><Stat label="REGISTERED VEHICLES" value={stats.vehicleCount ?? stats.vehicle_count ?? '—'} note="Vehicles linked to your account"/><Stat label="COMPLETED SERVICES" value={stats.completedServices ?? stats.completed_count ?? '—'} note="Your service history"/></div>
    <div className="dashboard-columns"><article className="panel"><div className="panel-heading"><div><span className="section-index">NEXT STEP</span><h3>Your next service</h3></div><span className="panel-symbol">↗</span></div><p className="muted">Your upcoming appointment details will appear here once the backend returns your booking data.</p><button className="text-action" onClick={() => navigate('my-services')}>VIEW MY SERVICES <span>→</span></button></article><article className="panel panel-dark"><span className="section-index">A LITTLE ATTENTION GOES A LONG WAY</span><h3>Keep your vehicle<br /><em>at its best.</em></h3><p>Book maintenance, diagnostics or detailing whenever your vehicle needs it.</p><button className="button button-light" onClick={() => navigate('book')}>SCHEDULE A SERVICE <span>↗</span></button></article></div>
  </section>
}

function BookService({ user, booking, setBooking, onSubmit, loading, error, notice, requireCustomer }) {
  if (!user) return <section className="simple-state"><span className="section-index">CUSTOMER ACCESS</span><h1>Sign in to book<br /><em>your service.</em></h1><button className="button button-dark" onClick={requireCustomer}>CONTINUE TO SIGN IN <span>↗</span></button></section>
  if (user.role !== 'customer') return <section className="simple-state"><h1>Booking is a customer feature.</h1><p>Use the admin overview to manage incoming appointments.</p></section>
  return <section className="form-page"><PageHeading eyebrow="APPOINTMENT REQUEST" title={<>Give your vehicle<br /><em>the right attention.</em></>} description="Tell us what your vehicle needs. Your request will be sent to AutoDB for scheduling."/><form className="booking-card form-stack" onSubmit={onSubmit}><div className="form-grid"><Field label="Vehicle (make / model / year)" value={booking.vehicle} onChange={(v) => setBooking({ ...booking, vehicle: v })} placeholder="e.g. Porsche 911 · 2022" required /><label className="field"><span>Service type</span><select value={booking.serviceType} onChange={(e) => setBooking({ ...booking, serviceType: e.target.value })}><option>Routine Maintenance</option><option>Engine & Diagnostics</option><option>Premium Detailing</option><option>General Inspection</option><option>Other</option></select></label><Field label="Preferred date" type="date" value={booking.date} onChange={(v) => setBooking({ ...booking, date: v })} required min={new Date().toISOString().slice(0, 10)} /><label className="field"><span>Preferred time</span><select value={booking.time} onChange={(e) => setBooking({ ...booking, time: e.target.value })} required><option value="">Choose a time</option><option>09:00</option><option>10:00</option><option>11:00</option><option>12:00</option><option>14:00</option><option>15:00</option><option>16:00</option></select></label></div><label className="field"><span>Tell us a little more (optional)</span><textarea rows="4" value={booking.description} onChange={(e) => setBooking({ ...booking, description: e.target.value })} placeholder="Describe any concerns or specific requests…" /></label>{error && <p className="form-error" role="alert">{error}</p>}{notice && <p className="form-success" role="status">{notice}</p>}<div className="form-submit-row"><p className="form-note">Your appointment is not confirmed until the service team reviews the request.</p><button className="button button-dark" disabled={loading}>{loading ? 'SUBMITTING…' : 'SUBMIT REQUEST'} <span>↗</span></button></div></form></section>
}

function MyServices({ appointments, error, navigate }) {
  return <section className="dashboard-page"><PageHeading eyebrow="YOUR VEHICLE CARE" title={<>Every service,<br /><em>thoughtfully tracked.</em></>} description="Review upcoming appointments and your maintenance history." action={<button className="button button-dark" onClick={() => navigate('book')}>NEW BOOKING <span>↗</span></button>} />{error && <ApiNotice text={error} />}<div className="table-panel"><div className="table-title"><div><span className="section-index">SERVICE RECORDS</span><h3>Appointments & history</h3></div><span className="muted">{appointments.length} records</span></div>{appointments.length ? <div className="responsive-table"><table><thead><tr><th>VEHICLE</th><th>SERVICE</th><th>DATE</th><th>STATUS</th></tr></thead><tbody>{appointments.map((item, index) => <tr key={item.id || index}><td>{item.vehicle || item.vehicle_name || '—'}</td><td>{item.serviceType || item.service_type || item.service || '—'}</td><td>{item.date || item.appointment_date || '—'}</td><td><StatusBadge status={item.status || 'Pending'} /></td></tr>)}</tbody></table></div> : <EmptyState title="Your service history will live here." body="Once appointments are returned by the backend, you’ll see booking status and completed service records on this page." action={() => navigate('book')} actionText="BOOK YOUR FIRST SERVICE" />}</div></section>
}

function AdminDashboard({ user, data, navigate }) {
  if (!user) return <section className="simple-state"><span className="section-index">RESTRICTED AREA</span><h1>Admin access<br /><em>required.</em></h1><p>Sign in with an administrator account to manage AutoDB.</p><button className="button button-dark" onClick={() => navigate('auth')}>SIGN IN <span>↗</span></button></section>
  if (user.role !== 'admin') return <section className="simple-state"><h1>Administrator access required.</h1><p>Your account does not have permission to view this area.</p><button className="button button-dark" onClick={() => navigate('dashboard')}>BACK TO MY DASHBOARD</button></section>
  const stats = data && !data.__error ? data : {}
  return <section className="dashboard-page"><PageHeading eyebrow="AUTODB OPERATIONS" title={<>Service, in<br /><em>good hands.</em></>} description="An overview for managing incoming requests and service operations." action={<span className="admin-role">ADMINISTRATOR</span>} />{data?.__error && <ApiNotice text={`Admin data could not be loaded: ${data.__error}`} />}<div className="stat-grid"><Stat label="TOTAL APPOINTMENTS" value={stats.totalAppointments ?? stats.total_appointments ?? '—'} note="All booking requests"/><Stat label="PENDING REQUESTS" value={stats.pendingAppointments ?? stats.pending_appointments ?? '—'} note="Awaiting review"/><Stat label="CUSTOMERS" value={stats.customerCount ?? stats.customer_count ?? '—'} note="Registered customer accounts"/></div><div className="table-panel"><div className="table-title"><div><span className="section-index">OPERATIONS</span><h3>Appointment management</h3></div><span className="muted">Live data requires the admin API</span></div>{Array.isArray(stats.appointments) && stats.appointments.length ? <div className="responsive-table"><table><thead><tr><th>CUSTOMER</th><th>VEHICLE</th><th>SERVICE</th><th>DATE</th><th>STATUS</th></tr></thead><tbody>{stats.appointments.map((item, index) => <tr key={item.id || index}><td>{item.customerName || item.customer_name || item.customer || '—'}</td><td>{item.vehicle || item.vehicle_name || '—'}</td><td>{item.serviceType || item.service_type || item.service || '—'}</td><td>{item.date || item.appointment_date || '—'}</td><td><StatusBadge status={item.status || 'Pending'} /></td></tr>)}</tbody></table></div> : <EmptyState title="Appointment requests will appear here." body="Connect the admin dashboard endpoint to populate this table. Status updates can be added to match your backend's appointment workflow." action={() => navigate('home')} actionText="VIEW PUBLIC HOMEPAGE" />}</div></section>
}

function Footer({ navigate, scrollTo }) {
  return <footer className="footer"><button className="brand footer-brand" onClick={() => navigate('home')}>AUTO<span>DB</span><small>THE ART OF AUTOMOTIVE CARE</small></button><p>Thoughtfully engineered for better journeys.</p><div className="footer-bottom"><span>© 2026 AUTODB</span><span>DESIGNED & DEVELOPED WITH CARE</span><button onClick={() => scrollTo('home')}>BACK TO TOP ↑</button></div></footer>
}
function PageHeading({ eyebrow, title, description, action }) { return <div className="page-heading"><div><span className="section-index">{eyebrow}</span><h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="page-heading-action">{action}</div>}</div> }
function Field({ label, value, onChange, type = 'text', placeholder, required, minLength, min }) { return <label className="field"><span>{label}</span><input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} required={required} minLength={minLength} min={min} /></label> }
function Stat({ label, value, note }) { return <article className="stat-card"><span className="section-index">{label}</span><strong>{value}</strong><p>{note}</p></article> }
function StatusBadge({ status }) { const value = String(status || 'pending'); return <span className={`status-badge status-${value.toLowerCase().replace(/[^a-z]+/g, '-')}`}>{value.replaceAll('_', ' ')}</span> }
function EmptyState({ title, body, action, actionText }) { return <div className="empty-state"><span className="empty-mark">A.</span><h4>{title}</h4><p>{body}</p>{action && <button className="text-action" onClick={action}>{actionText} <span>→</span></button>}</div> }
function ApiNotice({ text }) { return <div className="api-notice" role="status"><strong>Backend connection</strong><span>{text}</span><small>Confirm the API base URL and endpoint response shapes in <code>src/services/api.js</code>.</small></div> }

export default App
