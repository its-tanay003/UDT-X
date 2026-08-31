import React, { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Sphere } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";
import type { GraphNode, GraphEdge } from "../lib/api/graph";

interface ListeningSphereProps {
  nodes?: GraphNode[];
  edges?: GraphEdge[];
  interactive?: boolean;
  density?: "low" | "high";
  height?: string;
  onNodeClick?: (nodeId: string) => void;
}

// Deterministic string hasher for stable coordinates on sphere surface (r=1.8)
function getPositionForNodeId(id: string, radius: number = 1.8): THREE.Vector3 {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = (hash << 5) - hash + id.charCodeAt(i);
    hash |= 0;
  }
  const u = Math.abs((hash % 10000) / 10000);
  const v = Math.abs(((hash >> 8) % 10000) / 10000);

  const theta = u * 2.0 * Math.PI;
  const phi = Math.acos(2.0 * v - 1.0);

  const x = radius * Math.sin(phi) * Math.cos(theta);
  const y = radius * Math.sin(phi) * Math.sin(theta);
  const z = radius * Math.cos(phi);

  return new THREE.Vector3(x, y, z);
}

function SphereScene({
  nodes = [],
  edges = [],
  density = "high",
  onNodeClick,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  density: "low" | "high";
  onNodeClick?: (id: string) => void;
}) {
  const meshGroupRef = useRef<THREE.Group>(null);
  const particleGroupRef = useRef<THREE.Group>(null);

  // Map nodes to stable 3D positions
  const nodePositionMap = useMemo(() => {
    const map = new Map<string, THREE.Vector3>();
    nodes.forEach((n) => {
      map.set(n.id, getPositionForNodeId(n.id, 1.8));
    });
    return map;
  }, [nodes]);

  // Construct real 3D Bezier curve arcs along edges (or fallback radial arcs if no edges)
  const realArcs = useMemo(() => {
    if (edges.length === 0) return [];
    const arcs: Array<{
      curve: THREE.QuadraticBezierCurve3;
      edge: GraphEdge;
      color: string;
    }> = [];

    edges.forEach((edge) => {
      const srcPos = nodePositionMap.get(edge.source);
      const dstPos = nodePositionMap.get(edge.target);

      if (srcPos && dstPos) {
        // Compute midpoint curved slightly toward the core (inward curve)
        const mid = new THREE.Vector3()
          .addVectors(srcPos, dstPos)
          .multiplyScalar(0.5)
          .multiplyScalar(0.7); // Inward bias

        const curve = new THREE.QuadraticBezierCurve3(srcPos, mid, dstPos);
        const color =
          edge.severity === "critical"
            ? "#FF4757"
            : edge.severity === "high"
            ? "#FF8A3D"
            : "#3FC7D4";

        arcs.push({ curve, edge, color });
      }
    });
    return arcs;
  }, [edges, nodePositionMap]);

  // One-way inward particles along real arcs (or surface-to-center fallback)
  const particleCount = density === "high" ? Math.max(arcsCount(realArcs.length), 40) : 20;
  function arcsCount(eCount: number) {
    return Math.min(eCount * 4, 120);
  }

  const particleStates = useMemo(() => {
    const arr = [];
    for (let i = 0; i < particleCount; i++) {
      const arcIndex = realArcs.length > 0 ? i % realArcs.length : -1;
      arr.push({
        arcIndex,
        progress: Math.random(), // 0.0 to 1.0
        speed: 0.004 + Math.random() * 0.004,
        radialDir: new THREE.Vector3(
          Math.random() - 0.5,
          Math.random() - 0.5,
          Math.random() - 0.5
        ).normalize(),
        radialDist: Math.random(),
      });
    }
    return arr;
  }, [particleCount, realArcs.length]);

  useFrame((_, delta) => {
    if (meshGroupRef.current) {
      meshGroupRef.current.rotation.y += delta * 0.06;
      meshGroupRef.current.rotation.x += delta * 0.015;
    }

    // Animate particles along real arcs with smooth fade
    if (particleGroupRef.current) {
      particleGroupRef.current.children.forEach((child, idx) => {
        const p = particleStates[idx];
        if (!p) return;

        p.progress += p.speed;
        if (p.progress >= 1.0) {
          p.progress = 0.0;
        }

        // Compute smooth opacity fade (fade in near 0.0, fade out near 1.0)
        let alpha = 1.0;
        if (p.progress < 0.15) {
          alpha = p.progress / 0.15;
        } else if (p.progress > 0.85) {
          alpha = (1.0 - p.progress) / 0.15;
        }

        const mat = (child as THREE.Mesh).material as THREE.MeshBasicMaterial;
        if (mat) {
          mat.opacity = Math.max(0.05, alpha * 0.85);
        }

        if (p.arcIndex >= 0 && realArcs[p.arcIndex]) {
          const pt = realArcs[p.arcIndex].curve.getPoint(p.progress);
          child.position.copy(pt);
        } else {
          // Fallback inward radial flow to center
          p.radialDist -= p.speed;
          if (p.radialDist <= 0.05) p.radialDist = 1.0;
          child.position.copy(p.radialDir).multiplyScalar(p.radialDist * 1.8);
        }
      });
    }
  });

  const hasTelemetry = nodes.length > 0;

  return (
    <group ref={meshGroupRef}>
      {/* Outer Wireframe Perimeter */}
      <Sphere args={[1.8, 28, 28]}>
        <meshBasicMaterial
          wireframe
          color="#3FC7D4"
          transparent
          opacity={hasTelemetry ? 0.12 : 0.08}
        />
      </Sphere>

      {/* Central Passive Ingestion Core */}
      <Sphere args={[0.28, 16, 16]}>
        <meshStandardMaterial
          color="#3FC7D4"
          emissive="#3FC7D4"
          emissiveIntensity={0.6}
          roughness={0.2}
          transparent
          opacity={0.35}
        />
      </Sphere>

      {/* Real Arcs for Connected Telemetry Edges */}
      {realArcs.map((arc, idx) => {
        const points = arc.curve.getPoints(24);
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const lineMat = new THREE.LineBasicMaterial({
          color: arc.color,
          transparent: true,
          opacity: 0.45,
        });
        const lineObj = new THREE.Line(lineGeo, lineMat);
        return <primitive key={idx} object={lineObj} />;
      })}

      {/* Real Host Nodes on Sphere Surface */}
      {nodes.map((node) => {
        const pos = nodePositionMap.get(node.id) || new THREE.Vector3(0, 1.8, 0);
        const nodeColor =
          node.severity === "critical" || (node.risk && node.risk > 85)
            ? "#FF4757"
            : node.severity === "high" || (node.risk && node.risk > 65)
            ? "#FF8A3D"
            : "#3FC7D4";

        const nodeRadius =
          node.type === "incident"
            ? 0.09
            : node.type === "alert"
            ? 0.07
            : 0.055;

        return (
          <mesh
            key={node.id}
            position={pos}
            onClick={(e) => {
              e.stopPropagation();
              onNodeClick && onNodeClick(node.id);
            }}
          >
            <sphereGeometry args={[nodeRadius, 14, 14]} />
            <meshStandardMaterial
              color={nodeColor}
              emissive={nodeColor}
              emissiveIntensity={nodeColor === "#FF4757" ? 1.8 : 0.8}
              roughness={0.1}
            />
          </mesh>
        );
      })}

      {/* Inward Particle Flows */}
      <group ref={particleGroupRef}>
        {particleStates.map((p, idx) => {
          const particleColor =
            p.arcIndex >= 0 && realArcs[p.arcIndex]
              ? realArcs[p.arcIndex].color
              : "#3FC7D4";

          return (
            <mesh key={idx}>
              <sphereGeometry args={[0.022, 6, 6]} />
              <meshBasicMaterial
                color={particleColor}
                transparent
                opacity={0.8}
              />
            </mesh>
          );
        })}
      </group>
    </group>
  );
}

export const ListeningSphere: React.FC<ListeningSphereProps> = ({
  nodes = [],
  edges = [],
  interactive = false,
  density = "high",
  height = "320px",
  onNodeClick,
}) => {
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
          {nodes.some((n) => n.severity === "critical" || (n.risk && n.risk > 85)) && (
            <div className="absolute top-2 right-4 w-3 h-3 rounded-full bg-[#FF4757] animate-ping" />
          )}
        </div>
        <p className="text-xs font-mono text-[#8A95AA] mt-4 uppercase tracking-wider">
          Passive Listening Perimeter (Static Accessible View)
        </p>
      </div>
    );
  }

  const isEmpty = nodes.length === 0;

  return (
    <div
      className="w-full relative rounded-xl overflow-hidden border border-[#3FC7D4]/15 bg-[#0B1220]"
      style={{ height }}
    >
      {/* Background Sonar Grid Overlay */}
      <div className="absolute inset-0 pointer-events-none z-10 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(11,18,32,0.65)_100%)]" />

      {/* Empty State Banner if no telemetry nodes exist yet */}
      {isEmpty && (
        <div className="absolute top-4 left-4 z-20 pointer-events-none flex items-center gap-2 font-mono text-xs text-[#8A95AA]">
          <span className="w-2 h-2 rounded-full bg-[#3FC7D4]" />
          <span>PERIMETER NOMINAL // NO ACTIVE TELEMETRY DETECTED</span>
        </div>
      )}

      <Canvas camera={{ position: [0, 0, 4.3], fov: 45 }}>
        <ambientLight intensity={0.4} />
        {/* Soft directional & rim lighting for physical depth */}
        <directionalLight position={[5, 8, 5]} intensity={0.9} color="#E7ECF5" />
        <pointLight position={[-6, -4, -4]} intensity={0.5} color="#3FC7D4" />

        <SphereScene
          nodes={nodes}
          edges={edges}
          density={density}
          onNodeClick={onNodeClick}
        />

        {/* Postprocessing Bloom Pass */}
        <EffectComposer>
          <Bloom
            luminanceThreshold={0.25}
            luminanceSmoothing={0.9}
            intensity={1.2}
            mipmapBlur
          />
        </EffectComposer>

        {interactive && (
          <OrbitControls
            enablePan={false}
            minDistance={2.4}
            maxDistance={7.5}
            autoRotate={false}
          />
        )}
      </Canvas>

      {/* Bottom Status Tag */}
      <div className="absolute bottom-2.5 left-3 z-20 pointer-events-none flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
        <span className="text-[10px] font-mono text-[#8A95AA] uppercase tracking-widest">
          Passive Telemetry Perimeter // Inward Arcs Only ({nodes.length} Nodes / {edges.length} Flows)
        </span>
      </div>
    </div>
  );
};
