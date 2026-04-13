// src/pages/dashboard/Patients.jsx
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { patientAPI } from "../../api/client"

export default function Patients() {
  const [patients, setPatients]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [search, setSearch]       = useState("")

  useEffect(() => {
    patientAPI.list(0, 50)
      .then(r => setPatients(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = patients.filter(p =>
    p.user?.full_name?.toLowerCase().includes(search.toLowerCase()) ||
    p.user?.email?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-gray-400 text-sm mt-1">{patients.length} total patients</p>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full text-sm focus:outline-none text-gray-700 placeholder-gray-300"
          />
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading patients...</div>
        ) : filtered.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No patients found.</div>
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
              {filtered.map((p, i) => (
                <motion.tr
                  key={p.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="border-b border-gray-50 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center text-teal-700 text-sm font-medium">
                        {p.user?.full_name?.charAt(0) || "?"}
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {p.user?.full_name || "—"}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{p.user?.email || "—"}</td>
                  <td className="px-6 py-4">
                    {p.blood_type ? (
                      <span className="bg-red-50 text-red-600 text-xs px-2 py-1 rounded-full font-medium">
                        {p.blood_type}
                      </span>
                    ) : <span className="text-gray-300 text-sm">—</span>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{p.phone || "—"}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 capitalize">{p.gender || "—"}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}