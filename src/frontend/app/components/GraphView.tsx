"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchGraph, fetchNodeDetail, GraphData, GraphNode } from "../lib/api";

// react-force-graph-2d is a canvas-based library, needs dynamic import
import dynamic from "next/dynamic";
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

const NODE_COLORS: Record<string, string> = {
  SalesOrder: "#3b82f6",
  Delivery: "#10b981",
  BillingDocument: "#f59e0b",
  Customer: "#8b5cf6",
  Product: "#ef4444",
  Plant: "#6366f1",
  JournalEntry: "#ec4899",
  Payment: "#14b8a6",
};

// force-graph nodes get x/y coords at runtime
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ForceNode = any;

interface Props {
  onNodeSelect: (node: GraphNode | null) => void;
}

export default function GraphView({ onNodeSelect }: Props) {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);

  useEffect(() => {
    fetchGraph()
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  const handleNodeClick = useCallback(
    async (node: ForceNode) => {
      try {
        const detail = await fetchNodeDetail(node.id);
        if (detail.focus) {
          onNodeSelect(detail.focus);
        }
        // zoom to clicked node
        if (graphRef.current) {
          graphRef.current.centerAt(node.x, node.y, 500);
          graphRef.current.zoom(3, 500);
        }
      } catch {
        onNodeSelect({
          id: node.id,
          type: node.type || "Unknown",
          label: node.label || node.id,
          properties: {},
        });
      }
    },
    [onNodeSelect]
  );

  const paintNode = useCallback((node: ForceNode, ctx: CanvasRenderingContext2D) => {
    const size = 5;
    const color = NODE_COLORS[node.type] || "#94a3b8";

    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 0.5;
    ctx.stroke();

    // label
    ctx.font = "3px Inter, sans-serif";
    ctx.fillStyle = "#e2e8f0";
    ctx.textAlign = "center";
    ctx.fillText(node.label?.slice(0, 20) || "", node.x, node.y + size + 4);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400" />
        <span className="ml-3 text-slate-400">Loading graph…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-400">
        Graph load failed: {error}
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-slate-950 rounded-lg overflow-hidden relative">
      {/* Legend */}
      <div className="absolute top-3 left-3 z-10 bg-slate-900/90 backdrop-blur rounded-lg p-3 text-xs">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2 mb-1">
            <span
              className="w-3 h-3 rounded-full inline-block"
              style={{ backgroundColor: color }}
            />
            <span className="text-slate-300">{type}</span>
          </div>
        ))}
      </div>

      {data && (
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          nodeCanvasObject={paintNode}
          onNodeClick={handleNodeClick}
          linkColor={() => "#334155"}
          linkWidth={0.5}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          backgroundColor="#020617"
          width={typeof window !== "undefined" ? window.innerWidth * 0.6 : 800}
          height={typeof window !== "undefined" ? window.innerHeight - 64 : 600}
          cooldownTicks={100}
          enableNodeDrag={true}
        />
      )}
    </div>
  );
}
