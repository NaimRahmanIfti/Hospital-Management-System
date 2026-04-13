// src/pages/dashboard/Pharmacy.jsx
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import api from "../../api/client"
import useAuthStore from "../../store/authstore"

export default function Pharmacy() {
  const { user }                    = useAuthStore()
  const [records,   setRecords]     = useState([])
  const [loading,   setLoading]     = useState(true)
  const [search,    setSearch]      = useState("")
  const [filter,    setFilter]      = useState("all")

  useEffect(() => {
    api.get("/medical-records/my")
      .then(r => setRecords(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user])

  // Flatten all prescriptions from all records
  const allPrescriptions = records.flatMap(record =>
    (record.prescriptions || []).map(rx => ({
      ...rx,
      record_id:  record.id,
      created_at: record.created_at,
      diagnosis:  record.diagnosis,
    }))
  )

  const filtered = allPrescriptions.filter(rx => {
    const matchSearch = rx.medication_name?.toLowerCase().includes(search.toLowerCase())
    return matchSearch
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pharmacy</h1>
          <p className="text-gray-400 text-sm mt-1">
            {allPrescriptions.length} prescriptions
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
        <input
          type="text"
          placeholder="Search medications..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
          <div className="text-4xl mb-4">💊</div>
          <p className="text-gray-500 font-medium">No prescriptions found</p>
          <p className="text-gray-400 text-sm mt-1">
            Prescriptions will appear here after a doctor visit.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((rx, i) => (
            <motion.div
              key={rx.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-md transition-all"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center text-xl">
                  💊
                </div>
                <span className="bg-green-100 text-green-700 text-xs px-2.5 py-1 rounded-full font-medium">
                  Active
                </span>
              </div>

              {/* Medication */}
              <h3 className="font-semibold text-gray-900 mb-1">
                {rx.medication_name}
              </h3>

              {/* Details */}
              <div className="space-y-1.5 mt-3">
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="text-gray-300">◆</span>
                  <span>Dosage: <span className="text-gray-900 font-medium">{rx.dosage}</span></span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <span className="text-gray-300">◆</span>
                  <span>Frequency: <span className="text-gray-900 font-medium">{rx.frequency}</span></span>
                </div>
                {rx.duration && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span className="text-gray-300">◆</span>
                    <span>Duration: <span className="text-gray-900 font-medium">{rx.duration}</span></span>
                  </div>
                )}
                {rx.instructions && (
                  <div className="mt-3 bg-teal-50 rounded-lg px-3 py-2">
                    <p className="text-xs text-teal-700">ℹ {rx.instructions}</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                <p className="text-xs text-gray-400">
                  Record #{rx.record_id}
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(rx.created_at).toLocaleDateString("en-US", {
                    month: "short", day: "numeric", year: "numeric"
                  })}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}