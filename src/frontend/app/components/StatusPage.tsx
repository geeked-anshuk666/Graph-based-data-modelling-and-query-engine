"use client";

import { useEffect, useState } from "react";
import { fetchStatus, StatusResponse } from "../lib/api";

export default function StatusPage() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStatus();
      setStatus(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const ServiceCard = ({
    service,
  }: {
    service: { name: string; ok: boolean; latency_ms: number };
  }) => (
    <div
      className={`rounded-lg p-4 border ${
        service.ok
          ? "bg-green-950/30 border-green-800"
          : "bg-red-950/30 border-red-800"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-200">
          {service.name}
        </span>
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded ${
            service.ok
              ? "bg-green-900 text-green-300"
              : "bg-red-900 text-red-300"
          }`}
        >
          {service.ok ? "Healthy" : "Down"}
        </span>
      </div>
      <p className="text-xs text-slate-400 mt-1">
        Latency: {service.latency_ms.toFixed(1)}ms
      </p>
    </div>
  );

  return (
    <div className="max-w-lg mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">System Status</h2>
        <button
          onClick={loadStatus}
          disabled={loading}
          className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1.5 rounded transition-colors disabled:opacity-50"
        >
          {loading ? "Checking…" : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950/30 border border-red-800 rounded-lg p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {status && (
        <div className="space-y-3">
          <ServiceCard service={status.backend} />
          <ServiceCard service={status.database} />
          <ServiceCard service={status.llm} />
        </div>
      )}
    </div>
  );
}
