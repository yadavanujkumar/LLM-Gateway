"use client";

import { useEffect, useState } from "react";
import { getMe, regenerateApiKey } from "@/lib/auth";
import { getUsage, getBalance } from "@/lib/llm";
import { User, UsageResponse } from "@/types";

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [balance, setBalance] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    getMe().then(setUser);
    getUsage(1, 5).then(setUsage);
    getBalance()
      .then((b) => setBalance(b.balance))
      .catch(() => setBalance(0));
  }, []);

  const copyApiKey = () => {
    if (user?.api_key) {
      navigator.clipboard.writeText(user.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRegenerate = async () => {
    if (!confirm("Regenerate API key? The old key will stop working immediately.")) return;
    setRegenerating(true);
    const updated = await regenerateApiKey();
    setUser(updated);
    setRegenerating(false);
  };

  if (!user || !usage) {
    return <div className="text-gray-400">Loading...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Dashboard</h2>
        <p className="text-gray-400 text-sm">Welcome back, {user.email}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Requests"
          value={usage.summary.total_requests.toLocaleString()}
        />
        <StatCard
          label="Total Tokens"
          value={usage.summary.total_tokens.toLocaleString()}
        />
        <StatCard
          label="Total Cost"
          value={`$${usage.summary.total_cost.toFixed(4)}`}
          sub="USD"
        />
        <StatCard
          label="Balance"
          value={`$${(balance ?? 0).toFixed(4)}`}
          sub="USD remaining"
        />
      </div>

      {/* API Key */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-1">Your API Key</h3>
        <p className="text-sm text-gray-400 mb-4">
          Use this key in your requests with{" "}
          <code className="bg-gray-800 px-1.5 py-0.5 rounded text-indigo-400">
            Authorization: Bearer &lt;key&gt;
          </code>
        </p>
        <div className="flex gap-3 flex-wrap">
          <code className="flex-1 bg-gray-800 rounded-lg px-4 py-3 text-sm text-green-400 font-mono break-all min-w-0">
            {user.api_key}
          </code>
          <button
            onClick={copyApiKey}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors whitespace-nowrap"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm rounded-lg transition-colors whitespace-nowrap disabled:opacity-50"
          >
            {regenerating ? "Regenerating..." : "Regenerate"}
          </button>
        </div>
      </div>

      {/* Recent Usage */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-4">Recent Usage</h3>
        {usage.records.length === 0 ? (
          <p className="text-gray-400 text-sm">
            No usage yet. Make your first API call to see it here.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-800">
                  <th className="text-left py-2 pr-4">Model</th>
                  <th className="text-right py-2 pr-4">Tokens</th>
                  <th className="text-right py-2 pr-4">Cost</th>
                  <th className="text-right py-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {usage.records.map((r) => (
                  <tr key={r.id} className="border-b border-gray-800/50">
                    <td className="py-2.5 pr-4 text-white font-mono text-xs">
                      {r.model}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-gray-300">
                      {r.total_tokens.toLocaleString()}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-gray-300">
                      ${r.cost.toFixed(6)}
                    </td>
                    <td className="py-2.5 text-right text-gray-400">
                      {new Date(r.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Start */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-4">Quick Start</h3>
        <pre className="bg-gray-800 rounded-lg p-4 text-sm text-green-400 font-mono overflow-x-auto">
          {`curl https://your-domain/v1/chat/completions \\
  -H "Authorization: Bearer ${user.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'`}
        </pre>
      </div>
    </div>
  );
}
