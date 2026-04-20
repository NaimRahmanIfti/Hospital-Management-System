// src/pages/dashboard/Invoices.jsx
import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import api from "../../api/client"
import useAuthStore from "../../store/authstore"

const statusColor = {
  pending: "bg-amber-100 text-amber-700",
  paid:    "bg-green-100 text-green-700",
  partial: "bg-blue-100 text-blue-700",
  overdue: "bg-red-100 text-red-700",
  waived:  "bg-gray-100 text-gray-600",
}

// ── Payment Modal ──────────────────────────────────────────────
function PaymentModal({ invoice, onClose, onPaid }) {
  const [method,  setMethod]  = useState("card")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error,   setError]   = useState("")

  const amount = Number(invoice.total_amount || 0).toFixed(2)

  const handlePay = async () => {
    setLoading(true)
    setError("")
    try {
      await api.patch(`/invoices/${invoice.id}`, { status: "paid" })
      setSuccess(true)
      setTimeout(() => {
        onPaid()
        onClose()
      }, 2000)
    } catch(err) {
      setError("Payment failed. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
        <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm z-10 p-8 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", delay: 0.1 }}
            className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <span className="text-green-600 text-3xl">✓</span>
          </motion.div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
          <p className="text-gray-500 text-sm">
            Your payment of <span className="font-semibold text-gray-900">${amount}</span> has been processed.
          </p>
          <p className="text-gray-400 text-xs mt-2">Invoice #{invoice.id} is now marked as paid.</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-white rounded-2xl shadow-xl w-full max-w-md z-10"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h2 className="font-semibold text-gray-900">Pay Invoice #{invoice.id}</h2>
            <p className="text-xs text-gray-400 mt-0.5">Secure payment</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">×</button>
        </div>

        <div className="p-6 space-y-5">

          {/* Amount */}
          <div className="bg-teal-50 rounded-xl p-4 text-center">
            <p className="text-sm text-teal-600 mb-1">Amount Due</p>
            <p className="text-3xl font-bold text-teal-800">${amount}</p>
            {invoice.items?.length > 0 && (
              <p className="text-xs text-teal-500 mt-1">
                {invoice.items.length} item{invoice.items.length !== 1 ? "s" : ""}
              </p>
            )}
          </div>

          {/* Invoice breakdown */}
          {invoice.items?.length > 0 && (
            <div className="bg-gray-50 rounded-xl p-4 space-y-2">
              {invoice.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-gray-600">
                    {item.description}
                    {item.quantity > 1 && <span className="text-gray-400"> ×{item.quantity}</span>}
                  </span>
                  <span className="text-gray-900 font-medium">
                    ${Number(item.total_price || item.unit_price).toFixed(2)}
                  </span>
                </div>
              ))}
              <div className="flex justify-between text-sm border-t border-gray-200 pt-2 mt-2">
                <span className="text-gray-500">Subtotal</span>
                <span className="text-gray-900">${Number(invoice.subtotal || 0).toFixed(2)}</span>
              </div>
              {Number(invoice.tax_amount || 0) > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Tax</span>
                  <span className="text-gray-900">${Number(invoice.tax_amount).toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-semibold">
                <span className="text-gray-900">Total</span>
                <span className="text-teal-700">${amount}</span>
              </div>
            </div>
          )}

          {/* Payment method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Payment Method
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: "card",   label: "💳 Card"    },
                { value: "cash",   label: "💵 Cash"    },
                { value: "insurance", label: "🏥 Insurance" },
              ].map(m => (
                <button
                  key={m.value}
                  onClick={() => setMethod(m.value)}
                  className={`py-2.5 rounded-lg text-xs font-medium border transition-all ${
                    method === m.value
                      ? "bg-teal-600 text-white border-teal-600"
                      : "border-gray-200 text-gray-500 hover:border-teal-300"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Card details (demo) */}
          {method === "card" && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="space-y-3"
            >
              <div>
                <label className="block text-xs text-gray-500 mb-1">Card Number</label>
                <input
                  type="text"
                  defaultValue="4242 4242 4242 4242"
                  disabled
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-400"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Expiry</label>
                  <input
                    type="text"
                    defaultValue="12/28"
                    disabled
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-400"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">CVV</label>
                  <input
                    type="text"
                    defaultValue="•••"
                    disabled
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-400"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-400 text-center">
                Demo mode — no real payment processed
              </p>
            </motion.div>
          )}

          {error && (
            <div className="bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-100">
              {error}
            </div>
          )}

          <button
            onClick={handlePay}
            disabled={loading}
            className="w-full bg-teal-600 text-white py-3 rounded-xl font-semibold hover:bg-teal-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>💳 Pay ${amount}</>
            )}
          </button>

          <p className="text-center text-xs text-gray-400">
            🔒 Secured by MediCore Payment System
          </p>
        </div>
      </motion.div>
    </div>
  )
}

// ── Main Invoices Page ─────────────────────────────────────────
export default function Invoices() {
  const { user }                        = useAuthStore()
  const [invoices,    setInvoices]      = useState([])
  const [loading,     setLoading]       = useState(true)
  const [error,       setError]         = useState("")
  const [payTarget,   setPayTarget]     = useState(null)

  const loadInvoices = async () => {
    try {
      let data = []
      if (user?.role === "admin" || user?.role === "doctor") {
        const r = await api.get("/invoices/")
        data = r.data || []
      } else if (user?.role === "patient") {
        const r = await api.get("/invoices/my")
        data = r.data || []
      }
      setInvoices(data)
    } catch(e) {
      setError("Could not load invoices.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadInvoices() }, [user])

  const total = invoices.reduce((s, i) => s + Number(i.total_amount || 0), 0)
  const paid  = invoices
    .filter(i => i.status === "paid")
    .reduce((s, i) => s + Number(i.total_amount || 0), 0)

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
        <p className="text-gray-400 text-sm mt-1">{invoices.length} invoices</p>
      </div>

      {invoices.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: "Total Billed",  value: `$${total.toFixed(2)}`,          color: "border-l-teal-500"  },
            { label: "Total Paid",    value: `$${paid.toFixed(2)}`,           color: "border-l-green-500" },
            { label: "Outstanding",   value: `$${(total - paid).toFixed(2)}`, color: "border-l-amber-500" },
          ].map(c => (
            <div key={c.label} className={`bg-white rounded-xl p-4 border border-gray-100 border-l-4 ${c.color}`}>
              <div className="text-xl font-bold text-gray-900">{c.value}</div>
              <div className="text-sm text-gray-400 mt-0.5">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Loading...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-400 text-sm">{error}</div>
        ) : invoices.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            No invoices yet. They will appear here after your appointments.
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-400 border-b border-gray-50">
                <th className="text-left px-6 py-3 font-medium">Invoice #</th>
                <th className="text-left px-6 py-3 font-medium">Date</th>
                <th className="text-left px-6 py-3 font-medium">Items</th>
                <th className="text-left px-6 py-3 font-medium">Subtotal</th>
                <th className="text-left px-6 py-3 font-medium">Total</th>
                <th className="text-left px-6 py-3 font-medium">Status</th>
                <th className="text-left px-6 py-3 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv, i) => (
                <motion.tr
                  key={inv.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="border-b border-gray-50 hover:bg-gray-50"
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">#{inv.id}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(inv.created_at).toLocaleDateString("en-US", {
                      month: "short", day: "numeric", year: "numeric"
                    })}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {inv.items?.length || 0} item{inv.items?.length !== 1 ? "s" : ""}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    ${Number(inv.subtotal || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                    ${Number(inv.total_amount || 0).toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      statusColor[inv.status] || "bg-gray-100 text-gray-600"
                    }`}>
                      {inv.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {user?.role === "patient" && inv.status === "pending" && (
                      <button
                        onClick={() => setPayTarget(inv)}
                        className="bg-teal-600 text-white text-xs px-4 py-1.5 rounded-lg hover:bg-teal-700 transition-colors font-medium"
                      >
                        💳 Pay Now
                      </button>
                    )}
                    {inv.status === "paid" && (
                      <span className="text-xs text-green-600 font-medium">✓ Paid</span>
                    )}
                    {user?.role === "patient" && inv.status === "overdue" && (
                      <button
                        onClick={() => setPayTarget(inv)}
                        className="bg-red-600 text-white text-xs px-4 py-1.5 rounded-lg hover:bg-red-700 transition-colors font-medium"
                      >
                        ⚠️ Pay Overdue
                      </button>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <AnimatePresence>
        {payTarget && (
          <PaymentModal
            invoice={payTarget}
            onClose={() => setPayTarget(null)}
            onPaid={() => {
              setPayTarget(null)
              loadInvoices()
            }}
          />
        )}
      </AnimatePresence>
    </div>
  )
}