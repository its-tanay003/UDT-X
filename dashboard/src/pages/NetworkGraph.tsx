import React, { useEffect, useState } from "react";
import {
  Activity,
  ArrowLeft,
  Database,
  ExternalLink,
  Layers,
  Network,
  RefreshCw,
  Search,
  Shield,
  ShieldAlert,
} from "lucide-react";
import { useLiveStore } from "../lib/store";
import { fetchGraphTopology, type GraphData, type GraphNode } from "../lib/api/graph";
import { ListeningSphere } from "../components/ListeningSphere";

interface NetworkGraphProps {
  onBack?: () => void;
  onSelectAlert?: (alertId: string) => void;
}

export const NetworkGraphPage: React.FC<NetworkGraphProps> = ({
  onBack,
  onSelectAlert,
}) => {
  const { alerts, incidents } = useLiveStore();
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadGraph = async () => {
      setIsLoading(true);
      const data = await fetchGraphTopology("http://localhost:8000", alerts, incidents);
      setGraphData(data);
      if (data.nodes.length > 0 && !selectedNode) {
        setSelectedNode(data.nodes[0]);
      }
      setIsLoading(false);
    };
    loadGraph();
  }, [alerts, incidents]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#3FC7D4]/15">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="p-2 rounded-lg bg-[#131B2E] border border-[#3FC7D4]/20 text-[#8A95AA] hover:text-[#E7ECF5] transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <div>
            <div className="flex items-center gap-2 font-mono text-xs text-[#3FC7D4]">
              <Network className="w-3.5 h-3.5 text-[#3FC7D4]" />
              <span className="font-bold uppercase tracking-wider">
                Full-Scale Interactive Listening Perimeter Sphere
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-[#E7ECF5] mt-1 tracking-tight">
              Enclave Evidence Graph Topology
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs text-[#8A95AA]">
          <span className="px-3 py-1 rounded bg-[#131B2E] border border-[#3FC7D4]/20 text-[#3FC7D4] font-bold">
            {graphData.nodes.length} NODES // {graphData.edges.length} EDGES
          </span>
        </div>
      </div>

      {/* Grid: Full Interactive Sphere + Side Detail Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Interactive 3D Listening Sphere (Primary Focus) */}
        <div className="lg:col-span-8 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between mb-3 z-20">
            <span className="text-xs font-mono font-bold text-[#E7ECF5] uppercase tracking-wider">
              3D Orbital Wireframe // Passive Inward Telemetry (Orbit / Pan / Zoom)
            </span>
          </div>

          <ListeningSphere
            density="high"
            height="520px"
            interactive={true}
            onNodeClick={(id) => {
              const n = graphData.nodes.find((item) => item.id === id);
              if (n) setSelectedNode(n);
            }}
          />
        </div>

        {/* Side Node Detail Inspector */}
        <div className="lg:col-span-4 rounded-xl bg-[#131B2E] border border-[#3FC7D4]/20 p-5 space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#8A95AA] uppercase tracking-wider">
            Entity Inspector
          </h3>

          {selectedNode ? (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15">
                <span className="text-[10px] text-[#8A95AA] uppercase">ENTITY IDENTIFIER</span>
                <h4 className="text-sm font-bold text-[#3FC7D4] mt-1 break-all">
                  {selectedNode.id}
                </h4>
                <div className="mt-2 flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] bg-[#3FC7D4]/10 text-[#3FC7D4] uppercase border border-[#3FC7D4]/20">
                    TYPE: {selectedNode.type}
                  </span>
                  {selectedNode.risk && (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-[#FF4757]/10 text-[#FF4757] uppercase border border-[#FF4757]/20">
                      RISK: {selectedNode.risk}
                    </span>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-lg bg-[#0B1220] border border-[#3FC7D4]/15 space-y-2">
                <span className="text-[10px] text-[#8A95AA] uppercase">GRAPH CONNECTIONS</span>
                <div className="space-y-1.5 pt-1">
                  {graphData.edges
                    .filter(
                      (e) =>
                        e.source === selectedNode.id || e.target === selectedNode.id
                    )
                    .map((edge) => (
                      <div
                        key={edge.id}
                        className="text-[11px] flex items-center justify-between text-[#E7ECF5]"
                      >
                        <span className="text-[#3FC7D4]">{edge.type}</span>
                        <span className="text-[#8A95AA] truncate ml-2">
                          {edge.source === selectedNode.id ? `→ ${edge.target}` : `← ${edge.source}`}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center text-[#8A95AA] font-mono text-xs py-12">
              Select a node in the graph to inspect entity relationships.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
