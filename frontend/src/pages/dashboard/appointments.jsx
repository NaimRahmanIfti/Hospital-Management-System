// src/pages/dashboard/Appointments.jsx
import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { appointmentAPI, doctorAPI, authAPI } from "../../api/client"
import api from "../../api/client"
import useAuthStore from "../../store/authstore"
const statusColor = {
  scheduled: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
  no_show:   "bg-gray-100 text-gray-600",
}

// ── Doctor Card ────────────────────────────────────────────────
function DoctorCard({ doctor, selected, onSelect }) {
  return (
    <div
      onClick={() => onSelect(doctor)}
      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
        selected ? "border-teal-500 bg-teal-50" : "border-gray-100 bg-white hover:border-teal-200"
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center text-teal-700 font-bold text-sm flex-shrink-0">
          {doctor.user?.full_name?.charAt(0) || "D"}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 text-sm truncate">{doctor.user?.full_name}</p>
          <p className="text-xs text-teal-600">{doctor.specialization}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm font-semibold text-gray-900">${Number(doctor.consultation_fee).toFixed(0)}</p>
          <p className="text-xs text-gray-400">consult</p>
        </div>
      </div>
      {selected && (
        <div className="mt-2 pt-2 border-t border-teal-200">
          <p className="text-xs text-teal-700">✓ Selected — choose date & time below</p>
        </div>
      )}
    </div>
  )
}

// ── Cancel Modal ───────────────────────────────────────────────
function CancelModal({ appointment, onClose, onCancelled }) {
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")

  const handleCancel = async () => {
    setLoading(true)
    setError("")
    try {
      await appointmentAPI.cancel(appointment.id)
      onCancelled()
      onClose()
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(typeof detail === "string" ? detail : "Failed to cancel. Try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm z-10 p-6"
      >
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-red-600 text-xl font-bold">×</span>
          </div>
          <h2 className="font-semibold text-gray-900 text-lg">Cancel Appointment</h2>
          <p className="text-gray-500 text-sm mt-2">
            Are you sure you want to cancel your appointment with{" "}
            <span className="font-medium text-gray-900">
              {appointment.doctor_name || `Doctor #${appointment.doctor_id}`}
            </span>{" "}on{" "}
            <span className="font-medium text-gray-900">
              {new Date(appointment.scheduled_at).toLocaleString("en-US", {
                month: "short", day: "numeric",
                hour: "2-digit", minute: "2-digit"
              })}
            </span>?
          </p>
          <p className="text-red-500 text-xs mt-2">This action cannot be undone.</p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4 border border-red-100">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Keep it
          </button>
          <button
            onClick={handleCancel}
            disabled={loading}
            className="flex-1 py-2.5 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {loading ? "Cancelling..." : "Yes, cancel"}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Booking Modal ──────────────────────────────────────────────
function BookingModal({ onClose, onBooked }) {
  const { user }                      = useAuthStore()
  const [allDoctors,  setAllDoctors]  = useState([])
  const [doctors,     setDoctors]     = useState([])
  const [loadingDocs, setLoadingDocs] = useState(true)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState("")
  const [search,      setSearch]      = useState("")
  const [specFilter,  setSpecFilter]  = useState("All")
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [form, setForm] = useState({
    scheduled_at:     "",
    duration_minutes: 30,
    reason:           "",
  })

  useEffect(() => {
    doctorAPI.list()
      .then(r => { setAllDoctors(r.data); setDoctors(r.data) })
      .catch(() => setError("Could not load doctors. Is the backend running?"))
      .finally(() => setLoadingDocs(false))
  }, [])

  // Filter doctors
  useEffect(() => {
    let filtered = allDoctors
    if (specFilter !== "All") {
      filtered = filtered.filter(d =>
        d.specialization?.toLowerCase().includes(specFilter.toLowerCase())
      )
    }
    if (search.trim()) {
      filtered = filtered.filter(d =>
        d.user?.full_name?.toLowerCase().includes(search.toLowerCase()) ||
        d.specialization?.toLowerCase().includes(search.toLowerCase())
      )
    }
    setDoctors(filtered)
  }, [search, specFilter, allDoctors])

  const minDate = new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 16)

  // ── Get or create patient profile ─────────────────────────
  const getOrCreatePatientProfile = async () => {
    const token = localStorage.getItem("hms_token")
    const headers = {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${token}`,
    }

    // Get current user
    const meRes = await fetch("http://localhost:8000/auth/me", { headers })
    const meData = await meRes.json()

    if (meData.role !== "patient") return null

    // Try to get patient profile by searching all patients
    // Backend auto-creates based on JWT for the POST /appointments endpoint
    // But we need the patient_id to send in the request
    // So we create the profile if it doesn't exist
    try {
      const createRes = await fetch("http://localhost:8000/patients/", {
        method: "POST",
        headers,
        body: JSON.stringify({ user_id: meData.id }),
      })
      const created = await createRes.json()

      // If profile already exists, backend returns 409 or error
      // but we can extract patient_id from the error or from a fresh fetch
      if (createRes.ok) return created.id

      // Profile already exists — find it from appointments or try again
      // Use the known mapping from DB
      return null
    } catch(e) {
      return null
    }
  }

  const handleCreate = async () => {
    if (!form.patient_id) { setError("Patient ID is required."); return }
    if (form.items.some(i => !i.description || !i.unit_price)) {
      setError("All items need a description and price.")
      return
    }
    setLoading(true)
    setError("")
    try {
      await api.post("/invoices/", {
        patient_id:     Number(form.patient_id),
        appointment_id: form.appointment_id ? Number(form.appointment_id) : null,
        notes:          form.notes || null,
        // NO due_date — not in the model
        items: form.items.map(i => ({
          description: i.description,
          quantity:    Number(i.quantity) || 1,
          unit_price:  Number(i.unit_price),
        })),
      })
      setSuccess("✅ Invoice created! Patient can now see it.")
      setForm({
        appointment_id: "", patient_id: "", due_date: "", notes: "",
        items: [{ description: "", quantity: 1, unit_price: "" }],
      })
      onCreated()
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (typeof detail === "string") setError(detail)
      else if (Array.isArray(detail)) setError(detail.map(e => e.msg || JSON.stringify(e)).join(", "))
      else setError("Failed to create invoice.")
      console.error("Invoice error:", err?.response?.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg z-10 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white z-10">
          <h2 className="font-semibold text-gray-900">Book Appointment</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">×</button>
        </div>

        <div className="p-6 space-y-6">

          {/* Step 1 — Doctor */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-5 h-5 bg-teal-600 text-white rounded-full text-xs flex items-center justify-center font-bold">1</span>
              Choose a Doctor
            </h3>

            <div className="relative mb-3">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
              <input
                type="text"
                placeholder="Search by name or specialization..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="flex gap-2 flex-wrap mb-3">
              {["All","Cardiology","General Medicine","Neurology","Pediatrics","Dermatology"].map(s => (
                <button
                  key={s}
                  onClick={() => setSpecFilter(s)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                    specFilter === s
                      ? "bg-teal-600 text-white border-teal-600"
                      : "border-gray-200 text-gray-500 hover:border-teal-300"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
              {loadingDocs ? (
                <div className="text-center py-6 text-gray-400 text-sm">Loading doctors...</div>
              ) : doctors.length === 0 ? (
                <div className="text-center py-6 text-gray-400 text-sm">No doctors found.</div>
              ) : (
                doctors.map(d => (
                  <DoctorCard
                    key={d.id}
                    doctor={d}
                    selected={selectedDoc?.id === d.id}
                    onSelect={setSelectedDoc}
                  />
                ))
              )}
            </div>
          </div>

          {/* Step 2 — Date & Time */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-5 h-5 bg-teal-600 text-white rounded-full text-xs flex items-center justify-center font-bold">2</span>
              Date & Time
            </h3>
            <input
              type="datetime-local"
              min={minDate}
              value={form.scheduled_at}
              onChange={e => setForm({ ...form, scheduled_at: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          {/* Step 3 — Duration */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-5 h-5 bg-teal-600 text-white rounded-full text-xs flex items-center justify-center font-bold">3</span>
              Duration
            </h3>
            <div className="flex gap-2">
              {[15, 30, 45, 60].map(mins => (
                <button
                  key={mins}
                  onClick={() => setForm({ ...form, duration_minutes: mins })}
                  className={`flex-1 py-2 text-sm rounded-lg border transition-all ${
                    form.duration_minutes === mins
                      ? "bg-teal-600 text-white border-teal-600"
                      : "border-gray-200 text-gray-500 hover:border-teal-300"
                  }`}
                >
                  {mins}min
                </button>
              ))}
            </div>
          </div>

          {/* Step 4 — Reason */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span className="w-5 h-5 bg-teal-600 text-white rounded-full text-xs flex items-center justify-center font-bold">4</span>
              Reason
              <span className="text-gray-400 font-normal text-xs">(optional)</span>
            </h3>
            <textarea
              rows={2}
              placeholder="Describe your symptoms or reason for visit..."
              value={form.reason}
              onChange={e => setForm({ ...form, reason: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>

          {/* Booking summary */}
          {selectedDoc && form.scheduled_at && (
            <div className="bg-gray-50 rounded-xl p-4 text-sm space-y-1.5">
              <p className="font-medium text-gray-700 mb-2">Booking summary</p>
              <div className="flex justify-between text-gray-500">
                <span>Doctor</span>
                <span className="text-gray-900 font-medium">{selectedDoc.user?.full_name}</span>
              </div>
              <div className="flex justify-between text-gray-500">
                <span>Specialization</span>
                <span className="text-gray-900">{selectedDoc.specialization}</span>
              </div>
              <div className="flex justify-between text-gray-500">
                <span>Date & Time</span>
                <span className="text-gray-900">
                  {new Date(form.scheduled_at).toLocaleString("en-US", {
                    month: "short", day: "numeric",
                    hour: "2-digit", minute: "2-digit"
                  })}
                </span>
              </div>
              <div className="flex justify-between text-gray-500">
                <span>Duration</span>
                <span className="text-gray-900">{form.duration_minutes} min</span>
              </div>
              <div className="flex justify-between text-gray-500 border-t border-gray-200 pt-2 mt-2">
                <span>Consultation fee</span>
                <span className="text-teal-700 font-semibold">
                  ${Number(selectedDoc.consultation_fee).toFixed(2)}
                </span>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-100">
              {error}
            </div>
          )}

          <button
            onClick={handleBook}
            disabled={loading || !selectedDoc || !form.scheduled_at}
            className="w-full bg-teal-600 text-white py-3 rounded-xl font-medium hover:bg-teal-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading
              ? "Booking..."
              : `Confirm Appointment${selectedDoc ? ` with ${selectedDoc.user?.full_name}` : ""}`
            }
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Main Appointments Page ─────────────────────────────────────
export default function Appointments() {
  const { user }                        = useAuthStore()
  const [appointments, setAppointments] = useState([])
  const [loading,      setLoading]      = useState(true)
  const [filter,       setFilter]       = useState("all")
  const [showModal,    setShowModal]    = useState(false)
  const [cancelTarget, setCancelTarget] = useState(null)

  const loadAppointments = () => {
    setLoading(true)
    appointmentAPI.myAppointments()
      .then(r => setAppointments(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadAppointments() }, [])

  const filtered = filter === "all"
    ? appointments
    : appointments.filter(a => a.status === filter)

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
          <p className="text-gray-400 text-sm mt-1">{appointments.length} total</p>
        </div>
        {(user?.role === "patient" || user?.role === "admin") && (
          <button
            onClick={() => setShowModal(true)}
            className="bg-teal-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-teal-700 transition-colors flex items-center gap-2"
          >
            <span className="text-lg leading-none">+</span> Book Appointment
          </button>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {["all", "scheduled", "completed", "cancelled"].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all capitalize ${
              filter === s
                ? "bg-teal-600 text-white"
                : "bg-white border border-gray-200 text-gray-500 hover:border-teal-300"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-400 text-sm mb-4">No appointments found.</p>
            {user?.role === "patient" && (
              <button
                onClick={() => setShowModal(true)}
                className="bg-teal-600 text-white px-6 py-2 rounded-lg text-sm hover:bg-teal-700"
              >
                Book your first appointment
              </button>
            )}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-400 border-b border-gray-50">
                <th className="text-left px-6 py-3 font-medium">Patient</th>
                <th className="text-left px-6 py-3 font-medium">Doctor</th>
                <th className="text-left px-6 py-3 font-medium">Date & Time</th>
                <th className="text-left px-6 py-3 font-medium">Duration</th>
                <th className="text-left px-6 py-3 font-medium">Reason</th>
                <th className="text-left px-6 py-3 font-medium">Status</th>
                <th className="text-left px-6 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a, i) => (
                <motion.tr
                  key={a.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="border-b border-gray-50 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    {a.patient_name || `Patient #${a.patient_id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {a.doctor_name || `Doctor #${a.doctor_id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(a.scheduled_at).toLocaleString("en-US", {
                      month: "short", day: "numeric", year: "numeric",
                      hour: "2-digit", minute: "2-digit"
                    })}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{a.duration_minutes} min</td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {a.reason || "—"}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      statusColor[a.status] || "bg-gray-100 text-gray-600"
                    }`}>
                      {a.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {a.status === "scheduled" ? (
                      <button
                        onClick={() => setCancelTarget(a)}
                        className="text-xs px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors font-medium"
                      >
                        Cancel
                      </button>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modals */}
      <AnimatePresence>
        {showModal && (
          <BookingModal
            onClose={() => setShowModal(false)}
            onBooked={loadAppointments}
          />
        )}
        {cancelTarget && (
          <CancelModal
            appointment={cancelTarget}
            onClose={() => setCancelTarget(null)}
            onCancelled={loadAppointments}
          />
        )}
      </AnimatePresence>
    </div>
  )
}