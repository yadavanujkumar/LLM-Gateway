"use client";

import { useEffect, useState } from "react";
import { getModels } from "@/lib/llm";
import { ModelInfo } from "@/types";

const providerColors: Record<string, string> = {
  openai: "bg-green-500/10 text-green-400 border-green-500/20",
  meta: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "mistral-ai": "bg-orange-500/10 text-orange-400 border-orange-500/20",
};

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    getModels()
      .then((r) => setModels(r.data))
      .finally(() => setLoading(false));
  }, []);

  const providers = ["all", ...new Set(models.map((m) => m.owned_by))];
  const filtered =
    filter === "all" ? models : models.filter((m) => m.owned_by === filter);

  if (loading) return <div className="text-gray-400">Loading models...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Available Models</h2>
        <p className="text-gray-400 text-sm">{models.length} models available</p>
      </div>

      <div className="flex gap-2 flex-wrap">
        {providers.map((p) => (
          <button
            key={p}
            onClick={() => setFilter(p)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium capitalize transition-colors ${
              filter === p
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-white"
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((model) => (
          <div
            key={model.id}
            className="bg-gray-900 border border-gray-800 rounded-xl p-5"
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div>
                <h3 className="font-semibold text-white font-mono text-sm">
                  {model.id}
                </h3>
                {model.description && (
                  <p className="text-xs text-gray-400 mt-1">{model.description}</p>
                )}
              </div>
              <span
                className={`text-xs px-2.5 py-1 rounded-full border whitespace-nowrap ${
                  providerColors[model.owned_by] ||
                  "bg-gray-700 text-gray-300 border-gray-600"
                }`}
              >
                {model.owned_by}
              </span>
            </div>

            <div className="space-y-1 text-xs text-gray-400">
              {model.context_window && (
                <div className="flex justify-between">
                  <span>Context</span>
                  <span className="text-gray-300">
                    {(model.context_window / 1000).toFixed(0)}K tokens
                  </span>
                </div>
              )}
              {model.pricing && (
                <>
                  <div className="flex justify-between">
                    <span>Input</span>
                    <span className="text-gray-300">
                      ${model.pricing.input}/1K tokens
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Output</span>
                    <span className="text-gray-300">
                      ${model.pricing.output}/1K tokens
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
