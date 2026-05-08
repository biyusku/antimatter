import { useRef, useMemo, useState, useCallback, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import * as THREE from "three";
import { useSimStore } from "../store/simulationStore";

// ── Constants ────────────────────────────────────────────────────────────────
const BOUNDS = 8;
const SPEED_MIN = 1.5;
const SPEED_MAX = 3.5;
const ANNIHILATION_DIST_SQ = 0.5 * 0.5;
const FLASH_LIFETIME = 0.65; // seconds
const MAX_PARTICLES = 300; // instanced mesh capacity

// ── Helpers ──────────────────────────────────────────────────────────────────
function randRange(lo, hi) {
  return lo + Math.random() * (hi - lo);
}

function makeParticle() {
  const speed = randRange(SPEED_MIN, SPEED_MAX);
  const theta = Math.random() * Math.PI * 2;
  const phi = Math.acos(2 * Math.random() - 1);
  return {
    pos: [
      randRange(-BOUNDS, BOUNDS),
      randRange(-BOUNDS, BOUNDS),
      randRange(-BOUNDS, BOUNDS),
    ],
    vel: [
      speed * Math.sin(phi) * Math.cos(theta),
      speed * Math.sin(phi) * Math.sin(theta),
      speed * Math.cos(phi),
    ],
  };
}

function bounceParticle(p) {
  for (let ax = 0; ax < 3; ax++) {
    if (p.pos[ax] > BOUNDS) {
      p.pos[ax] = BOUNDS;
      p.vel[ax] = -Math.abs(p.vel[ax]);
    } else if (p.pos[ax] < -BOUNDS) {
      p.pos[ax] = -BOUNDS;
      p.vel[ax] = Math.abs(p.vel[ax]);
    }
  }
}

// ── Annihilation flash — self-contained, no store deps ───────────────────────
function Flash({ position, onExpire }) {
  const mesh = useRef();
  const mat = useRef();
  const age = useRef(0);

  useFrame((_, dt) => {
    if (!mesh.current) return;
    age.current += dt;
    const t = Math.min(age.current / FLASH_LIFETIME, 1);
    mesh.current.scale.setScalar(0.3 + t * 2.2);
    if (mat.current) mat.current.opacity = 1 - t;
    if (age.current >= FLASH_LIFETIME) onExpire();
  });

  return (
    <mesh ref={mesh} position={position}>
      <sphereGeometry args={[0.3, 10, 10]} />
      <meshBasicMaterial
        ref={mat}
        color="#ffe060"
        transparent
        depthWrite={false}
      />
    </mesh>
  );
}

// ── Core simulation ───────────────────────────────────────────────────────────
// Particle state lives entirely in mutable refs (never triggers re-renders).
// Flash state uses a local useState in Scene, lifted via callback.
function Simulation({ onAnnihilation }) {
  const isRunning = useSimStore((s) => s.isRunning);
  const particleCount = useSimStore((s) => s.config.particle_count);

  const matterParticles = useRef([]);
  const antimatterParticles = useRef([]);
  const prevRunning = useRef(false);

  const matterMesh = useRef();
  const antimatterMesh = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);

  // Reinitialise whenever simulation starts (isRunning flips false→true)
  useEffect(() => {
    if (!isRunning) return;
    const half = Math.max(1, Math.floor(particleCount / 2));
    const clamped = Math.min(half, MAX_PARTICLES);
    matterParticles.current = Array.from({ length: clamped }, makeParticle);
    antimatterParticles.current = Array.from({ length: clamped }, makeParticle);
  }, [isRunning, particleCount]);

  useFrame((_, dt) => {
    if (!isRunning) {
      prevRunning.current = false;
      return;
    }
    prevRunning.current = true;

    const matter = matterParticles.current;
    const antimatter = antimatterParticles.current;

    // Integrate positions
    for (const p of matter) {
      for (let ax = 0; ax < 3; ax++) p.pos[ax] += p.vel[ax] * dt;
      bounceParticle(p);
    }
    for (const p of antimatter) {
      for (let ax = 0; ax < 3; ax++) p.pos[ax] += p.vel[ax] * dt;
      bounceParticle(p);
    }

    // O(n×m) annihilation detection — fine for n,m < MAX_PARTICLES
    const deadM = new Uint8Array(matter.length);
    const deadA = new Uint8Array(antimatter.length);
    let anyDead = false;

    for (let m = 0; m < matter.length; m++) {
      if (deadM[m]) continue;
      const mp = matter[m].pos;
      for (let a = 0; a < antimatter.length; a++) {
        if (deadA[a]) continue;
        const ap = antimatter[a].pos;
        const dx = mp[0] - ap[0];
        const dy = mp[1] - ap[1];
        const dz = mp[2] - ap[2];
        if (dx * dx + dy * dy + dz * dz < ANNIHILATION_DIST_SQ) {
          deadM[m] = 1;
          deadA[a] = 1;
          anyDead = true;
          onAnnihilation([
            (mp[0] + ap[0]) * 0.5,
            (mp[1] + ap[1]) * 0.5,
            (mp[2] + ap[2]) * 0.5,
          ]);
          break;
        }
      }
    }

    if (anyDead) {
      matterParticles.current = matter.filter((_, i) => !deadM[i]);
      antimatterParticles.current = antimatter.filter((_, i) => !deadA[i]);
    }

    // Sync instanced meshes — matter (blue protons)
    if (matterMesh.current) {
      const live = matterParticles.current;
      for (let i = 0; i < live.length; i++) {
        dummy.position.set(live[i].pos[0], live[i].pos[1], live[i].pos[2]);
        dummy.updateMatrix();
        matterMesh.current.setMatrixAt(i, dummy.matrix);
      }
      matterMesh.current.count = live.length;
      matterMesh.current.instanceMatrix.needsUpdate = true;
    }

    // Sync instanced meshes — antimatter (red antiprotons)
    if (antimatterMesh.current) {
      const live = antimatterParticles.current;
      for (let i = 0; i < live.length; i++) {
        dummy.position.set(live[i].pos[0], live[i].pos[1], live[i].pos[2]);
        dummy.updateMatrix();
        antimatterMesh.current.setMatrixAt(i, dummy.matrix);
      }
      antimatterMesh.current.count = live.length;
      antimatterMesh.current.instanceMatrix.needsUpdate = true;
    }
  });

  return (
    <>
      {/* Matter — blue */}
      <instancedMesh ref={matterMesh} args={[null, null, MAX_PARTICLES]}>
        <sphereGeometry args={[0.18, 10, 10]} />
        <meshStandardMaterial
          color="#4499ff"
          emissive="#002266"
          emissiveIntensity={1.1}
          roughness={0.3}
          metalness={0.2}
        />
      </instancedMesh>

      {/* Antimatter — red */}
      <instancedMesh ref={antimatterMesh} args={[null, null, MAX_PARTICLES]}>
        <sphereGeometry args={[0.18, 10, 10]} />
        <meshStandardMaterial
          color="#ff2244"
          emissive="#cc0020"
          emissiveIntensity={1.1}
          roughness={0.3}
          metalness={0.2}
        />
      </instancedMesh>
    </>
  );
}

// ── Scene ─────────────────────────────────────────────────────────────────────
// Owns flash list as local state so Three.js sub-tree handles its own lifecycle.
let _flashSeq = 0;

function Scene() {
  const [flashes, setFlashes] = useState([]);

  const addFlash = useCallback((position) => {
    const id = ++_flashSeq;
    setFlashes((prev) => [...prev, { id, position }]);
  }, []);

  const removeFlash = useCallback((id) => {
    setFlashes((prev) => prev.filter((f) => f.id !== id));
  }, []);

  return (
    <>
      <ambientLight intensity={0.25} />
      <pointLight position={[12, 12, 12]} intensity={1.4} color="#ffffff" />
      <pointLight position={[-12, -8, -10]} intensity={0.7} color="#4466ff" />
      <pointLight position={[0, -14, 0]} intensity={0.4} color="#ff3344" />

      <Stars radius={80} depth={60} count={5000} factor={4} fade speed={0.4} />

      <Simulation onAnnihilation={addFlash} />

      {flashes.map((f) => (
        <Flash
          key={f.id}
          position={f.position}
          onExpire={() => removeFlash(f.id)}
        />
      ))}

      <OrbitControls
        enablePan={false}
        minDistance={6}
        maxDistance={50}
        autoRotate
        autoRotateSpeed={0.3}
      />

      <fog attach="fog" args={["#020408", 35, 90]} />
    </>
  );
}

// ── Root export ───────────────────────────────────────────────────────────────
export default function ParticleCanvas() {
  return (
    <Canvas
      camera={{ position: [0, 6, 18], fov: 55 }}
      gl={{ antialias: true, alpha: false }}
      dpr={[1, 1.5]}
    >
      <color attach="background" args={["#020408"]} />
      <Scene />
    </Canvas>
  );
}
