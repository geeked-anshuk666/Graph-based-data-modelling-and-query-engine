"use client";

import { useState } from "react";
import GraphView from "./components/GraphView";
import ChatPanel from "./components/ChatPanel";
import NodeDetail from "./components/NodeDetail";
import StatusPage from "./components/StatusPage";
import { GraphNode } from "./lib/api";

type Tab = "graph" | "status";

export default function Home() {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("graph");

  return (
    <div className="h-screen flex flex-col">
      {/* Top bar */}
      <header className="h-14 border-b border-slate-800 flex items-center justify-between px-4 bg-slate-900/80 backdrop-blur shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-bold text-slate-200 tracking-tight">
            SAP O2C Graph Query
          </h1>
          <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded">
            v0.1
          </span>
        </div>

        <nav className="flex gap-1">
          <button
            onClick={() => setActiveTab("graph")}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${
              activeTab === "graph"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Graph + Chat
          </button>
          <button
            onClick={() => setActiveTab("status")}
            className={`px-3 py-1.5 rounded text-sm transition-colors ${
              activeTab === "status"
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Status
          </button>
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        {activeTab === "graph" ? (
          <div className="flex h-full">
            {/* Graph panel — 60% */}
            <div className="w-[60%] h-full border-r border-slate-800">
              <GraphView onNodeSelect={setSelectedNode} />
            </div>

            {/* Right panel — 40%: node detail + chat */}
            <div className="w-[40%] h-full flex flex-col">
              {/* Node detail (if selected) */}
              {selectedNode && (
                <div className="p-3 border-b border-slate-800 shrink-0">
                  <NodeDetail
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                  />
                </div>
              )}

              {/* Chat */}
              <div className="flex-1 min-h-0">
                <ChatPanel />
              </div>
            </div>
          </div>
        ) : (
          <div className="p-6">
            <StatusPage />
          </div>
        )}
      </main>
    </div>
  );
}
