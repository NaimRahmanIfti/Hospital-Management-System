// src/pages/dashboard/Doctors.jsx
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { doctorAPI } from "../../api/client"

export default function Doctors() {
  const [doctors, setDoctors]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState("")

  useEffect(() => {
    doctorAPI.list()
      .then(r => setDoctors(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = doctors.filter(d =>
    d.user?.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    d.specialization?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Doctors</h1>
        <p className="text-gray-400 text-sm mt-1">{doctors.length} doctors on staff</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <p className="text-gray-400 text-sm col-span-3 text-center py-8">Loading...</p>
        ) : filtered.length === 0 ? (
          <p className="text-gray-400 text-sm col-span-3 text-center py-8">No doctors found.</p>
        ) : filtered.map((d, i) => (
          <motion.div
            key={d.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="bg-white rounded-2xl p-5 border border-gray-100 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center text-teal-700 font-semibold">
                {d.user?.full_name?.charAt(0) || "D"}
              </div>
              <div>
                <p className="font-medium text-gray-900 text-sm">{d.user?.full_name || "—"}</p>
                <p className="text-xs text-teal-600">{d.specialization}</p>
              </div>
            </div>
            <div className="space-y-1.5 text-xs text-gray-400">
              <div className="flex justify-between">
                <span>License</span>
                <span className="text-gray-600">{d.license_number}</span>
              </div>
              <div className="flex justify-between">
                <span>Consultation</span>
                <span className="text-gray-600">${Number(d.consultation_fee).toFixed(2)}</span>
              </div>
              {d.phone && (
                <div className="flex justify-between">
                  <span>Phone</span>
                  <span className="text-gray-600">{d.phone}</span>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}