"use client";

import { GraphNode } from "../lib/api";

interface Props {
  node: GraphNode | null;
  onClose: () => void;
}

export default function NodeDetail({ node, onClose }: Props) {
  if (!node) return null;

  const entries = Object.entries(node.properties).filter(
    ([, v]) => v !== null && v !== "" && v !== undefined
  );

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs font-medium text-blue-400 uppercase tracking-wider">
            {node.type}
          </span>
          <h3 className="text-slate-200 font-semibold">{node.label}</h3>
          <p className="text-xs text-slate-500 font-mono">{node.id}</p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 text-lg leading-none"
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      <div className="space-y-1 max-h-64 overflow-y-auto">
        {entries.map(([key, val]) => (
          <div
            key={key}
            className="flex justify-between gap-3 py-1 border-b border-slate-800"
          >
            <span className="text-slate-400 shrink-0">{key}</span>
            <span className="text-slate-200 text-right truncate">
              {String(val)}
            </span>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-slate-500 italic">No properties available</p>
        )}
      </div>
    </div>
  );
}
