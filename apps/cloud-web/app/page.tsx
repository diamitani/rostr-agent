import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              ROSTR
            </div>
            <div className="flex gap-4">
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium hover:text-cyan-400 transition"
              >
                Sign In
              </Link>
              <Link
                href="/app/chat"
                className="px-4 py-2 text-sm font-medium bg-cyan-500 hover:bg-cyan-600 rounded-lg transition"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center space-y-8 animate-fade-in">
          <h1 className="text-6xl font-bold tracking-tight">
            AI-Powered Workflow<br />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Automation Cloud
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Build, deploy, and scale intelligent workflows with ROSTR. Powered by Vercel AI SDK,
            built for teams that demand reliability and performance.
          </p>

          <div className="flex gap-4 justify-center pt-4">
            <Link
              href="/app/chat"
              className="px-8 py-3 bg-cyan-500 hover:bg-cyan-600 rounded-lg font-semibold transition shadow-lg shadow-cyan-500/20"
            >
              Start Chat
            </Link>
            <Link
              href="/app/skills"
              className="px-8 py-3 border border-slate-700 hover:border-slate-500 rounded-lg font-semibold transition"
            >
              Browse Skills
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24">
          {[
            {
              title: "Real-time Streaming",
              description:
                "Stream LLM responses as they're generated for instant feedback",
            },
            {
              title: "Session Persistence",
              description:
                "Save and restore workspace state with Vercel KV Redis",
            },
            {
              title: "Scalable Skills",
              description:
                "Upload custom skills and execute them across your workflows",
            },
            {
              title: "Multi-Channel Integration",
              description:
                "Connect via Telegram, WhatsApp, iMessage, Signal with Composio",
            },
            {
              title: "Usage Tracking",
              description:
                "Monitor execution metrics and billing in real-time dashboards",
            },
            {
              title: "Enterprise Ready",
              description:
                "Postgres storage, Stripe billing, and secure authentication",
            },
          ].map((feature, i) => (
            <div
              key={i}
              className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition group"
            >
              <h3 className="font-semibold text-lg mb-2 group-hover:text-cyan-400 transition">
                {feature.title}
              </h3>
              <p className="text-slate-400 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Tech Stack */}
        <div className="mt-24 text-center">
          <h2 className="text-3xl font-bold mb-8">Built with Best-in-Class Tools</h2>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-slate-400">
            {["Vercel AI SDK", "Next.js", "Vercel Functions", "Postgres", "Vercel KV", "Stripe", "Anthropic"].map(
              (tech) => (
                <div key={tech} className="px-4 py-2 bg-slate-800 rounded-full">
                  {tech}
                </div>
              )
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-800 mt-24 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-500 text-sm">
          Built with Vercel AI SDK | rostr-agent.vercel.app
        </div>
      </div>
    </div>
  );
}
