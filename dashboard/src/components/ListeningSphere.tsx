import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Sphere } from "@react-three/drei";
import * as THREE from "three";

interface ListeningSphereProps {
  interactive?: boolean;
  density?: "low" | "high";
  height?: string;
  onNodeClick?: (nodeId: string) => void;
}

// Fixed mathematical node distribution on sphere surface
const SPHERE_NODES = [
  { id: "192.168.1.105", pos: [0.8, 0.5, 0.3], severity: "critical", label: "Host 105" },
  { id: "10.0.0.1", pos: [-0.6, 0.7, -0.4], severity: "normal", label: "DC-01" },
  { id: "10.0.0.2", pos: [-0.7, -0.5, 0.5], severity: "normal", label: "DB-02" },
  { id: "198.51.100.22", pos: [0.5, -0.8, -0.4], severity: "critical", label: "C2 Server" },
  { id: "192.168.1.1", pos: [0.1, 0.9, -0.4], severity: "normal", label: "Gateway" },
  { id: "203.0.113.5", pos: [-0.8, 0.2, 0.6], severity: "warn", label: "Target" },
  { id: "172.16.0.40", pos: [0.3, -0.6, 0.7], severity: "normal", label: "Sensor" },
];

function SphereMesh({ density = "high" }: { density: "low" | "high" }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const particleGroupRef = useRef<THREE.Group>(null);

  // Inward passive particles: strictly travel from surface (r=1) inward toward center (r=0)
  const particleCount = density === "high" ? 180 : 60;
  const particles = useMemo(() => {
    const arr = [];
    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const dir = new THREE.Vector3(
        Math.sin(phi) * Math.cos(theta),
        Math.sin(phi) * Math.sin(theta),
        Math.cos(phi)
      );
      arr.push({
        direction: dir,
        distance: Math.random(), // 0.0 (center) to 1.0 (surface)
        speed: 0.003 + Math.random() * 0.005,
      });
    }
    return arr;
  }, [particleCount]);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.08;
      meshRef.current.rotation.x += delta * 0.02;
    }

    // Advance particles strictly inward
    if (particleGroupRef.current) {
      particleGroupRef.current.children.forEach((child, idx) => {
        const p = particles[idx];
        if (p) {
          p.distance -= p.speed;
          if (p.distance <= 0.05) {
            p.distance = 1.0; // Reset at the perimeter surface
          }
          child.position.copy(p.direction).multiplyScalar(p.distance * 1.8);
        }
      });
    }
  });

  return (
    <group ref={meshRef}>
      {/* Translucent Perimeter Wireframe */}
      <Sphere args={[1.8, 24, 24]}>
        <meshBasicMaterial
          wireframe
          color="#3FC7D4"
          transparent
          opacity={0.12}
        />
      </Sphere>

      {/* Internal Listening Core */}
      <Sphere args={[0.3, 16, 16]}>
        <meshBasicMaterial
          color="#3FC7D4"
          transparent
          opacity={0.25}
        />
      </Sphere>

      {/* Surface Host Nodes */}
      {SPHERE_NODES.map((node, i) => {
        const posVec = new THREE.Vector3(...(node.pos as [number, number, number])).normalize().multiplyScalar(1.8);
        const nodeColor =
          node.severity === "critical"
            ? "#FF4757"
            : node.severity === "warn"
            ? "#FF8A3D"
            : "#3FC7D4";

        return (
          <mesh key={i} position={posVec}>
            <sphereGeometry args={[0.06, 12, 12]} />
            <meshBasicMaterial color={nodeColor} />
          </mesh>
        );
      })}

      {/* Inward One-Way Traffic Particles */}
      <group ref={particleGroupRef}>
        {particles.map((_, idx) => (
          <mesh key={idx}>
            <sphereGeometry args={[0.02, 6, 6]} />
            <meshBasicMaterial color="#3FC7D4" transparent opacity={0.6} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

export const ListeningSphere: React.FC<ListeningSphereProps> = ({
  interactive = false,
  density = "high",
  height = "320px",
  onNodeClick,
}) => {
  // Reduced-motion accessibility fallback check
  const prefersReducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (prefersReducedMotion) {
    return (
      <div
        className="w-full flex flex-col items-center justify-center bg-[#0B1220] border border-[#3FC7D4]/20 rounded-xl p-6 relative overflow-hidden"
        style={{ height }}
      >
        <div className="w-32 h-32 rounded-full border-2 border-dashed border-[#3FC7D4]/40 flex items-center justify-center relative">
          <div className="w-4 h-4 rounded-full bg-[#3FC7D4] shadow-[0_0_12px_#3FC7D4]" />
          <div className="absolute top-2 right-4 w-3 h-3 rounded-full bg-[#FF4757] animate-ping" />
        </div>
        <p className="text-xs font-mono text-[#8A95AA] mt-4 uppercase tracking-wider">
          Passive Listening Perimeter (Static Accessible Fallback)
        </p>
      </div>
    );
  }

  return (
    <div className="w-full relative rounded-xl overflow-hidden border border-[#3FC7D4]/15 bg-[#0B1220]" style={{ height }}>
      {/* Sonar Grid Overlay */}
      <div className="absolute inset-0 pointer-events-none z-10 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(11,18,32,0.6)_100%)]" />

      <Canvas camera={{ position: [0, 0, 4.2], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <SphereMesh density={density} />
        {interactive && (
          <OrbitControls
            enablePan={false}
            minDistance={2.5}
            maxDistance={7.0}
            autoRotate={false}
          />
        )}
      </Canvas>

      {/* Perimeter Indicator Label */}
      <div className="absolute bottom-2.5 left-3 z-20 pointer-events-none flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
        <span className="text-[10px] font-mono text-[#8A95AA] uppercase tracking-widest">
          Passive Telemetry Perimeter // Inward Flow Only
        </span>
      </div>
    </div>
  );
};
