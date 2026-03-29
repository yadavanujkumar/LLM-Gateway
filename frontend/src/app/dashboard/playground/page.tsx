"use client";

import { useEffect, useState, useRef } from "react";
import { getModels, chatCompletion } from "@/lib/llm";
import { ModelInfo, ChatMessage } from "@/types";

export default function PlaygroundPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("gpt-3.5-turbo");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(512);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastUsage, setLastUsage] = useState<{
    tokens: number;
    cost: number;
    cached?: boolean;
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getModels().then((r) => {
      const chatModels = r.data.filter(
        (m) => !m.id.includes("embed") && !m.id.includes("ada")
      );
      setModels(chatModels);
    });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await chatCompletion({
        model: selectedModel,
        messages: newMessages,
        temperature,
        max_tokens: maxTokens,
      });

      const assistantMessage = response.choices[0].message;
      setMessages([...newMessages, assistantMessage]);
      setLastUsage({
        tokens: response.usage.total_tokens,
        cost: 0, // would need to calculate from model pricing
        cached: response.cached,
      });
    } catch {
      setMessages([
        ...newMessages,
        { role: "assistant", content: "❌ Error: Failed to get response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setLastUsage(null);
  };

  return (
    <div className="space-y-6 h-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Playground</h2>
          <p className="text-gray-400 text-sm">Test prompts against any model</p>
        </div>
        <button
          onClick={clearChat}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Clear chat
        </button>
      </div>

      <div className="flex gap-6">
        {/* Settings Panel */}
        <div className="w-56 space-y-4 flex-shrink-0">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Model
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.id}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Temperature: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1.5">
              Max Tokens: {maxTokens}
            </label>
            <input
              type="range"
              min="64"
              max="4096"
              step="64"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>

          {lastUsage && (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-xs space-y-1">
              <p className="text-gray-400">Last response</p>
              <p className="text-gray-300">
                {lastUsage.tokens.toLocaleString()} tokens
              </p>
              {lastUsage.cached && (
                <p className="text-green-400">⚡ Cached response</p>
              )}
            </div>
          )}
        </div>

        {/* Chat Panel */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl p-4 min-h-96 max-h-[60vh] overflow-y-auto space-y-4">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                Start a conversation...
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-800 text-gray-100"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 text-gray-400 rounded-xl px-4 py-3 text-sm">
                  <span className="animate-pulse">Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="mt-3 flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
              rows={2}
              className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="px-5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-medium transition-colors self-end py-3"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
