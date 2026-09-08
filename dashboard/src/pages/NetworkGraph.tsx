import React, { useState, useEffect } from "react";
import {
  Globe,
  Layers,
  Network,
  Radio,
  Search,
  ShieldAlert,
  HelpCircle,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { fetchGraphTopology, type GraphData, type GraphNode } from "../lib/api/graph";
import { ListeningSphere } from "../components/ListeningSphere";
import { Tooltip } from "../components/Tooltip";

export const NetworkGraphPage: React.FC = () => {
  const { alerts, incidents } = useLiveStore();
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [activeTab, setActiveTab] = useState<"3D_SPHERE" | "2D_TOPOLOGY">("3D_SPHERE");

  useEffect(() => {
    fetchGraphTopology("http://localhost:8000", alerts, incidents).then((data) => {
      setGraphData(data);
    });
  }, [alerts, incidents]);

  const handleNodeClick = (nodeId: string) => {
    const n = graphData.nodes.find((item) => item.id === nodeId);
    if (n) setSelectedNode(n);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-4 border-b border-[#3FC7D4]/15 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#3FC7D4] animate-pulse" />
            <span className="text-[11px] font-mono font-bold tracking-widest text-[#3FC7D4] uppercase">
              Neo4j Real-time Topology & 3D Listening Sphere
            </span>
          </div>
          <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
            Network Evidence Graph
          </h1>
          <p className="text-xs text-[#8A95AA] mt-0.5">
            Every host UDT-X can see, and every flow between them — traffic only ever moves inward.
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-2 p-1 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs">
          <Tooltip content="Three-dimensional hemispherical perimeter representation of incoming flows">
            <button
              onClick={() => setActiveTab("3D_SPHERE")}
              className={`px-3 py-1.5 rounded flex items-center gap-1.5 transition-all ${
                activeTab === "3D_SPHERE"
                  ? "bg-[#3FC7D4]/20 text-[#3FC7D4] font-bold"
                  : "text-[#8A95AA] hover:text-[#E7ECF5]"
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              3D LISTENING SPHERE
            </button>
          </Tooltip>

          <Tooltip content="Two-dimensional structural host/node topology derived from live telemetry">
            <button
              onClick={() => setActiveTab("2D_TOPOLOGY")}
              className={`px-3 py-1.5 rounded flex items-center gap-1.5 transition-all ${
                activeTab === "2D_TOPOLOGY"
                  ? "bg-[#3FC7D4]/20 text-[#3FC7D4] font-bold"
                  : "text-[#8A95AA] hover:text-[#E7ECF5]"
              }`}
            >
              <Network className="w-3.5 h-3.5" />
              TOPOLOGY NODES ({graphData.nodes.length})
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Main Graph Canvas Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Graph Display Area */}
        <div className="lg:col-span-8 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col justify-between min-h-115">
          {activeTab === "3D_SPHERE" ? (
            <div className="w-full flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-[#3FC7D4]" />
                  <span className="font-mono text-xs font-bold text-[#E7ECF5]">
                    3D PASSIVE TAP HEMISPHERE
                  </span>
                </div>
                <span className="text-[10px] font-mono text-[#8A95AA]">
                  {graphData.nodes.length} Nodes // {graphData.edges.length} Ingress Edges
                </span>
              </div>

              <div className="flex-1 flex items-center justify-center">
                <ListeningSphere
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  density="high"
                  height="420px"
                  interactive={true}
                />
              </div>
            </div>
          ) : (
            <div className="w-full flex-1 flex flex-col space-y-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#E7ECF5]">
                  EXTRACTED TOPOLOGY ENTITIES
                </span>
                <span className="text-[10px] font-mono text-[#3FC7D4]">
                  Graph Correlation Active
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-95 overflow-y-auto pr-1">
                {graphData.nodes.map((node) => (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                      selectedNode?.id === node.id
                        ? "bg-[#1B2540] border-[#3FC7D4]"
                        : "bg-[#0B1220] border-[#3FC7D4]/15 hover:border-[#3FC7D4]/40"
                    }`}
                  >
                    <div className="flex items-center justify-between font-mono text-xs">
                      <span className="font-bold text-[#E7ECF5]">{node.label}</span>
                      <span
                        className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase"
                        style={{
                          backgroundColor:
                            node.type === "host" ? "rgba(63,199,212,0.15)" : "rgba(255,138,61,0.15)",
                          color: node.type === "host" ? "#3FC7D4" : "#FF8A3D",
                        }}
                      >
                        {node.type}
                      </span>
                    </div>
                    <div className="mt-2 text-[10px] font-mono text-[#8A95AA] flex justify-between">
                      <span>IP: {node.ip || node.id}</span>
                      <span>Risk: {node.risk || 20}/100</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Selected Entity Inspector Panel */}
        <div className="lg:col-span-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 space-y-4">
          <h3 className="font-mono text-xs font-bold text-[#8A95AA] uppercase tracking-wider">
            ENTITY FORENSIC INSPECTOR
          </h3>

          {selectedNode ? (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/20 space-y-2">
                <div className="flex justify-between">
                  <span className="text-[#8A95AA]">Node ID:</span>
                  <span className="text-[#3FC7D4] font-bold">{selectedNode.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A95AA]">Classification:</span>
                  <span className="text-[#E7ECF5]">{selectedNode.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8A95AA]">Observed IP:</span>
                  <span className="text-[#E7ECF5]">{selectedNode.ip || selectedNode.id}</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-[10px] text-[#8A95AA] uppercase">Isolation / Quarantine Posture:</span>
                <p className="text-xs text-[#E7ECF5] p-3 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 leading-relaxed">
                  UDT-X is operating in <strong>passive one-way listening post</strong> mode. Egress control signals are disabled by hardware data diode policy.
                </p>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 text-center space-y-2 font-mono">
              <Globe className="w-8 h-8 text-[#3FC7D4]/50 mx-auto" />
              <p className="text-xs text-[#8A95AA]">
                Click any node in the 3D Sphere or Topology list to inspect its security posture.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
