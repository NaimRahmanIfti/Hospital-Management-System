// src/pages/dashboard/MedicalRecords.jsx
import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { medicalRecordAPI, appointmentAPI } from "../../api/client"
import useAuthStore from "../../store/authstore"
import api from "../../api/client"

// ── Create Medical Record Modal ────────────────────────────────
function CreateRecordModal({ onClose, onCreated }) {
  const { user } = useAuthStore()
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    appointment_id: "",
    patient_id: "",
    doctor_id: "",
    diagnosis: "",
    symptoms: "",
    treatment: "",
    follow_up_date: "",
  })

  useEffect(() => {
    // Load doctor's completed appointments
    appointmentAPI.myAppointments()
      .then(r => {
        const completed = r.data.filter(a =>
          a.status === "scheduled" || a.status === "completed"
        )
        setAppointments(completed)
      })
      .catch(console.error)
  }, [])

  const handleAppointmentSelect = (appt) => {
    setForm({
      ...form,
      appointment_id: appt.id,
      patient_id: appt.patient_id,
      doctor_id: appt.doctor_id,
    })
  }

  const handleSubmit = async () => {
    if (!form.patient_id || !form.doctor_id) {
      setError("Please select an appointment first.")
      return
    }
    if (!form.diagnosis) {
      setError("Diagnosis is required.")
      return
    }
    setLoading(true)
    setError("")
    try {
      await api.post("/medical-records/", {
        patient_id:     form.patient_id,
        doctor_id:      form.doctor_id,
        appointment_id: form.appointment_id || null,
        diagnosis:      form.diagnosis,
        symptoms:       form.symptoms || null,
        treatment:      form.treatment || null,
        follow_up_date: form.follow_up_date
          ? new Date(form.follow_up_date).toISOString()
          : null,
      })
      onCreated()
      onClose()
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (typeof detail === "string") setError(detail)
      else if (Array.isArray(detail)) setError(detail.map(e => e.msg).join(", "))
      else setError("Failed to create medical record.")
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
          <h2 className="font-semibold text-gray-900">Create Medical Record</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-100">
              {error}
            </div>
          )}

          {/* Select appointment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Link to Appointment
            </label>
            <select
              value={form.appointment_id}
              onChange={e => {
                const appt = appointments.find(a => a.id === Number(e.target.value))
                if (appt) handleAppointmentSelect(appt)
              }}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="">Select appointment...</option>
              {appointments.map(a => (
                <option key={a.id} value={a.id}>
                  Patient #{a.patient_id} —{" "}
                  {new Date(a.scheduled_at).toLocaleDateString()} —{" "}
                  {a.reason || "No reason given"}
                </option>
              ))}
            </select>
          </div>

          {/* Symptoms */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Symptoms
            </label>
            <textarea
              rows={2}
              placeholder="Patient reported symptoms..."
              value={form.symptoms}
              onChange={e => setForm({ ...form, symptoms: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>

          {/* Diagnosis */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Diagnosis <span className="text-red-400">*</span>
            </label>
            <textarea
              rows={2}
              placeholder="Clinical diagnosis..."
              value={form.diagnosis}
              onChange={e => setForm({ ...form, diagnosis: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>

          {/* Treatment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Treatment Plan
            </label>
            <textarea
              rows={2}
              placeholder="Recommended treatment..."
              value={form.treatment}
              onChange={e => setForm({ ...form, treatment: e.target.value })}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>

          {/* Follow up */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Follow-up Date <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="date"
              value={form.follow_up_date}
              onChange={e => setForm({ ...form, follow_up_date: e.target.value })}
              min={new Date().toISOString().split("T")[0]}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-teal-600 text-white py-3 rounded-xl font-medium hover:bg-teal-700 transition-colors disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Medical Record"}
          </button>
        </div>
      </motion.div>
    </div>
  )
}

// ── Record Detail Modal ────────────────────────────────────────
function RecordDetailModal({ record, onClose, onUpdated }) {
  const { user } = useAuthStore()
  const [showPrescriptionForm, setShowPrescriptionForm] = useState(false)
  const [showLabForm, setShowLabForm] = useState(false)
  const [rxForm, setRxForm] = useState({
    medication_name: "", dosage: "", frequency: "", duration: "", instructions: ""
  })
  const [labForm, setLabForm] = useState({ test_name: "", test_code: "" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleAddPrescription = async () => {
    if (!rxForm.medication_name || !rxForm.dosage || !rxForm.frequency) {
      setError("Medication name, dosage and frequency are required.")
      return
    }
    setLoading(true)
    setError("")
    try {
      await api.post(`/medical-records/${record.id}/prescriptions`, {
        medical_record_id: record.id,
        doctor_id: record.doctor_id,
        ...rxForm,
      })
      setRxForm({ medication_name: "", dosage: "", frequency: "", duration: "", instructions: "" })
      setShowPrescriptionForm(false)
      onUpdated()
    } catch (err) {
      setError("Failed to add prescription.")
    } finally {
      setLoading(false)
    }
  }

  const handleOrderLab = async () => {
    if (!labForm.test_name) { setError("Test name is required."); return }
    setLoading(true)
    setError("")
    try {
      await api.post(`/medical-records/${record.id}/lab-results`, {
        medical_record_id: record.id,
        ...labForm,
      })
      setLabForm({ test_name: "", test_code: "" })
      setShowLabForm(false)
      onUpdated()
    } catch (err) {
      setError("Failed to order lab test.")
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
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-2xl z-10 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white">
          <div>
            <h2 className="font-semibold text-gray-900">Medical Record #{record.id}</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {new Date(record.created_at).toLocaleDateString("en-US", {
                month: "long", day: "numeric", year: "numeric"
              })}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
        </div>

        <div className="p-6 space-y-6">

          {/* Clinical info */}
          <div className="grid grid-cols-1 gap-4">
            {[
              { label: "Symptoms",      value: record.symptoms   },
              { label: "Diagnosis",     value: record.diagnosis  },
              { label: "Treatment",     value: record.treatment  },
            ].map(f => f.value && (
              <div key={f.label} className="bg-gray-50 rounded-xl p-4">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">{f.label}</p>
                <p className="text-sm text-gray-900">{f.value}</p>
              </div>
            ))}
            {record.follow_up_date && (
              <div className="bg-teal-50 rounded-xl p-4">
                <p className="text-xs font-medium text-teal-600 uppercase tracking-wide mb-1">Follow-up</p>
                <p className="text-sm text-teal-900">
                  {new Date(record.follow_up_date).toLocaleDateString("en-US", {
                    month: "long", day: "numeric", year: "numeric"
                  })}
                </p>
              </div>
            )}
          </div>

          {/* Prescriptions */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 text-sm">💊 Prescriptions</h3>
              {user?.role === "doctor" && (
                <button
                  onClick={() => setShowPrescriptionForm(!showPrescriptionForm)}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium"
                >
                  + Add prescription
                </button>
              )}
            </div>

            {showPrescriptionForm && (
              <div className="bg-gray-50 rounded-xl p-4 mb-3 space-y-3">
                {error && <p className="text-red-600 text-xs">{error}</p>}
                <div className="grid grid-cols-2 gap-3">
                  <input
                    placeholder="Medication name *"
                    value={rxForm.medication_name}
                    onChange={e => setRxForm({ ...rxForm, medication_name: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  <input
                    placeholder="Dosage * (e.g. 10mg)"
                    value={rxForm.dosage}
                    onChange={e => setRxForm({ ...rxForm, dosage: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  <input
                    placeholder="Frequency * (e.g. twice daily)"
                    value={rxForm.frequency}
                    onChange={e => setRxForm({ ...rxForm, frequency: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  <input
                    placeholder="Duration (e.g. 7 days)"
                    value={rxForm.duration}
                    onChange={e => setRxForm({ ...rxForm, duration: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <input
                  placeholder="Instructions (e.g. take with food)"
                  value={rxForm.instructions}
                  onChange={e => setRxForm({ ...rxForm, instructions: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddPrescription}
                    disabled={loading}
                    className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-teal-700 disabled:opacity-50"
                  >
                    {loading ? "Adding..." : "Add"}
                  </button>
                  <button
                    onClick={() => setShowPrescriptionForm(false)}
                    className="border border-gray-200 text-gray-500 px-4 py-2 rounded-lg text-sm hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {record.prescriptions?.length === 0 ? (
              <p className="text-gray-400 text-sm">No prescriptions yet.</p>
            ) : (
              <div className="space-y-2">
                {record.prescriptions?.map(rx => (
                  <div key={rx.id} className="bg-white border border-gray-100 rounded-xl p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{rx.medication_name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {rx.dosage} · {rx.frequency}
                          {rx.duration && ` · ${rx.duration}`}
                        </p>
                        {rx.instructions && (
                          <p className="text-xs text-teal-600 mt-1">ℹ {rx.instructions}</p>
                        )}
                      </div>
                      <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full">
                        Active
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Lab Results */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 text-sm">🔬 Lab Results</h3>
              {user?.role === "doctor" && (
                <button
                  onClick={() => setShowLabForm(!showLabForm)}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium"
                >
                  + Order test
                </button>
              )}
            </div>

            {showLabForm && (
              <div className="bg-gray-50 rounded-xl p-4 mb-3 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    placeholder="Test name * (e.g. CBC)"
                    value={labForm.test_name}
                    onChange={e => setLabForm({ ...labForm, test_name: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                  <input
                    placeholder="Test code (e.g. CBC-001)"
                    value={labForm.test_code}
                    onChange={e => setLabForm({ ...labForm, test_code: e.target.value })}
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleOrderLab}
                    disabled={loading}
                    className="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-teal-700 disabled:opacity-50"
                  >
                    {loading ? "Ordering..." : "Order Test"}
                  </button>
                  <button
                    onClick={() => setShowLabForm(false)}
                    className="border border-gray-200 text-gray-500 px-4 py-2 rounded-lg text-sm hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {record.lab_results?.length === 0 ? (
              <p className="text-gray-400 text-sm">No lab tests ordered.</p>
            ) : (
              <div className="space-y-2">
                {record.lab_results?.map(lab => (
                  <div key={lab.id} className="bg-white border border-gray-100 rounded-xl p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900 text-sm">{lab.test_name}</p>
                        {lab.test_code && (
                          <p className="text-xs text-gray-400 mt-0.5">Code: {lab.test_code}</p>
                        )}
                        {lab.result_value && (
                          <p className="text-xs text-gray-600 mt-1">Result: {lab.result_value}</p>
                        )}
                        {lab.normal_range && (
                          <p className="text-xs text-gray-400">Normal: {lab.normal_range}</p>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                        lab.status === "completed" ? "bg-green-100 text-green-700" :
                        lab.status === "pending"   ? "bg-amber-100 text-amber-700" :
                                                     "bg-gray-100 text-gray-600"
                      }`}>
                        {lab.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}

// ── Main Medical Records Page ──────────────────────────────────
export default function MedicalRecords() {
  const { user }                        = useAuthStore()
  const [records,     setRecords]       = useState([])
  const [loading,     setLoading]       = useState(true)
  const [showCreate,  setShowCreate]    = useState(false)
  const [selected,    setSelected]      = useState(null)

  const loadRecords = () => {
    setLoading(true)
    api.get("/medical-records/my")
      .then(r => setRecords(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const loadSelected = async () => {
    if (!selected) return
    try {
      const r = await api.get(`/medical-records/${selected.id}`)
      setSelected(r.data)
      loadRecords()
    } catch(e) { console.error(e) }
  }

  useEffect(() => { loadRecords() }, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Medical Records</h1>
          <p className="text-gray-400 text-sm mt-1">{records.length} records</p>
        </div>
        {user?.role === "doctor" && (
          <button
            onClick={() => setShowCreate(true)}
            className="bg-teal-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-teal-700 flex items-center gap-2"
          >
            <span>+</span> New Record
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : records.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
          <div className="text-4xl mb-4">📋</div>
          <p className="text-gray-500 font-medium">No medical records yet</p>
          <p className="text-gray-400 text-sm mt-1">
            {user?.role === "doctor"
              ? "Create a record after seeing a patient."
              : "Your medical records will appear here after a doctor visit."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {records.map((record, i) => (
            <motion.div
              key={record.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              onClick={() => setSelected(record)}
              className="bg-white rounded-2xl border border-gray-100 p-5 cursor-pointer hover:shadow-md hover:border-teal-200 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-semibold text-gray-900 text-sm">
                    Record #{record.id}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(record.created_at).toLocaleDateString("en-US", {
                      month: "long", day: "numeric", year: "numeric"
                    })}
                  </p>
                </div>
                <div className="flex gap-1.5">
                  {record.prescriptions?.length > 0 && (
                    <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded-full">
                      💊 {record.prescriptions.length} Rx
                    </span>
                  )}
                  {record.lab_results?.length > 0 && (
                    <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                      🔬 {record.lab_results.length} Labs
                    </span>
                  )}
                </div>
              </div>

              {record.diagnosis && (
                <div className="mb-2">
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Diagnosis</p>
                  <p className="text-sm text-gray-900 mt-0.5 line-clamp-2">{record.diagnosis}</p>
                </div>
              )}

              {record.symptoms && (
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wide">Symptoms</p>
                  <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">{record.symptoms}</p>
                </div>
              )}

              <p className="text-xs text-teal-600 mt-3 font-medium">View details →</p>
            </motion.div>
          ))}
        </div>
      )}

      <AnimatePresence>
        {showCreate && (
          <CreateRecordModal
            onClose={() => setShowCreate(false)}
            onCreated={loadRecords}
          />
        )}
        {selected && (
          <RecordDetailModal
            record={selected}
            onClose={() => setSelected(null)}
            onUpdated={loadSelected}
          />
        )}
      </AnimatePresence>
    </div>
  )
}