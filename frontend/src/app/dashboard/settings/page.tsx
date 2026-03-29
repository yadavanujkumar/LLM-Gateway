"use client";

import { useEffect, useState } from "react";
import { getMe, regenerateApiKey } from "@/lib/auth";
import { User } from "@/types";

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getMe().then(setUser);
  }, []);

  const handleRegenerate = async () => {
    if (!confirm("Regenerate API key? The old key will stop working immediately."))
      return;
    setRegenerating(true);
    const updated = await regenerateApiKey();
    setUser(updated);
    setRegenerating(false);
  };

  const copyKey = () => {
    if (user?.api_key) {
      navigator.clipboard.writeText(user.api_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!user) return <div className="text-gray-400">Loading...</div>;

  const planLimits: Record<string, { rpm: number; rpd: number }> = {
    free: { rpm: 10, rpd: 100 },
    starter: { rpm: 30, rpd: 1000 },
    pro: { rpm: 60, rpd: 10000 },
    enterprise: { rpm: 200, rpd: 100000 },
  };
  const limits = planLimits[user.plan] || planLimits.free;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Settings</h2>
        <p className="text-gray-400 text-sm">Manage your account and API key</p>
      </div>

      {/* Profile */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h3 className="font-semibold text-white">Profile</h3>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Email</span>
            <span className="text-white">{user.email}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Plan</span>
            <span className="text-white capitalize">{user.plan}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Balance</span>
            <span className="text-white">${user.balance.toFixed(4)} USD</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Member since</span>
            <span className="text-white">
              {new Date(user.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Plan Limits */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="font-semibold text-white mb-4">Plan Limits</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-indigo-400">{limits.rpm}</p>
            <p className="text-xs text-gray-400 mt-1">Requests / minute</p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-indigo-400">
              {limits.rpd.toLocaleString()}
            </p>
            <p className="text-xs text-gray-400 mt-1">Requests / day</p>
          </div>
        </div>
      </div>

      {/* API Key */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h3 className="font-semibold text-white">API Key</h3>
        <div className="flex gap-2">
          <code className="flex-1 bg-gray-800 rounded-lg px-4 py-3 text-sm text-green-400 font-mono break-all min-w-0">
            {user.api_key}
          </code>
          <button
            onClick={copyKey}
            className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
          >
            {copied ? "✓" : "Copy"}
          </button>
        </div>
        <p className="text-xs text-gray-500">
          Keep this key secret. Do not share it or commit it to source control.
        </p>
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm rounded-lg transition-colors disabled:opacity-50"
        >
          {regenerating ? "Regenerating..." : "Regenerate API Key"}
        </button>
      </div>
    </div>
  );
}
