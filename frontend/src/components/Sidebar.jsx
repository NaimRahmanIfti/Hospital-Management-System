// src/components/Sidebar.jsx
import { NavLink, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import useAuthStore from "../store/authstore"

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  const navItems = [
    { path: "/dashboard",                 icon: "⊞",  label: "Overview",        roles: ["admin","doctor","patient"] },
    { path: "/dashboard/patients",        icon: "👤",  label: "Patients",        roles: ["admin","doctor"]           },
    { path: "/dashboard/appointments",    icon: "📅",  label: "Appointments",    roles: ["admin","doctor","patient"] },
    { path: "/dashboard/medical-records", icon: "📋",  label: "Medical Records", roles: ["admin","doctor","patient"] },
    { path: "/dashboard/pharmacy",        icon: "💊",  label: "Pharmacy",        roles: ["admin","doctor","patient"] },
    { path: "/dashboard/invoices",        icon: "💳",  label: "Invoices",        roles: ["admin","patient"]          },
    { path: "/dashboard/doctors",         icon: "🩺",  label: "Doctors",         roles: ["admin","patient"]          },
    { path: "/dashboard/rooms",           icon: "🏥",  label: "Rooms",           roles: ["admin"]                    },
    { path: "/dashboard/admin",           icon: "⚙️",  label: "Admin Panel",     roles: ["admin"]                    },
  ].filter(item => item.roles.includes(user?.role || "patient"))

  const roleColor = {
    admin:   "bg-purple-100 text-purple-700",
    doctor:  "bg-blue-100 text-blue-700",
    patient: "bg-teal-100 text-teal-700",
  }

  return (
    <aside className="w-64 min-h-screen bg-white border-r border-gray-100 flex flex-col">

      {/* Logo */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-gray-100">
        <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-700 rounded-lg flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-sm">N</span>
        </div>
        <div>
          <span className="font-bold text-gray-900 text-sm">NovaCare</span>
          <p className="text-xs text-gray-400 leading-none">Medical Center</p>
        </div>
      </div>

      {/* Role badge */}
      <div className="px-4 pt-4 pb-1">
        <span className={`text-xs px-2.5 py-1 rounded-full font-medium capitalize ${roleColor[user?.role] || "bg-gray-100 text-gray-600"}`}>
          {user?.role} access
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-3 overflow-y-auto">
        {navItems.map((item, i) => (
          <motion.div
            key={item.path}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <NavLink
              to={item.path}
              end={item.path === "/dashboard"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm mb-1 transition-all ${
                  isActive
                    ? "bg-teal-50 text-teal-700 font-medium shadow-sm"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              <span className="text-base w-5 text-center">{item.icon}</span>
              {item.label}
            </NavLink>
          </motion.div>
        ))}
      </nav>

      {/* User card */}
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center gap-3 mb-3 p-2 rounded-xl hover:bg-gray-50 transition-colors">
          <div className="w-9 h-9 bg-gradient-to-br from-teal-400 to-teal-600 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
            {user?.full_name?.charAt(0) || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2 text-xs text-gray-400 hover:text-red-500 transition-colors px-2 py-1.5 rounded-lg hover:bg-red-50"
        >
          <span>→</span> Sign out
        </button>
      </div>
    </aside>
  )
}