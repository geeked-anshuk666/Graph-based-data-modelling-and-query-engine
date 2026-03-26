const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  properties: Record<string, string | number | null>;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  focus?: GraphNode;
}

export interface QueryResponse {
  answer: string;
  sql: string | null;
  rows: Record<string, unknown>[];
  on_topic: boolean;
}

export interface StatusService {
  name: string;
  ok: boolean;
  latency_ms: number;
}

export interface StatusResponse {
  backend: StatusService;
  database: StatusService;
  llm: StatusService;
}

export async function fetchGraph(): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/api/graph`);
  if (!res.ok) throw new Error(`graph fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchNodeDetail(nodeId: string): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/api/graph/node/${encodeURIComponent(nodeId)}`);
  if (!res.ok) throw new Error(`node fetch failed: ${res.status}`);
  return res.json();
}

export async function submitQuery(question: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`query failed: ${res.status}`);
  return res.json();
}

export async function fetchStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/api/status`);
  if (!res.ok) throw new Error(`status fetch failed: ${res.status}`);
  return res.json();
}
