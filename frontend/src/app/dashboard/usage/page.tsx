"use client";

import { useEffect, useState } from "react";
import { getUsage } from "@/lib/llm";
import { UsageResponse } from "@/types";

export default function UsagePage() {
  const [data, setData] = useState<UsageResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const PAGE_SIZE = 20;

  useEffect(() => {
    setLoading(true);
    getUsage(page, PAGE_SIZE)
      .then(setData)
      .finally(() => setLoading(false));
  }, [page]);

  if (loading && !data) return <div className="text-gray-400">Loading...</div>;
  if (!data) return null;

  const totalPages = Math.ceil(data.total / PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Usage</h2>
        <p className="text-gray-400 text-sm">
          {data.total.toLocaleString()} total requests
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            label: "Total Requests",
            value: data.summary.total_requests.toLocaleString(),
          },
          {
            label: "Total Tokens",
            value: data.summary.total_tokens.toLocaleString(),
          },
          {
            label: "Prompt Tokens",
            value: data.summary.prompt_tokens.toLocaleString(),
          },
          {
            label: "Total Cost",
            value: `$${data.summary.total_cost.toFixed(6)}`,
          },
        ].map((s) => (
          <div
            key={s.label}
            className="bg-gray-900 border border-gray-800 rounded-xl p-5"
          >
            <p className="text-xs text-gray-400 mb-1">{s.label}</p>
            <p className="text-xl font-bold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Records Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-800">
              <tr className="text-gray-400">
                <th className="text-left px-4 py-3">Model</th>
                <th className="text-right px-4 py-3">Prompt</th>
                <th className="text-right px-4 py-3">Completion</th>
                <th className="text-right px-4 py-3">Total</th>
                <th className="text-right px-4 py-3">Cost</th>
                <th className="text-right px-4 py-3">Time</th>
              </tr>
            </thead>
            <tbody>
              {data.records.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="text-center py-12 text-gray-500"
                  >
                    No usage records yet
                  </td>
                </tr>
              ) : (
                data.records.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-gray-800/50 hover:bg-gray-800/30"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-white">
                      {r.model}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300">
                      {r.prompt_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300">
                      {r.completion_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300 font-medium">
                      {r.total_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-300">
                      ${r.cost.toFixed(8)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400 text-xs">
                      {new Date(r.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800">
            <span className="text-sm text-gray-400">
              Page {page} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white rounded-lg transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
