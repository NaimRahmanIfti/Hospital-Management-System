// src/components/3d/HeroScene.jsx
import { useRef, useMemo } from "react"
import { Canvas, useFrame } from "@react-three/fiber"
import * as THREE from "three"

// ── Holographic grid floor ─────────────────────────────────────
function HoloGrid() {
  const ref = useRef()
  const uniforms = useMemo(() => ({
    u_time:  { value: 0 },
    u_color: { value: new THREE.Color("#14b8a6") },
  }), [])

  useFrame((s) => { uniforms.u_time.value = s.clock.elapsedTime })

  return (
    <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} position={[0, -4, 0]}>
      <planeGeometry args={[30, 30, 30, 30]} />
      <shaderMaterial
        uniforms={uniforms}
        transparent
        wireframe
        vertexShader={`
          uniform float u_time;
          varying vec2 vUv;
          void main() {
            vUv = uv;
            vec3 pos = position;
            float wave = sin(pos.x * 0.5 + u_time) * 0.3 +
                         sin(pos.y * 0.5 + u_time * 0.7) * 0.2;
            pos.z += wave;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          }
        `}
        fragmentShader={`
          uniform vec3 u_color;
          uniform float u_time;
          varying vec2 vUv;
          void main() {
            float dist = length(vUv - 0.5);
            float alpha = (1.0 - dist * 2.0) * 0.3;
            alpha *= sin(u_time * 0.5) * 0.2 + 0.8;
            gl_FragColor = vec4(u_color, alpha);
          }
        `}
      />
    </mesh>
  )
}

// ── Morphing torus knot ────────────────────────────────────────
function MorphTorusKnot() {
  const mesh = useRef()
  const uniforms = useMemo(() => ({
    u_time:   { value: 0 },
    u_color1: { value: new THREE.Color("#0d9488") },
    u_color2: { value: new THREE.Color("#6366f1") },
    u_color3: { value: new THREE.Color("#0ea5e9") },
  }), [])

  useFrame((s) => {
    uniforms.u_time.value = s.clock.elapsedTime
    mesh.current.rotation.x = s.clock.elapsedTime * 0.2
    mesh.current.rotation.y = s.clock.elapsedTime * 0.15
  })

  return (
    <mesh ref={mesh} position={[0, 0.5, 0]}>
      <torusKnotGeometry args={[1.4, 0.45, 200, 20, 2, 3]} />
      <shaderMaterial
        uniforms={uniforms}
        transparent
        side={THREE.DoubleSide}
        vertexShader={`
          uniform float u_time;
          varying vec3 vNormal;
          varying vec3 vPos;
          varying float vNoise;

          float hash(float n) { return fract(sin(n) * 43758.5453123); }
          float noise(vec3 x) {
            vec3 p = floor(x);
            vec3 f = fract(x);
            f = f * f * (3.0 - 2.0 * f);
            float n = p.x + p.y * 157.0 + 113.0 * p.z;
            return mix(mix(mix(hash(n+0.0),hash(n+1.0),f.x),
                           mix(hash(n+157.0),hash(n+158.0),f.x),f.y),
                       mix(mix(hash(n+113.0),hash(n+114.0),f.x),
                           mix(hash(n+270.0),hash(n+271.0),f.x),f.y),f.z);
          }

          void main() {
            vNormal = normal;
            vPos = position;
            float n = noise(position * 1.5 + u_time * 0.3) * 0.2;
            vNoise = n;
            vec3 newPos = position + normal * n;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPos, 1.0);
          }
        `}
        fragmentShader={`
          uniform float u_time;
          uniform vec3 u_color1;
          uniform vec3 u_color2;
          uniform vec3 u_color3;
          varying vec3 vNormal;
          varying vec3 vPos;
          varying float vNoise;

          void main() {
            float t = sin(u_time * 0.4) * 0.5 + 0.5;
            float t2 = sin(u_time * 0.3 + 2.0) * 0.5 + 0.5;

            vec3 color = mix(u_color1, u_color2, t);
            color = mix(color, u_color3, t2 * 0.5);
            color += vNoise * 0.5;

            // Fresnel
            vec3 viewDir = normalize(cameraPosition - vPos);
            float fresnel = pow(1.0 - max(dot(vNormal, viewDir), 0.0), 3.0);
            color += fresnel * vec3(0.4, 1.0, 1.0) * 0.6;

            // Scanline
            float scan = sin(vPos.y * 20.0 + u_time * 3.0) * 0.05 + 0.95;
            color *= scan;

            gl_FragColor = vec4(color, 0.92);
          }
        `}
      />
    </mesh>
  )
}

// ── Floating holographic panels ────────────────────────────────
function HoloPanel({ position, rotation, width, height, color }) {
  const mesh = useRef()
  const uniforms = useMemo(() => ({
    u_time:  { value: 0 },
    u_color: { value: new THREE.Color(color) },
  }), [color])

  useFrame((s) => {
    uniforms.u_time.value = s.clock.elapsedTime
    mesh.current.position.y = position[1] + Math.sin(s.clock.elapsedTime * 0.7 + position[0]) * 0.15
  })

  return (
    <mesh ref={mesh} position={position} rotation={rotation}>
      <planeGeometry args={[width, height, 10, 10]} />
      <shaderMaterial
        uniforms={uniforms}
        transparent
        side={THREE.DoubleSide}
        vertexShader={`
          varying vec2 vUv;
          void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `}
        fragmentShader={`
          uniform vec3 u_color;
          uniform float u_time;
          varying vec2 vUv;

          void main() {
            // Border
            float border = 0.04;
            float bx = step(border, vUv.x) * step(vUv.x, 1.0 - border);
            float by = step(border, vUv.y) * step(vUv.y, 1.0 - border);
            float inner = bx * by;

            // Scanlines
            float scan = sin(vUv.y * 40.0 + u_time * 2.0) * 0.06 + 0.94;

            // Flicker
            float flicker = sin(u_time * 8.0) * 0.02 + 0.98;

            // Data bars (fake chart)
            float barCount = 8.0;
            float barX = fract(vUv.x * barCount);
            float barIdx = floor(vUv.x * barCount);
            float barH = 0.3 + sin(barIdx * 1.7 + u_time * 0.8) * 0.25 + 0.25;
            float bar = step(1.0 - barH, vUv.y) * step(barX, 0.7);

            vec3 color = u_color;
            float alpha = (1.0 - inner) * 0.9   // border
                        + inner * 0.08            // background
                        + bar * 0.5 * inner       // bars
                        ;
            alpha *= scan * flicker;

            gl_FragColor = vec4(color, alpha * 0.85);
          }
        `}
      />
    </mesh>
  )
}

// ── Particle field ─────────────────────────────────────────────
function ParticleField() {
  const ref = useRef()
  const count = 4000

  const { positions, colors, sizes } = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const colors    = new Float32Array(count * 3)
    const sizes     = new Float32Array(count)
    const palette   = [
      new THREE.Color("#14b8a6"),
      new THREE.Color("#0ea5e9"),
      new THREE.Color("#6366f1"),
      new THREE.Color("#a78bfa"),
      new THREE.Color("#f0abfc"),
      new THREE.Color("#ffffff"),
    ]

    for (let i = 0; i < count; i++) {
      // Spiral galaxy formation
      const arm    = i % 3
      const t      = (i / count) * Math.PI * 8
      const r      = 3 + (i / count) * 10
      const spread = (Math.random() - 0.5) * 2

      positions[i * 3]     = Math.cos(t + arm * 2.1) * r + spread
      positions[i * 3 + 1] = (Math.random() - 0.5) * 3
      positions[i * 3 + 2] = Math.sin(t + arm * 2.1) * r + spread

      const c = palette[Math.floor(Math.random() * palette.length)]
      colors[i * 3]     = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
      sizes[i] = Math.random() * 2 + 0.5
    }
    return { positions, colors, sizes }
  }, [])

  useFrame((s) => {
    if (ref.current) {
      ref.current.rotation.y = s.clock.elapsedTime * 0.03
    }
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color"    args={[colors, 3]}    />
      </bufferGeometry>
      <pointsMaterial
        size={0.07}
        vertexColors
        transparent
        opacity={0.75}
        sizeAttenuation
      />
    </points>
  )
}

// ── Heartbeat line ─────────────────────────────────────────────
function Heartbeat() {
  const ref = useRef()
  const count = 300

  const positions = useMemo(() => new Float32Array(count * 3), [])

  useFrame((s) => {
    const t = s.clock.elapsedTime
    for (let i = 0; i < count; i++) {
      const x = (i / count) * 14 - 7
      const p = (i / count)
      const phase = (t * 0.6) % 1
      const local = (p - phase + 1) % 1

      let y = 0
      if      (local < 0.04) y = local / 0.04 * 0.2
      else if (local < 0.07) y = 0.2 - (local - 0.04) / 0.03 * 0.5
      else if (local < 0.10) y = -0.3 + (local - 0.07) / 0.03 * 1.6
      else if (local < 0.12) y = 1.3 - (local - 0.10) / 0.02 * 1.8
      else if (local < 0.15) y = -0.5 + (local - 0.12) / 0.03 * 0.7
      else if (local < 0.19) y = 0.2 - (local - 0.15) / 0.04 * 0.2
      else y = Math.sin(local * 40.0) * 0.02

      positions[i * 3]     = x
      positions[i * 3 + 1] = y - 3.8
      positions[i * 3 + 2] = 0
    }
    if (ref.current) {
      ref.current.geometry.attributes.position.needsUpdate = true
    }
  })

  return (
    <line ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial color="#14b8a6" transparent opacity={0.8} />
    </line>
  )
}

// ── Orbiting spheres ───────────────────────────────────────────
function OrbitingSpheres() {
  const group = useRef()
  useFrame((s) => {
    if (group.current) {
      group.current.rotation.y = s.clock.elapsedTime * 0.4
      group.current.rotation.x = s.clock.elapsedTime * 0.15
    }
  })

  const spheres = [
    { pos: [3.5, 0, 0],   color: "#14b8a6", size: 0.25 },
    { pos: [-3.5, 0, 0],  color: "#0ea5e9", size: 0.2  },
    { pos: [0, 3.5, 0],   color: "#a78bfa", size: 0.18 },
    { pos: [0, -3.5, 0],  color: "#f0abfc", size: 0.22 },
    { pos: [0, 0, 3.5],   color: "#34d399", size: 0.2  },
    { pos: [0, 0, -3.5],  color: "#fb923c", size: 0.15 },
  ]

  return (
    <group ref={group}>
      {/* Orbit ring */}
      <mesh>
        <torusGeometry args={[3.5, 0.015, 8, 100]} />
        <meshStandardMaterial color="#14b8a6" transparent opacity={0.2} emissive="#14b8a6" emissiveIntensity={0.3} />
      </mesh>
      {spheres.map((s, i) => (
        <mesh key={i} position={s.pos}>
          <sphereGeometry args={[s.size, 16, 16]} />
          <meshStandardMaterial color={s.color} emissive={s.color} emissiveIntensity={0.5} />
        </mesh>
      ))}
    </group>
  )
}

// ── DNA double helix ───────────────────────────────────────────
function DNA() {
  const group = useRef()
  useFrame((s) => {
    if (group.current) group.current.rotation.y = s.clock.elapsedTime * 0.3
  })

  const count = 30
  const colors = ["#14b8a6", "#0ea5e9", "#a78bfa", "#f0abfc"]

  return (
    <group ref={group} position={[-4.5, 0, 0]}>
      {Array.from({ length: count }, (_, i) => {
        const angle = (i / count) * Math.PI * 5
        const y     = (i / count) * 9 - 4.5
        return (
          <group key={i}>
            <mesh position={[Math.cos(angle) * 0.6, y, Math.sin(angle) * 0.6]}>
              <sphereGeometry args={[0.08, 8, 8]} />
              <meshStandardMaterial color={colors[i % 4]} emissive={colors[i % 4]} emissiveIntensity={0.7} />
            </mesh>
            <mesh position={[Math.cos(angle + Math.PI) * 0.6, y, Math.sin(angle + Math.PI) * 0.6]}>
              <sphereGeometry args={[0.08, 8, 8]} />
              <meshStandardMaterial color={colors[(i + 2) % 4]} emissive={colors[(i + 2) % 4]} emissiveIntensity={0.7} />
            </mesh>
          </group>
        )
      })}
    </group>
  )
}

// ── Floating medical crosses ───────────────────────────────────
function MedCross({ position, scale = 1 }) {
  const ref = useRef()
  useFrame((s) => {
    if (ref.current) {
      ref.current.rotation.z = Math.sin(s.clock.elapsedTime * 0.5 + position[0]) * 0.2
      ref.current.position.y = position[1] + Math.sin(s.clock.elapsedTime + position[2]) * 0.2
    }
  })
  return (
    <group ref={ref} position={position} scale={scale}>
      <mesh><boxGeometry args={[0.06, 0.28, 0.06]} /><meshStandardMaterial color="#14b8a6" emissive="#14b8a6" emissiveIntensity={1} /></mesh>
      <mesh><boxGeometry args={[0.28, 0.06, 0.06]} /><meshStandardMaterial color="#14b8a6" emissive="#14b8a6" emissiveIntensity={1} /></mesh>
    </group>
  )
}

// ── Main export ────────────────────────────────────────────────
export default function HeroScene() {
  return (
    <Canvas
      camera={{ position: [0, 1, 10], fov: 52 }}
      style={{ background: "transparent" }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true }}
    >
      <ambientLight intensity={0.15} />
      <pointLight position={[10, 10, 10]}   intensity={2}   color="#14b8a6" />
      <pointLight position={[-10, -10, -5]} intensity={1.2} color="#0ea5e9" />
      <pointLight position={[0, 10, 0]}     intensity={0.8} color="#a78bfa" />
      <pointLight position={[5, -5, 8]}     intensity={0.6} color="#f0abfc" />

      {/* Spiral galaxy particles */}
      <ParticleField />

      {/* Holographic grid floor */}
      <HoloGrid />

      {/* Main morphing torus knot */}
      <MorphTorusKnot />

      {/* Orbiting spheres */}
      <OrbitingSpheres />

      {/* DNA on the left */}
      <DNA />

      {/* Floating holographic data panels */}
      <HoloPanel position={[5, 1.5, -2]}  rotation={[0, -0.4, 0]} width={2.2} height={1.5} color="#14b8a6" />
      <HoloPanel position={[5, -1, -2]}   rotation={[0, -0.4, 0]} width={2.2} height={1.0} color="#0ea5e9" />
      <HoloPanel position={[-5.5, 1, -2]} rotation={[0, 0.4, 0]}  width={1.8} height={1.2} color="#a78bfa" />

      {/* EKG line */}
      <Heartbeat />

      {/* Medical crosses */}
      <MedCross position={[2, 3.5, -1]}   scale={1.2} />
      <MedCross position={[-2, -3, -1]}   scale={0.9} />
      <MedCross position={[5.5, -2, 0]}   scale={0.7} />
    </Canvas>
  )
}