// src/pages/dashboard/Dashboard.jsx
import { Routes, Route } from "react-router-dom"
import Sidebar        from "../../components/Sidebar"
import Overview       from "./Overview"
import Patients       from "./Patients"
import Appointments   from "./appointments"
import Invoices       from "./Invoices"
import Doctors        from "./Doctors"
import Admin          from "./admin"
import MedicalRecords from "./medicalRecords"
import Pharmacy       from "./pharmacy"
import useAuthStore   from "../../store/authstore"

export default function Dashboard() {
  const { user } = useAuthStore()

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">

        {/* Top bar */}
        <div className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
            <input
              type="text"
              placeholder="Search patients, appointments..."
              className="pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg w-72 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
            />
          </div>

          {/* NovaCare live indicator */}
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

        {/* Page content */}
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