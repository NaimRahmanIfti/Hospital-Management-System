// src/store/authStore.js
import { create } from "zustand"
import { authAPI } from "../api/client"

const useAuthStore = create((set) => ({
  token:   localStorage.getItem("hms_token") || null,
  user:    JSON.parse(localStorage.getItem("hms_user") || "null"),
  loading: false,
  error:   null,

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const { data }      = await authAPI.login(email, password)
      const token         = data.access_token
      localStorage.setItem("hms_token", token)
      const { data: user } = await authAPI.me()
      localStorage.setItem("hms_user", JSON.stringify(user))
      set({ token, user, loading: false })
      return { success: true, user }
    } catch (err) {
      const msg = err.response?.data?.detail || "Login failed"
      set({ error: msg, loading: false })
      return { success: false, error: msg }
    }
  },

  logout: () => {
    localStorage.removeItem("hms_token")
    localStorage.removeItem("hms_user")
    set({ token: null, user: null })
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore