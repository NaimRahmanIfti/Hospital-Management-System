// src/api/client.js
import axios from "axios"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("hms_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("hms_token")
      localStorage.removeItem("hms_user")
      window.location.href = "/login"
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  register: (data) => api.post("/auth/register", data),
  login: (email, password) => {
    const form = new URLSearchParams()
    form.append("username", email)
    form.append("password", password)
    return api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    })
  },
  me: () => api.get("/auth/me"),
}

export const patientAPI = {
  // Admin only
  list:   (skip = 0, limit = 100) => api.get(`/patients/?skip=${skip}&limit=${limit}`),
  get:    (id) => api.get(`/patients/${id}`),
  create: (data) => api.post("/patients/", data),
  update: (id, data) => api.patch(`/patients/${id}`, data),
}

export const doctorAPI = {
  // Any logged-in user
  list:   (params = {}) => api.get("/doctors/", { params }),
  get:    (id) => api.get(`/doctors/${id}`),
  create: (data) => api.post("/doctors/", data),
  update: (id, data) => api.patch(`/doctors/${id}`, data),
}

export const appointmentAPI = {
  // Works for all roles — returns own appointments
  myAppointments: (status) =>
    api.get("/appointments/my", { params: status ? { status } : {} }),
  get:    (id) => api.get(`/appointments/${id}`),
  book:   (data) => api.post("/appointments/", data),
  update: (id, data) => api.patch(`/appointments/${id}`, data),
  cancel: (id) => api.delete(`/appointments/${id}`),
}

export const invoiceAPI = {
  // Patient uses /my, admin uses /
  myInvoices:     () => api.get("/invoices/my"),
  list:           (params = {}) => api.get("/invoices/", { params }),
  get:            (id) => api.get(`/invoices/${id}`),
  create:         (data) => api.post("/invoices/", data),
  update:         (id, data) => api.patch(`/invoices/${id}`, data),
}

export const medicalRecordAPI = {
  myRecords: () => api.get("/medical-records/my"),
  get:       (id) => api.get(`/medical-records/${id}`),
  create:    (data) => api.post("/medical-records/", data),
  update:    (id, data) => api.patch(`/medical-records/${id}`, data),
}

export default api