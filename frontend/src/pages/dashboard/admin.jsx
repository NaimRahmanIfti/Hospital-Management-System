// src/pages/dashboard/Admin.jsx
import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { patientAPI, doctorAPI, authAPI, invoiceAPI } from "../../api/client"
import api from "../../api/client"

// ── Create Invoice Modal ───────────────────────────────────────
function CreateInvoiceModal({ onClose, onCreated }) {
  const [appointments, setAppointments] = useState([])
  const [loading,      setLoading]      = useState(false)
  const [error,        setError]        = useState("")
  const [success,      setSuccess]      = useState("")
  const [form, setForm] = useState({
    appointment_id: "",
    patient_id:     "",
    due_date:       "",
    notes:          "",
    items: [{ description: "", quantity: 1, unit_price: "" }],
  })

  useEffect(() => {
    api.get("/appointments/my")
      .then(r => setAppointments(r.data))
      .catch(console.error)
  }, [])

  const addItem = () => {
    setForm({ ...form, items: [...form.items, { description: "", quantity: 1, unit_price: "" }] })
  }

  const updateItem = (index, field, value) => {
    const items = [...form.items]
    items[index] = { ...items[index], [field]: value }
    setForm({ ...form, items })
  }

  const removeItem = (index) => {
    setForm({ ...form, items: form.items.filter((_, i) => i !== index) })
  }

  const subtotal = form.items.reduce((sum, item) => {
    return sum + (Number(item.unit_price || 0) * Number(item.quantity || 1))
  }, 0)

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
        due_date:       form.due_date ? new Date(form.due_date).toISOString() : null,
        notes:          form.notes || null,
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
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg z-10 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="font-semibold text-gray-900">Create Invoice</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
        </div>

        <div className="p-6 space-y-4">
          {error   && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-100">{error}</div>}
          {success && <div className="bg-green-50 text-green-700 text-sm px-4 py-3 rounded-lg border border-green-100">{success}</div>}

          {/* Link to appointment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Link to Appointment <span className="text-gray-400 font-normal">(auto-fills patient)</span>
            </label>
            <select
              value={form.appointment_id}
              onChange={e => {
                const appt = appointments.find(a => a.id === Number(e.target.value))
                setForm({
                  ...form,
                  appointment_id: e.target.value,
                  patient_id: appt ? String(appt.patient_id) : form.patient_id,
                  items: appt ? [{
                    description: `Consultation - ${appt.reason || "Medical appointment"}`,
                    quantity: 1,
                    unit_price: "",
                  }] : form.items,
                })
              }}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="">Select appointment (optional)...</option>
              {appointments.map(a => (
                <option key={a.id} value={a.id}>
                  #{a.id} — Patient #{a.patient_id} — Dr #{a.doctor_id} —{" "}
                  {new Date(a.scheduled_at).toLocaleDateString()} — {a.status}
                </option>
              ))}
            </select>
          </div>

          {/* Patient ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Patient Profile ID <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              value={form.patient_id}
              onChange={e => setForm({ ...form, patient_id: e.target.value })}
              placeholder="Auto-filled from appointment, or enter manually"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          {/* Line items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Invoice Items <span className="text-red-400">*</span>
              </label>
              <button
                onClick={addItem}
                className="text-xs text-teal-600 hover:text-teal-700 font-medium"
              >
                + Add item
              </button>
            </div>

            <div className="space-y-2">
              {form.items.map((item, index) => (
                <div key={index} className="flex gap-2 items-start">
                  <input
                    type="text"
                    placeholder="Description *"
                    value={item.description}
                    onChange={e => updateItem(index, "description", e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  <input
                    type="number"
                    placeholder="Qty"
                    value={item.quantity}
                    onChange={e => updateItem(index, "quantity", e.target.value)}
                    className="w-16 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Price *"
                    value={item.unit_price}
                    onChange={e => updateItem(index, "unit_price", e.target.value)}
                    className="w-24 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  {form.items.length > 1 && (
                    <button
                      onClick={() => removeItem(index)}
                      className="text-red-400 hover:text-red-600 px-2 py-2 text-lg leading-none"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Subtotal preview */}
          {subtotal > 0 && (
            <div className="bg-teal-50 rounded-xl px-4 py-3 flex justify-between items-center">
              <span className="text-sm text-teal-700 font-medium">Total Amount</span>
              <span className="text-lg font-bold text-teal-800">${subtotal.toFixed(2)}</span>
            </div>
          )}

          {/* Due date
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Due Date <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="date"
              value={form.due_date}
              onChange={e => setForm({ ...form, due_date: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div> */}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Notes <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              rows={2}
              value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })}
              placeholder="Additional notes..."
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>

          <button
            onClick={handleCreate}
            disabled={loading || !form.patient_id}
            className="w-full bg-teal-600 text-white py-3 rounded-lg font-medium hover:bg-teal-700 disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Invoice"}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Update Invoice Modal ───────────────────────────────────────
function UpdateInvoiceModal({ invoice, onClose, onUpdated }) {
  const [status,  setStatus]  = useState(invoice.status || invoice.payment_status)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")

  const handleUpdate = async () => {
    setLoading(true)
    try {
      await api.patch(`/invoices/${invoice.id}`, { status })
      onUpdated()
      onClose()
    } catch(err) {
      setError("Failed to update invoice.")
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
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm z-10 p-6"
      >
        <h2 className="font-semibold text-gray-900 mb-1">Update Invoice #{invoice.id}</h2>
        <p className="text-sm text-gray-500 mb-4">
          Total: <span className="font-semibold text-gray-900">
            ${Number(invoice.total_amount || invoice.total || 0).toFixed(2)}
          </span>
        </p>

        {error && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">{error}</div>}

        <div className="space-y-2 mb-6">
          {[
            { value: "pending",  label: "⏳ Pending"  },
            { value: "paid",     label: "✅ Paid"      },
            { value: "partial",  label: "🔄 Partial"  },
            { value: "overdue",  label: "⚠️ Overdue"  },
            { value: "waived",   label: "🚫 Waived"   },
          ].map(s => (
            <button
              key={s.value}
              onClick={() => setStatus(s.value)}
              className={`w-full py-2.5 rounded-lg text-sm font-medium border transition-all ${
                status === s.value
                  ? "bg-teal-600 text-white border-teal-600"
                  : "border-gray-200 text-gray-500 hover:border-teal-300"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 py-2.5 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50">
            Cancel
          </button>
          <button
            onClick={handleUpdate}
            disabled={loading}
            className="flex-1 py-2.5 bg-teal-600 text-white rounded-xl text-sm font-medium hover:bg-teal-700 disabled:opacity-50"
          >
            {loading ? "Saving..." : "Update"}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Create User Modal ──────────────────────────────────────────
function CreateUserModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    full_name: "", email: "", password: "Hospital123",
    role: "patient", specialization: "General Medicine",
    license_number: "", consultation_fee: "100",
  })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")
  const [success, setSuccess] = useState("")

  const handleCreate = async () => {
    setLoading(true)
    setError("")
    setSuccess("")
    try {
      const { data: newUser } = await authAPI.register({
        full_name: form.full_name,
        email:     form.email,
        password:  form.password,
        role:      form.role,
      })
      // Patient profile is auto-created on registration.
      // Doctor profile must be created explicitly with admin token.
      if (form.role === "doctor") {
        await api.post("/doctors/", {
          user_id:          newUser.id,
          specialization:   form.specialization,
          license_number:   form.license_number || `LIC-${Date.now()}`,
          consultation_fee: Number(form.consultation_fee),
        })
      }
      setSuccess(`✅ ${form.role} account created for ${form.full_name}`)
      setForm({ ...form, full_name: "", email: "" })
      onCreated()
    } catch (err) {
      const d = err?.response?.data
      if (Array.isArray(d?.detail)) setError(d.detail.map(e => e.msg).join(", "))
      else setError(d?.detail || "Failed to create user")
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
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-md z-10 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Create New User</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
        </div>
        <div className="p-6 space-y-4">
          {error   && <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg">{error}</div>}
          {success && <div className="bg-green-50 text-green-700 text-sm px-4 py-3 rounded-lg">{success}</div>}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Role</label>
            <div className="grid grid-cols-3 gap-2">
              {["patient","doctor","admin"].map(r => (
                <button key={r} type="button" onClick={() => setForm({ ...form, role: r })}
                  className={`py-2 rounded-lg text-sm font-medium border capitalize transition-all ${
                    form.role === r ? "bg-teal-600 text-white border-teal-600" : "border-gray-200 text-gray-500 hover:border-teal-300"
                  }`}>
                  {r === "patient" ? "👤" : r === "doctor" ? "🩺" : "⚙️"} {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Full name</label>
            <input type="text" value={form.full_name}
              onChange={e => setForm({ ...form, full_name: e.target.value })}
              placeholder={form.role === "doctor" ? "Dr. Sarah Smith" : "Alice Johnson"}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
            <input type="email" value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder="user@hospital.com"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Password <span className="text-gray-400 text-xs">(default: Hospital123)</span>
            </label>
            <input type="text" value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          {form.role === "doctor" && (
            <div className="space-y-4 border-t border-gray-100 pt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Specialization</label>
                <select value={form.specialization}
                  onChange={e => setForm({ ...form, specialization: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  {["General Medicine","Cardiology","Neurology","Orthopedics",
                    "Pediatrics","Dermatology","Psychiatry","Oncology","Emergency Medicine"]
                    .map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">License #</label>
                  <input type="text" value={form.license_number}
                    onChange={e => setForm({ ...form, license_number: e.target.value })}
                    placeholder="MD-2024-001"
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Fee ($)</label>
                  <input type="number" value={form.consultation_fee}
                    onChange={e => setForm({ ...form, consultation_fee: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>
            </div>
          )}

          <button onClick={handleCreate} disabled={loading || !form.full_name || !form.email}
            className="w-full bg-teal-600 text-white py-3 rounded-lg font-medium hover:bg-teal-700 disabled:opacity-50">
            {loading ? "Creating..." : `Create ${form.role} account`}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Main Admin Page ────────────────────────────────────────────
export default function Admin() {
  const [patients,      setPatients]      = useState([])
  const [doctors,       setDoctors]       = useState([])
  const [invoices,      setInvoices]      = useState([])
  const [loading,       setLoading]       = useState(true)
  const [tab,           setTab]           = useState("patients")
  const [showUserModal, setShowUserModal] = useState(false)
  const [showInvModal,  setShowInvModal]  = useState(false)
  const [editInvoice,   setEditInvoice]   = useState(null)

  const loadAll = async () => {
    setLoading(true)
    try {
      const [p, d, i] = await Promise.allSettled([
        patientAPI.list(0, 100),
        doctorAPI.list(),
        api.get("/invoices/"),
      ])
      setPatients(p.value?.data || [])
      setDoctors(d.value?.data  || [])
      setInvoices(i.value?.data || [])
    } catch(e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { loadAll() }, [])

  const statusColor = {
    pending: "bg-amber-100 text-amber-700",
    paid:    "bg-green-100 text-green-700",
    partial: "bg-blue-100 text-blue-700",
    overdue: "bg-red-100 text-red-700",
    waived:  "bg-gray-100 text-gray-600",
  }

  const revenue = invoices
    .filter(i => i.status === "paid" || i.payment_status === "paid")
    .reduce((s, i) => s + Number(i.total_amount || i.total || 0), 0)

  const stats = [
    { label: "Total Patients", value: patients.length, icon: "👤", color: "bg-teal-50 text-teal-600"   },
    { label: "Total Doctors",  value: doctors.length,  icon: "🩺", color: "bg-blue-50 text-blue-600"   },
    { label: "Total Invoices", value: invoices.length, icon: "💳", color: "bg-amber-50 text-amber-600" },
    { label: "Revenue",        value: `$${revenue.toFixed(0)}`, icon: "💰", color: "bg-green-50 text-green-600" },
  ]

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-400 text-sm mt-1">Manage all hospital users and data</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowInvModal(true)}
            className="border border-teal-600 text-teal-600 px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-teal-50 flex items-center gap-2">
            💳 Create Invoice
          </button>
          <button onClick={() => setShowUserModal(true)}
            className="bg-teal-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-teal-700 flex items-center gap-2">
            + Create User
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }} className="bg-white rounded-2xl p-5 border border-gray-100">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg mb-4 ${s.color}`}>{s.icon}</div>
            <div className="text-2xl font-bold text-gray-900">{loading ? "—" : s.value}</div>
            <div className="text-sm text-gray-500 mt-0.5">{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {["patients","doctors","invoices"].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-full text-sm font-medium capitalize transition-all ${
              tab === t ? "bg-teal-600 text-white" : "bg-white border border-gray-200 text-gray-500 hover:border-teal-300"
            }`}>
            {t === "patients" ? `👤 Patients (${patients.length})` :
             t === "doctors"  ? `🩺 Doctors (${doctors.length})` :
                                `💳 Invoices (${invoices.length})`}
          </button>
        ))}
      </div>

      {/* Patients table */}
      {tab === "patients" && (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          {loading ? <div className="p-8 text-center text-gray-400">Loading...</div>
          : patients.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-400 text-sm mb-3">No patients yet.</p>
              <button onClick={() => setShowUserModal(true)} className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm">Create first patient</button>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-xs text-gray-400 border-b border-gray-50">
                  <th className="text-left px-6 py-3 font-medium">Name</th>
                  <th className="text-left px-6 py-3 font-medium">Email</th>
                  <th className="text-left px-6 py-3 font-medium">Blood Type</th>
                  <th className="text-left px-6 py-3 font-medium">Phone</th>
                  <th className="text-left px-6 py-3 font-medium">Gender</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((p, i) => (
                  <motion.tr key={p.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center text-teal-700 text-sm font-medium">
                          {p.user?.full_name?.charAt(0) || "?"}
                        </div>
                        <span className="text-sm font-medium text-gray-900">{p.user?.full_name || "—"}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{p.user?.email || "—"}</td>
                    <td className="px-6 py-4">
                      {p.blood_type
                        ? <span className="bg-red-50 text-red-600 text-xs px-2 py-1 rounded-full">{p.blood_type}</span>
                        : <span className="text-gray-300 text-sm">—</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{p.phone || "—"}</td>
                    <td className="px-6 py-4 text-sm text-gray-500 capitalize">{p.gender || "—"}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Doctors table */}
      {tab === "doctors" && (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          {loading ? <div className="p-8 text-center text-gray-400">Loading...</div>
          : doctors.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-400 text-sm mb-3">No doctors yet.</p>
              <button onClick={() => setShowUserModal(true)} className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm">Create first doctor</button>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-xs text-gray-400 border-b border-gray-50">
                  <th className="text-left px-6 py-3 font-medium">Name</th>
                  <th className="text-left px-6 py-3 font-medium">Email</th>
                  <th className="text-left px-6 py-3 font-medium">Specialization</th>
                  <th className="text-left px-6 py-3 font-medium">License</th>
                  <th className="text-left px-6 py-3 font-medium">Fee</th>
                </tr>
              </thead>
              <tbody>
                {doctors.map((d, i) => (
                  <motion.tr key={d.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 text-sm font-medium">
                          {d.user?.full_name?.charAt(0) || "D"}
                        </div>
                        <span className="text-sm font-medium text-gray-900">{d.user?.full_name || "—"}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{d.user?.email || "—"}</td>
                    <td className="px-6 py-4">
                      <span className="bg-teal-50 text-teal-700 text-xs px-2.5 py-1 rounded-full">{d.specialization}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">{d.license_number}</td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">${Number(d.consultation_fee).toFixed(2)}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Invoices table */}
      {tab === "invoices" && (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          {loading ? <div className="p-8 text-center text-gray-400">Loading...</div>
          : invoices.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-gray-400 text-sm mb-3">No invoices yet.</p>
              <button onClick={() => setShowInvModal(true)} className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm">Create first invoice</button>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-xs text-gray-400 border-b border-gray-50">
                  <th className="text-left px-6 py-3 font-medium">Invoice #</th>
                  <th className="text-left px-6 py-3 font-medium">Patient</th>
                  <th className="text-left px-6 py-3 font-medium">Date</th>
                  <th className="text-left px-6 py-3 font-medium">Total</th>
                  <th className="text-left px-6 py-3 font-medium">Status</th>
                  <th className="text-left px-6 py-3 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv, i) => (
                  <motion.tr key={inv.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">#{inv.id}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">Patient #{inv.patient_id}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(inv.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                      ${Number(inv.total_amount || inv.total || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                        statusColor[inv.status || inv.payment_status] || "bg-gray-100 text-gray-600"
                      }`}>
                        {inv.status || inv.payment_status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button onClick={() => setEditInvoice(inv)}
                        className="text-xs px-3 py-1.5 border border-teal-200 text-teal-600 rounded-lg hover:bg-teal-50 font-medium">
                        Update
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <AnimatePresence>
        {showUserModal && <CreateUserModal onClose={() => setShowUserModal(false)} onCreated={loadAll} />}
        {showInvModal  && <CreateInvoiceModal onClose={() => setShowInvModal(false)} onCreated={loadAll} />}
        {editInvoice   && <UpdateInvoiceModal invoice={editInvoice} onClose={() => setEditInvoice(null)} onUpdated={loadAll} />}
      </AnimatePresence>
    </div>
  )
}