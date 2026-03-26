"use client";

import { useState, useRef, useEffect } from "react";
import { submitQuery, QueryResponse } from "../lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sql?: string | null;
  rows?: Record<string, unknown>[];
  on_topic?: boolean;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I can answer questions about the SAP Order-to-Cash dataset. Try asking about sales orders, deliveries, billing documents, or payments.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res: QueryResponse = await submitQuery(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.answer,
          sql: res.sql,
          rows: res.rows,
          on_topic: res.on_topic,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Something went wrong. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700">
        <h2 className="text-sm font-semibold text-slate-200">
          💬 Query Interface
        </h2>
        <p className="text-xs text-slate-400">
          Ask questions in plain English about SAP O2C data
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-800 text-slate-200"
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* SQL block */}
              {msg.sql && (
                <details className="mt-2">
                  <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-300">
                    View SQL
                  </summary>
                  <pre className="mt-1 p-2 bg-slate-950 rounded text-xs text-green-400 overflow-x-auto">
                    {msg.sql}
                  </pre>
                </details>
              )}

              {/* Results table */}
              {msg.rows && msg.rows.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-slate-400 cursor-pointer hover:text-slate-300">
                    View data ({msg.rows.length} rows)
                  </summary>
                  <div className="mt-1 overflow-x-auto max-h-48">
                    <table className="text-xs w-full">
                      <thead>
                        <tr className="text-slate-400 border-b border-slate-700">
                          {Object.keys(msg.rows[0]).map((col) => (
                            <th key={col} className="px-2 py-1 text-left">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.rows.slice(0, 20).map((row, ri) => (
                          <tr
                            key={ri}
                            className="border-b border-slate-800 text-slate-300"
                          >
                            {Object.values(row).map((val, ci) => (
                              <td key={ci} className="px-2 py-1">
                                {String(val ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              )}

              {/* Off-topic indicator */}
              {msg.on_topic === false && (
                <p className="mt-1 text-xs text-amber-400">⚠ Off-topic</p>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 rounded-lg px-3 py-2 text-sm text-slate-400">
              <span className="animate-pulse">Thinking…</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about orders, deliveries, billing..."
            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
