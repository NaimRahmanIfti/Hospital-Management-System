// src/pages/Register.jsx
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { authAPI } from "../api/client"
import useAuthStore from "../store/authstore"

export default function Register() {
  const navigate  = useNavigate()
  const { login } = useAuthStore()

  const [form, setForm] = useState({
    full_name:        "",
    email:            "",
    password:         "",
    role:             "patient",
    specialization:   "General Medicine",
    license_number:   "",
    consultation_fee: "100",
  })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")
  const [step,    setStep]    = useState("form") // "form" | "creating" | "done"

  const parseError = (err) => {
    const data = err?.response?.data
    if (!data) return err?.message || "Registration failed"
    if (Array.isArray(data.detail))
      return data.detail.map(e => typeof e === "string" ? e : (e.msg || JSON.stringify(e))).join(", ")
    if (typeof data.detail === "string") return data.detail
    return JSON.stringify(data)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.full_name || !form.email || !form.password) {
      setError("Please fill in all required fields.")
      return
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.")
      return
    }
    if (!/[A-Z]/.test(form.password)) {
      setError("Password must contain at least one uppercase letter.")
      return
    }
    if (!/[0-9]/.test(form.password)) {
      setError("Password must contain at least one number.")
      return
    }

    setLoading(true)
    setError("")
    setStep("creating")

    try {
      // Step 1 — Create user account
      const { data: newUser } = await authAPI.register({
        full_name: form.full_name,
        email:     form.email,
        password:  form.password,
        role:      form.role,
      })

      // Step 2 — Login to get token
      const loginResult = await login(form.email, form.password)
      if (!loginResult.success) {
        setError("Account created but login failed. Please sign in manually.")
        navigate("/login")
        return
      }

      const token = localStorage.getItem("hms_token")
      const headers = {
        "Content-Type":  "application/json",
        "Authorization": `Bearer ${token}`,
      }

      // Step 3 — Create profile
      if (form.role === "patient") {
        try {
          const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/patients/`, {
            method: "POST", headers,
            body: JSON.stringify({ user_id: newUser.id }),
          })
          if (!res.ok) {
            const errData = await res.json()
            // 409 = profile already created server-side — that's fine
            if (res.status !== 409) {
              console.error("Patient profile error:", errData)
              setError(`Account created but profile setup failed: ${errData.detail || "Unknown error"}. Please contact support.`)
            }
          }
        } catch (profileErr) {
          console.error("Patient profile creation failed:", profileErr)
        }
      }

      if (form.role === "doctor") {
        try {
          const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/doctors/`, {
            method: "POST", headers,
            body: JSON.stringify({
              user_id:          newUser.id,
              specialization:   form.specialization || "General Medicine",
              license_number:   form.license_number || `LIC-${Date.now()}`,
              consultation_fee: form.consultation_fee || "100",
            }),
          })
          if (!res.ok) {
            const errData = await res.json()
            if (res.status !== 409) {
              console.error("Doctor profile error:", errData)
              setError(`Account created but doctor profile setup failed: ${errData.detail || "Unknown error"}. Please contact support.`)
            }
          }
        } catch (profileErr) {
          console.error("Doctor profile creation failed:", profileErr)
        }
      }

      // Step 4 — Re-fetch user to make sure role is correct in store
      try {
        const meRes = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/auth/me`, { headers })
        const meData = await meRes.json()
        localStorage.setItem("hms_user", JSON.stringify(meData))
      } catch(e) { console.warn("Could not refresh user data") }

      setStep("done")
      // Force full page reload so auth store rehydrates with correct user
      window.location.href = "/dashboard"

    } catch (err) {
      setStep("form")
      setError(parseError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-teal-500 to-teal-700 rounded-xl mb-4 shadow-lg shadow-teal-200">
             <span className="text-white font-bold text-lg">N</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Join NovaCare</h1>
          <p className="text-gray-500 text-sm mt-1">Create your account at NovaCare Medical Center</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">

          {error && (
            <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg mb-5 border border-red-100">
              {error}
            </div>
          )}

          {step === "creating" && (
            <div className="text-center py-8">
              <div className="w-10 h-10 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600 font-medium">Creating your account...</p>
              <p className="text-gray-400 text-sm mt-1">Setting up your profile</p>
            </div>
          )}

          {step === "form" && (
            <form onSubmit={handleSubmit} className="space-y-4">

              {/* Role */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">I am a...</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: "patient", label: "👤 Patient" },
                    { value: "doctor",  label: "🩺 Doctor"  },
                    { value: "admin",   label: "⚙️ Admin"   },
                  ].map(r => (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setForm({ ...form, role: r.value })}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-all ${
                        form.role === r.value
                          ? "bg-teal-600 text-white border-teal-600"
                          : "border-gray-200 text-gray-500 hover:border-teal-300"
                      }`}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {form.role === "patient" && "Book appointments and view your medical records."}
                  {form.role === "doctor"  && "Manage appointments and create medical records."}
                  {form.role === "admin"   && "Full access to all hospital data."}
                </p>
              </div>

              {/* Full name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Full name</label>
                <input
                  type="text"
                  required
                  value={form.full_name}
                  onChange={e => setForm({ ...form, full_name: e.target.value })}
                  placeholder={form.role === "doctor" ? "Dr. Sarah Smith" : "Alice Johnson"}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={e => setForm({ ...form, email: e.target.value })}
                  placeholder="you@example.com"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                <input
                  type="password"
                  required
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  placeholder="Min 8 chars, 1 uppercase, 1 number"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <div className="flex gap-3 mt-2">
                  {[
                    { label: "8+ chars",   ok: form.password.length >= 8          },
                    { label: "Uppercase",  ok: /[A-Z]/.test(form.password)        },
                    { label: "Number",     ok: /[0-9]/.test(form.password)        },
                  ].map(r => (
                    <div key={r.label} className={`flex items-center gap-1 text-xs ${r.ok ? "text-green-600" : "text-gray-400"}`}>
                      <span>{r.ok ? "✓" : "○"}</span>
                      <span>{r.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Doctor-only fields */}
              {form.role === "doctor" && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="space-y-4 border-t border-gray-100 pt-4"
                >
                  <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Doctor details</p>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">Specialization</label>
                    <select
                      value={form.specialization}
                      onChange={e => setForm({ ...form, specialization: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                    >
                      {[
                        "General Medicine","Cardiology","Neurology",
                        "Orthopedics","Pediatrics","Dermatology",
                        "Psychiatry","Oncology","Emergency Medicine",
                      ].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">License #</label>
                      <input
                        type="text"
                        value={form.license_number}
                        onChange={e => setForm({ ...form, license_number: e.target.value })}
                        placeholder="MD-2024-001"
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1.5">Fee ($)</label>
                      <input
                        type="number"
                        value={form.consultation_fee}
                        onChange={e => setForm({ ...form, consultation_fee: e.target.value })}
                        placeholder="150"
                        className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                      />
                    </div>
                  </div>
                </motion.div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-teal-600 text-white py-3 rounded-lg font-medium hover:bg-teal-700 transition-colors disabled:opacity-60"
              >
                Create account & sign in
              </button>
            </form>
          )}

          <p className="text-center text-sm text-gray-500 mt-6 pt-4 border-t border-gray-100">
            Already have an account?{" "}
            <button
              onClick={() => navigate("/login")}
              className="text-teal-600 hover:underline font-medium"
            >
              Sign in
            </button>
          </p>
        </div>

        <p className="text-center text-sm text-gray-400 mt-4">
          <button onClick={() => navigate("/")} className="hover:text-teal-600">
            ← Back to home
          </button>
        </p>
      </motion.div>
    </div>
  )
}