// src/pages/Landing.jsx
import { Suspense, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion, useScroll, useTransform } from "framer-motion"
import { Canvas, useFrame } from "@react-three/fiber"
import { Sphere, MeshDistortMaterial, Float, Stars, Torus } from "@react-three/drei"

// ── 3D DNA Helix inspired scene ────────────────────────────────
function FloatingOrb({ position, color, speed, size, distort }) {
  const ref = useRef()
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * speed * 0.5) * 0.4
      ref.current.rotation.y += speed * 0.003
      ref.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * speed) * 0.3
    }
  })
  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[size, 64, 64]} />
      <MeshDistortMaterial
        color={color}
        distort={distort}
        speed={1.5}
        roughness={0.1}
        metalness={0.3}
        transparent
        opacity={0.85}
      />
    </mesh>
  )
}

function RotatingRing({ radius, color, speed, tilt }) {
  const ref = useRef()
  useFrame(() => {
    if (ref.current) ref.current.rotation.z += speed
  })
  return (
    <mesh ref={ref} rotation={[tilt, 0, 0]}>
      <torusGeometry args={[radius, 0.025, 16, 100]} />
      <meshStandardMaterial color={color} transparent opacity={0.25} />
    </mesh>
  )
}

function Particles() {
  const ref = useRef()
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.03
    }
  })
  return (
    <group ref={ref}>
      <Stars radius={80} depth={40} count={4000} factor={3} fade speed={0.3} />
    </group>
  )
}

function HeroScene3D() {
  return (
    <Canvas camera={{ position: [0, 0, 9], fov: 55 }} style={{ background: "transparent" }}>
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]}  intensity={1.5} color="#14b8a6" />
      <pointLight position={[-8, -8, -5]}  intensity={0.8} color="#0ea5e9" />
      <pointLight position={[0, 8, 0]}     intensity={0.6} color="#a78bfa" />
      <directionalLight position={[5, 5, 5]} intensity={0.5} />

      <Particles />

      {/* Main large orb */}
      <Float speed={1} rotationIntensity={0.3} floatIntensity={0.5}>
        <FloatingOrb position={[0, 0, 0]}     color="#0d9488" speed={0.6} size={2.0} distort={0.35} />
      </Float>

      {/* Smaller accent orbs */}
      <FloatingOrb position={[4.5, 1.5, -2]}  color="#14b8a6" speed={1.2} size={0.9} distort={0.5} />
      <FloatingOrb position={[-4, -1.5, -1]}  color="#0ea5e9" speed={0.8} size={0.7} distort={0.4} />
      <FloatingOrb position={[2.5, -2.5, -1]} color="#a78bfa" speed={1.0} size={0.5} distort={0.6} />
      <FloatingOrb position={[-2.5, 2.5, -2]} color="#f0abfc" speed={0.7} size={0.4} distort={0.5} />

      {/* Rotating rings */}
      <RotatingRing radius={3.2} color="#14b8a6" speed={0.004}  tilt={Math.PI / 4}  />
      <RotatingRing radius={4.5} color="#0ea5e9" speed={-0.003} tilt={Math.PI / 3}  />
      <RotatingRing radius={5.5} color="#a78bfa" speed={0.002}  tilt={Math.PI / 6}  />
    </Canvas>
  )
}

// ── Feature cards data ─────────────────────────────────────────
const features = [
  { icon: "👤", title: "Patient Management",    desc: "Complete profiles, medical history, emergency contacts and blood type tracking." },
  { icon: "📅", title: "Smart Appointments",    desc: "Conflict-free booking with real-time doctor availability and specialization search." },
  { icon: "🔬", title: "Medical Records",       desc: "Diagnoses, prescriptions, and lab results organized by patient and doctor." },
  { icon: "💳", title: "Billing & Invoices",    desc: "Automated invoicing with line items, tax calculation, and online payment." },
  { icon: "💊", title: "Pharmacy",              desc: "All prescriptions in one place with dosage, frequency and instructions." },
  { icon: "🔐", title: "Role-Based Access",     desc: "Separate secure dashboards for admin, doctors, and patients." },
]

const stats = [
  { value: "40+",  label: "API Endpoints"  },
  { value: "11",   label: "DB Tables"      },
  { value: "3",    label: "User Roles"     },
  { value: "100%", label: "Secure JWT"     },
]

export default function Landing() {
  const navigate   = useNavigate()
  const { scrollY } = useScroll()
  const y1 = useTransform(scrollY, [0, 300], [0, -50])
  const opacity = useTransform(scrollY, [0, 300], [1, 0])

  return (
    <div className="min-h-screen bg-white">

      {/* ── Navbar ──────────────────────────────────────────── */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-700 rounded-lg flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-sm">N</span>
            </div>
            <div>
              <span className="font-bold text-gray-900">NovaCare</span>
              <span className="text-gray-400 text-sm ml-1">Medical Center</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/login")}
              className="text-sm text-gray-600 hover:text-teal-600 transition-colors font-medium"
            >
              Sign in
            </button>
            <button
              onClick={() => navigate("/register")}
              className="bg-teal-600 text-white text-sm px-5 py-2 rounded-lg hover:bg-teal-700 transition-colors shadow-sm"
            >
              Get started
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex items-center overflow-hidden">

        {/* 3D background */}
        <motion.div style={{ y: y1, opacity }} className="absolute inset-0 z-0">
          <div className="absolute right-0 top-0 w-full h-full opacity-70">
            <Suspense fallback={null}>
              <HeroScene3D />
            </Suspense>
          </div>
          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-white via-white/85 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent" />
        </motion.div>

        {/* Hero content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-16">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="max-w-2xl"
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <span className="inline-flex items-center gap-2 bg-teal-50 text-teal-700 text-sm font-medium px-4 py-1.5 rounded-full border border-teal-100 mb-6">
                <span className="w-2 h-2 bg-teal-500 rounded-full animate-pulse" />
                NovaCare Medical Center
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight mb-6"
            >
              Advanced Care,
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-600 to-cyan-500">
                Human Touch
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-xl text-gray-500 mb-8 leading-relaxed"
            >
              A complete hospital management platform — patient records,
              appointments, prescriptions, billing, and role-based access.
              All in one secure system.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex items-center gap-4 flex-wrap"
            >
              <button
                onClick={() => navigate("/register")}
                className="bg-teal-600 text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-teal-700 transition-all shadow-lg shadow-teal-200 hover:shadow-teal-300 hover:-translate-y-0.5"
              >
                Get Started Free
              </button>
              <button
                onClick={() => navigate("/login")}
                className="flex items-center gap-2 text-gray-700 font-medium hover:text-teal-600 transition-colors"
              >
                <span className="w-10 h-10 bg-white rounded-full border border-gray-200 flex items-center justify-center shadow-sm text-teal-600">
                  →
                </span>
                Sign in to dashboard
              </button>
            </motion.div>

            {/* Live status */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7 }}
              className="flex items-center gap-6 mt-10 pt-8 border-t border-gray-100"
            >
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                Live on PostgreSQL
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-2 h-2 bg-blue-400 rounded-full" />
                Docker containerized
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-2 h-2 bg-purple-400 rounded-full" />
                JWT secured
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ── Stats bar ───────────────────────────────────────── */}
      <section className="bg-teal-600 py-12">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {stats.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="text-3xl font-bold text-white">{s.value}</div>
                <div className="text-teal-200 text-sm mt-1">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────── */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <motion.span
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-teal-600 text-sm font-semibold uppercase tracking-wide"
            >
              Everything you need
            </motion.span>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-3xl font-bold text-gray-900 mt-2 mb-4"
            >
              Complete hospital management
            </motion.h2>
            <motion.p
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              className="text-gray-500 max-w-xl mx-auto"
            >
              Built with FastAPI, PostgreSQL, React and Three.js — a full-stack
              system designed for real hospital workflows.
            </motion.p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
                whileHover={{ y: -4 }}
                className="bg-white rounded-2xl p-6 border border-gray-100 hover:border-teal-200 hover:shadow-lg transition-all group cursor-default"
              >
                <div className="w-12 h-12 bg-teal-50 rounded-xl flex items-center justify-center text-2xl mb-4 group-hover:bg-teal-100 transition-colors">
                  {f.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-teal-600 transition-colors">
                  {f.title}
                </h3>
                <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────── */}
      <section className="py-24 bg-white">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How it works</h2>
            <p className="text-gray-500">Three roles, one seamless system</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                role: "Patient",
                icon: "👤",
                color: "bg-teal-50 border-teal-100",
                iconBg: "bg-teal-100",
                steps: ["Register account", "Search & book doctor", "View medical records", "Pay invoices online"],
              },
              {
                role: "Doctor",
                icon: "🩺",
                color: "bg-blue-50 border-blue-100",
                iconBg: "bg-blue-100",
                steps: ["View appointments", "Create medical records", "Prescribe medications", "Order lab tests"],
              },
              {
                role: "Admin",
                icon: "⚙️",
                color: "bg-purple-50 border-purple-100",
                iconBg: "bg-purple-100",
                steps: ["Manage all users", "Create invoices", "Track payments", "Hospital overview"],
              },
            ].map((item, i) => (
              <motion.div
                key={item.role}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15 }}
                viewport={{ once: true }}
                className={`rounded-2xl p-6 border ${item.color}`}
              >
                <div className={`w-12 h-12 ${item.iconBg} rounded-xl flex items-center justify-center text-2xl mb-4`}>
                  {item.icon}
                </div>
                <h3 className="font-bold text-gray-900 text-lg mb-4">{item.role}</h3>
                <ul className="space-y-2">
                  {item.steps.map((step, j) => (
                    <li key={j} className="flex items-center gap-2 text-sm text-gray-600">
                      <span className="w-5 h-5 bg-white rounded-full flex items-center justify-center text-xs font-bold text-gray-400 border">
                        {j + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────── */}
      <section className="py-24 bg-gradient-to-br from-teal-600 to-cyan-700 relative overflow-hidden">
        {/* Background 3D */}
        <div className="absolute inset-0 opacity-20">
          <Canvas camera={{ position: [0, 0, 5] }}>
            <Stars radius={50} depth={20} count={2000} factor={3} fade />
            <FloatingOrb position={[-3, 1, 0]}  color="white" speed={0.5} size={1.5} distort={0.4} />
            <FloatingOrb position={[3, -1, 0]}  color="white" speed={0.8} size={1.0} distort={0.5} />
          </Canvas>
        </div>

        <div className="relative z-10 max-w-3xl mx-auto text-center px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to transform your hospital?
            </h2>
            <p className="text-teal-100 text-lg mb-8">
              Join NovaCare today. Set up in minutes, secure from day one.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <button
                onClick={() => navigate("/register")}
                className="bg-white text-teal-700 px-8 py-3.5 rounded-xl font-semibold hover:bg-teal-50 transition-colors shadow-lg"
              >
                Create free account →
              </button>
              <button
                onClick={() => navigate("/login")}
                className="border-2 border-white/40 text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-white/10 transition-colors"
              >
                Sign in
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="bg-gray-900 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">N</span>
              </div>
              <div>
                <span className="font-bold text-white">NovaCare</span>
                <span className="text-gray-500 text-sm ml-1">Medical Center</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm">
              Built with FastAPI · PostgreSQL · React · Three.js
            </p>
            <p className="text-gray-600 text-sm">
              © 2026 NovaCare. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}