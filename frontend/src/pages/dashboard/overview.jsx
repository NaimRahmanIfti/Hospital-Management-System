// src/pages/dashboard/Overview.jsx
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import StatsCard from "../../components/StatsCard"
import { patientAPI, appointmentAPI, invoiceAPI, doctorAPI } from "../../api/client"
import useAuthStore from "../../store/authstore"

export default function Overview() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState({
    patients: 0, doctors: 0, appointments: 0, invoices: 0
  })
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const results = {}

        // Appointments — works for all roles
        try {
          const r = await appointmentAPI.myAppointments()
          results.appointments = r.data?.length || 0
          setAppointments(r.data?.slice(0, 5) || [])
        } catch(e) { results.appointments = 0 }

        // Doctors — works for all roles
        try {
          const r = await doctorAPI.list()
          results.doctors = r.data?.length || 0
        } catch(e) { results.doctors = 0 }

        // Patients — admin and doctor only
        if (user?.role === "admin" || user?.role === "doctor") {
          try {
            const r = await patientAPI.list(0, 100)
            results.patients = r.data?.length || 0
          } catch(e) { results.patients = 0 }
        }

        // Invoices — admin uses list, patient uses myInvoices
        try {
          if (user?.role === "admin") {
            const r = await invoiceAPI.list()
            results.invoices = r.data?.length || 0
          } else if (user?.role === "patient") {
            const r = await invoiceAPI.myInvoices()
            results.invoices = r.data?.filter(i => i.payment_status === "pending").length || 0
          }
        } catch(e) { results.invoices = 0 }

        setStats(results)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user])

  const statusColor = {
    scheduled: "bg-blue-100 text-blue-700",
    completed: "bg-green-100 text-green-700",
    cancelled: "bg-red-100 text-red-700",
    no_show:   "bg-gray-100 text-gray-600",
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
        <p className="text-gray-400 text-sm mt-1">
          {new Date().toLocaleDateString("en-US", {
            weekday: "long", year: "numeric",
            month: "long", day: "numeric"
          })}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {(user?.role === "admin" || user?.role === "doctor") && (
          <StatsCard icon="👤" label="Total Patients"   value={loading ? "—" : stats.patients}     color="teal"   />
        )}
        <StatsCard   icon="🩺" label="Doctors on Staff" value={loading ? "—" : stats.doctors}      color="blue"   />
        <StatsCard   icon="📅" label="My Appointments"  value={loading ? "—" : stats.appointments} color="purple" />
        {user?.role !== "doctor" && (
          <StatsCard icon="💳" label="Pending Invoices" value={loading ? "—" : stats.invoices}     color="amber"  />
        )}
      </div>

      {/* Recent appointments */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Recent Appointments</h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading...</div>
        ) : appointments.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            No appointments yet.
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-400 border-b border-gray-50">
                <th className="text-left px-6 py-3 font-medium">Patient</th>
                <th className="text-left px-6 py-3 font-medium">Doctor</th>
                <th className="text-left px-6 py-3 font-medium">Date & Time</th>
                <th className="text-left px-6 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((appt, i) => (
                <motion.tr
                  key={appt.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="border-b border-gray-50 hover:bg-gray-50"
                >
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {appt.patient_name || `Patient #${appt.patient_id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {appt.doctor_name || `Doctor #${appt.doctor_id}`}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(appt.scheduled_at).toLocaleString("en-US", {
                      month: "short", day: "numeric",
                      hour: "2-digit", minute: "2-digit"
                    })}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${statusColor[appt.status] || "bg-gray-100 text-gray-600"}`}>
                      {appt.status}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}