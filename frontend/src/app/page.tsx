import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-950 flex flex-col">
      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 text-sm text-indigo-400 mb-8">
          <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
          Production-Ready LLM API Gateway
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-br from-white to-gray-400 bg-clip-text text-transparent">
          LLM Gateway
        </h1>

        <p className="text-xl text-gray-400 max-w-2xl mb-10">
          Access GPT-4, Llama 3, and Mistral through a single unified API.
          Pay per token. Auto-fallback. Streaming. Caching.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/auth/register"
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-semibold transition-colors"
          >
            Get Started Free
          </Link>
          <Link
            href="/auth/login"
            className="px-8 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-6xl mx-auto w-full px-4 pb-24 grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            title: "Multiple Models",
            desc: "OpenAI GPT-4/3.5, Meta Llama 3, Mistral — all from a single endpoint.",
            icon: "🤖",
          },
          {
            title: "Pay Per Token",
            desc: "Transparent per-token pricing. Add balance via Stripe. No surprise bills.",
            icon: "💳",
          },
          {
            title: "Auto Fallback",
            desc: "If one model fails, we automatically retry with the next available model.",
            icon: "🔄",
          },
          {
            title: "Streaming",
            desc: "Real-time token streaming for all supported models.",
            icon: "⚡",
          },
          {
            title: "Prompt Caching",
            desc: "Repeated identical prompts are cached in Redis, saving tokens.",
            icon: "🗄️",
          },
          {
            title: "Usage Dashboard",
            desc: "Monitor your token usage, costs, and request logs in real-time.",
            icon: "📊",
          },
        ].map((f) => (
          <div
            key={f.title}
            className="bg-gray-900 border border-gray-800 rounded-xl p-6"
          >
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-semibold text-white mb-2">{f.title}</h3>
            <p className="text-gray-400 text-sm">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-6 text-center text-gray-500 text-sm">
        LLM Gateway © {new Date().getFullYear()} — Built with FastAPI, Next.js &amp; ❤️
      </footer>
    </main>
  );
}
