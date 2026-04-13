// src/pages/Login.jsx
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import useAuthStore from "../store/authstore"

export default function Login() {
  const navigate  = useNavigate()
  const { login, loading, error, clearError } = useAuthStore()

  const [form, setForm] = useState({ email: "", password: "" })

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    const result = await login(form.email, form.password)
    if (result.success) {
      navigate("/dashboard")
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        {/* Logo */}
        <div className="text-center mb-8">
         <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-teal-500 to-teal-700 rounded-xl mb-4 shadow-lg shadow-teal-200">
          <span className="text-white font-bold text-lg">N</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome back</h1>
        <p className="text-gray-500 text-sm mt-1">Sign in to NovaCare Medical Center</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">

          {/* Error message */}
          {error && (
            <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-6 border border-red-100">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Email address
              </label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="doctor@hospital.com"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Password
              </label>
              <input
                type="password"
                required
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 text-white py-2.5 rounded-lg font-medium hover:bg-teal-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          {/* Quick fill for testing */}
          <div className="mt-6 pt-6 border-t border-gray-100">
            <p className="text-xs text-gray-400 mb-3 text-center">Quick fill for testing</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: "Admin",   email: "admin@hospital.com",    pw: "Admin123"  },
                { label: "Doctor",  email: "dr.jones@hospital.com", pw: "Doctor123" },
                { label: "Patient", email: "alice@hospital.com",    pw: "Patient123"},
              ].map((u) => (
                <button
                  key={u.label}
                  onClick={() => setForm({ email: u.email, password: u.pw })}
                  className="text-xs px-3 py-1.5 border border-gray-200 rounded-lg hover:border-teal-300 hover:text-teal-600 transition-colors"
                >
                  {u.label}
                </button>
              ))}
            </div>
          </div>

          {/* Register link — INSIDE the card, below quick fill */}
          <p className="text-center text-sm text-gray-500 mt-6 pt-4 border-t border-gray-100">
            Don't have an account?{" "}
            <button
              onClick={() => navigate("/register")}
              className="text-teal-600 hover:underline font-medium"
            >
              Create one
            </button>
          </p>

        </div>

        {/* Back to home — OUTSIDE the card */}
        <p className="text-center text-sm text-gray-400 mt-4">
          <button
            onClick={() => navigate("/")}
            className="hover:text-teal-600 transition-colors"
          >
            ← Back to home
          </button>
        </p>

      </motion.div>
    </div>
  )
}