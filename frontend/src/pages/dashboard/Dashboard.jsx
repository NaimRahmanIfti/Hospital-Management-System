// src/pages/dashboard/Dashboard.jsx
import { Routes, Route, useNavigate } from "react-router-dom"
import { useState, useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Sidebar        from "../../components/Sidebar"
import Overview       from "./overview"
import Patients       from "./patients"
import Appointments   from "./appointments"
import Invoices       from "./invoices"
import Doctors        from "./doctors"
import Admin          from "./admin"
import MedicalRecords from "./medicalRecords"
import Pharmacy       from "./pharmacy"
import useAuthStore   from "../../store/authstore"
import { patientAPI, doctorAPI, appointmentAPI } from "../../api/client"

// ── Global Search ──────────────────────────────────────────────
function GlobalSearch() {
  const navigate                    = useNavigate()
  const { user }                    = useAuthStore()
  const [query,   setQuery]         = useState("")
  const [results, setResults]       = useState([])
  const [loading, setLoading]       = useState(false)
  const [open,    setOpen]          = useState(false)
  const wrapperRef                  = useRef()

  useEffect(() => {
    const handler = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults([])
      setOpen(false)
      return
    }

    const timeout = setTimeout(async () => {
      setLoading(true)
      const found = []

      // Search patients (admin + doctor)
      if (user?.role === "admin" || user?.role === "doctor") {
        try {
          const r = await patientAPI.list(0, 100)
          r.data.forEach(p => {
            const name  = p.user?.full_name?.toLowerCase() || ""
            const email = p.user?.email?.toLowerCase() || ""
            if (name.includes(query.toLowerCase()) || email.includes(query.toLowerCase())) {
              found.push({
                icon:  "👤",
                title: p.user?.full_name || "Unknown",
                sub:   p.user?.email,
                path:  "/dashboard/patients",
                color: "bg-teal-50 text-teal-700",
              })
            }
          })
        } catch(e) {}
      }

      // Search doctors
      try {
        const r = await doctorAPI.list()
        r.data.forEach(d => {
          const name = d.user?.full_name?.toLowerCase() || ""
          const spec = d.specialization?.toLowerCase() || ""
          if (name.includes(query.toLowerCase()) || spec.includes(query.toLowerCase())) {
            found.push({
              icon:  "🩺",
              title: d.user?.full_name || "Unknown",
              sub:   d.specialization,
              path:  "/dashboard/doctors",
              color: "bg-blue-50 text-blue-700",
            })
          }
        })
      } catch(e) {}

      // Search appointments
      try {
        const r = await appointmentAPI.myAppointments()
        r.data.forEach(a => {
          const reason = a.reason?.toLowerCase() || ""
          if (
            reason.includes(query.toLowerCase()) ||
            a.status?.includes(query.toLowerCase()) ||
            a.patient_name?.toLowerCase().includes(query.toLowerCase()) ||
            a.doctor_name?.toLowerCase().includes(query.toLowerCase())
          ) {
            found.push({
              icon:  "📅",
              title: `${a.patient_name || `Patient #${a.patient_id}`} — ${a.reason || "Appointment"}`,
              sub:   `${a.status} · ${new Date(a.scheduled_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`,
              path:  "/dashboard/appointments",
              color: "bg-purple-50 text-purple-700",
            })
          }
        })
      } catch(e) {}

      // Navigation shortcuts
      const shortcuts = [
        { keyword: "overview",        path: "/dashboard",                 icon: "⊞", title: "Go to Overview",        sub: "Dashboard home"            },
        { keyword: "patient",         path: "/dashboard/patients",        icon: "👤", title: "Go to Patients",        sub: "View all patients"         },
        { keyword: "appointment",     path: "/dashboard/appointments",    icon: "📅", title: "Go to Appointments",    sub: "Book or view appointments" },
        { keyword: "medical",         path: "/dashboard/medical-records", icon: "📋", title: "Go to Medical Records", sub: "View medical records"      },
        { keyword: "pharmacy",        path: "/dashboard/pharmacy",        icon: "💊", title: "Go to Pharmacy",        sub: "View prescriptions"        },
        { keyword: "invoice",         path: "/dashboard/invoices",        icon: "💳", title: "Go to Invoices",        sub: "View and pay invoices"     },
        { keyword: "doctor",          path: "/dashboard/doctors",         icon: "🩺", title: "Go to Doctors",         sub: "View all doctors"          },
        { keyword: "admin",           path: "/dashboard/admin",           icon: "⚙️", title: "Go to Admin Panel",     sub: "Manage hospital"           },
        { keyword: "room",            path: "/dashboard/rooms",           icon: "🏥", title: "Go to Rooms",           sub: "Manage hospital rooms"     },
      ]

      shortcuts.forEach(s => {
        if (s.keyword.includes(query.toLowerCase())) {
          found.push({
            icon:  s.icon,
            title: s.title,
            sub:   s.sub,
            path:  s.path,
            color: "bg-gray-50 text-gray-600",
          })
        }
      })

      setResults(found.slice(0, 8))
      setOpen(found.length > 0)
      setLoading(false)
    }, 300)

    return () => clearTimeout(timeout)
  }, [query, user])

  const handleSelect = (item) => {
    navigate(item.path)
    setQuery("")
    setOpen(false)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
          {loading
            ? <div className="w-3.5 h-3.5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
            : "🔍"
          }
        </span>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === "Escape" && (setOpen(false), setQuery(""))}
          placeholder="Search patients, doctors, appointments..."
          className="pl-9 pr-8 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg w-80 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
        />
        {query && (
          <button
            onClick={() => { setQuery(""); setOpen(false) }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-lg"
          >×</button>
        )}
      </div>

      <AnimatePresence>
        {open && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full mt-2 left-0 w-96 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden"
          >
            <div className="px-4 py-2 border-b border-gray-50 flex justify-between items-center">
              <span className="text-xs text-gray-400">{results.length} results for "{query}"</span>
              <span className="text-xs text-gray-300">ESC to close</span>
            </div>
            <div className="py-1 max-h-80 overflow-y-auto">
              {results.map((item, i) => (
                <button
                  key={i}
                  onClick={() => handleSelect(item)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left group"
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0 ${item.color}`}>
                    {item.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate group-hover:text-teal-600">
                      {item.title}
                    </p>
                    {item.sub && <p className="text-xs text-gray-400 truncate">{item.sub}</p>}
                  </div>
                  <span className="text-gray-300 group-hover:text-teal-400 text-sm">→</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {open && results.length === 0 && !loading && query.length >= 2 && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute top-full mt-2 left-0 w-80 bg-white rounded-xl shadow-lg border border-gray-100 z-50 p-6 text-center"
          >
            <p className="text-gray-400 text-sm">No results for "{query}"</p>
            <p className="text-gray-300 text-xs mt-1">Try patient name, doctor, or page name</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ── Dashboard ──────────────────────────────────────────────────
export default function Dashboard() {
  const { user }    = useAuthStore()
  const navigate    = useNavigate()

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">

        {/* Topbar */}
        <div className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-8 sticky top-0 z-10 shadow-sm">
          <GlobalSearch />
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-gray-400 bg-gray-50 px-3 py-1.5 rounded-full border border-gray-100">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              NovaCare Live
            </div>
            <div className="text-xs text-gray-400 hidden md:block">
              {new Date().toLocaleDateString("en-US", {
                weekday: "short", month: "short", day: "numeric"
              })}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          <Routes>
            <Route index                  element={<Overview />}       />
            <Route path="patients"        element={<Patients />}       />
            <Route path="appointments"    element={<Appointments />}   />
            <Route path="medical-records" element={<MedicalRecords />} />
            <Route path="pharmacy"        element={<Pharmacy />}       />
            <Route path="invoices"        element={<Invoices />}       />
            <Route path="doctors"         element={<Doctors />}        />
            {user?.role === "admin" && (
              <Route path="admin"         element={<Admin />}          />
            )}
          </Routes>
        </div>
      </main>
    </div>
  )
}