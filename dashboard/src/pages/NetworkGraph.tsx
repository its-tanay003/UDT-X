import React, { useState, useEffect } from "react";
import {
  Globe,
  Layers,
  Network,
  Radio,
  Search,
  ShieldAlert,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { fetchGraphTopology, type GraphData, type GraphNode } from "../lib/api/graph";
import { ListeningSphere } from "../components/ListeningSphere";

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
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-2 p-1 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 font-mono text-xs">
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
        </div>
      </div>

      {/* Main Grid: Interactive Canvas + Node Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Canvas Column */}
        <div id="tour-graph-canvas" className="lg:col-span-8 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 relative overflow-hidden">
          <div className="flex items-center justify-between mb-3 font-mono text-xs text-[#8A95AA]">
            <span>ORBIT / PAN / ZOOM ENABLED</span>
            <span className="text-[#3FC7D4]">
              {graphData.nodes.length} ACTIVE NODES // {graphData.edges.length} ARCS
            </span>
          </div>

          {activeTab === "3D_SPHERE" ? (
            <ListeningSphere
              nodes={graphData.nodes}
              edges={graphData.edges}
              interactive={true}
              density="high"
              height="540px"
              onNodeClick={handleNodeClick}
            />
          ) : (
            <div className="h-135 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 p-4 overflow-y-auto font-mono text-xs space-y-2">
              {graphData.nodes.map((node) => (
                <div
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                    selectedNode?.id === node.id
                      ? "bg-[#1B2540] border-[#3FC7D4]"
                      : "bg-[#131B2E] border-[#3FC7D4]/10 hover:border-[#3FC7D4]/30"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{
                        backgroundColor:
                          node.severity === "critical"
                            ? "#FF4757"
                            : node.severity === "high"
                            ? "#FF8A3D"
                            : "#3FC7D4",
                      }}
                    />
                    <div>
                      <div className="font-bold text-[#E7ECF5]">{node.label}</div>
                      <div className="text-[10px] text-[#8A95AA] uppercase">{node.type}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] text-[#3FC7D4]">
                      Risk: {node.risk || 20}/100
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Node Inspector Column */}
        <div id="tour-graph-inspector" className="lg:col-span-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 space-y-4 font-mono text-xs">
          <h3 className="font-bold text-[#E7ECF5] uppercase tracking-wider pb-3 border-b border-[#3FC7D4]/15 flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-[#3FC7D4]" />
            Node Telemetry Inspector
          </h3>

          {selectedNode ? (
            <div className="space-y-4">
              <div className="p-3.5 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15">
                <span className="text-[10px] text-[#8A95AA] uppercase">Target Entity</span>
                <div className="text-sm font-bold text-[#E7ECF5] mt-1">{selectedNode.label}</div>
                <div className="text-xs text-[#3FC7D4] mt-0.5">Type: {selectedNode.type}</div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between p-2.5 rounded bg-[#0B1220] border border-[#3FC7D4]/10">
                  <span className="text-[#8A95AA]">Risk Rating:</span>
                  <span className="text-[#FF4757] font-bold">
                    {selectedNode.risk || 45} / 100
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded bg-[#0B1220] border border-[#3FC7D4]/10">
                  <span className="text-[#8A95AA]">Severity Level:</span>
                  <span className="text-[#E7ECF5] uppercase">
                    {selectedNode.severity || "NOMINAL"}
                  </span>
                </div>
                <div className="flex justify-between p-2.5 rounded bg-[#0B1220] border border-[#3FC7D4]/10">
                  <span className="text-[#8A95AA]">Connected Flows:</span>
                  <span className="text-[#3FC7D4]">
                    {graphData.edges.filter(
                      (e) => e.source === selectedNode.id || e.target === selectedNode.id
                    ).length} Arcs
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-[#8A95AA] space-y-2">
              <Layers className="w-8 h-8 mx-auto text-[#3FC7D4] opacity-50" />
              <p>Click on any node on the 3D Sphere or Topology list to inspect its connected attack edges.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
