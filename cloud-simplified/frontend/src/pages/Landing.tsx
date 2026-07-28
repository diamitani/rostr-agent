import { Link } from "react-router-dom";
import { ArrowRight, Sparkles, Zap, Shield } from "lucide-react";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Navigation */}
      <nav className="border-b border-zinc-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="text-white font-bold text-lg">ROSTR</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-zinc-300 hover:text-white text-sm font-medium transition-colors">
              Sign in
            </Link>
            <Link to="/register" className="bg-cyan-500 hover:bg-cyan-400 text-black px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-20 pb-32">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full mb-8">
            <Sparkles className="text-cyan-400" size={16} />
            <span className="text-cyan-400 text-sm font-medium">Now with ROSTR 2.0</span>
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white leading-tight mb-6">
            AI Agents That<br />
            <span className="bg-gradient-to-r from-cyan-400 to-cyan-600 bg-clip-text text-transparent">
              Actually Work
            </span>
          </h1>
          
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto mb-10">
            Production-grade AI with smart routing, persistent memory, and intelligent RAG. Built on AWS with enterprise-grade security.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link to="/register" className="inline-flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-black px-8 py-4 rounded-xl font-semibold text-lg transition-colors">
              Get Started Free
              <ArrowRight size={20} />
            </Link>
            <a href="#features" className="inline-flex items-center justify-center gap-2 border border-zinc-700 hover:border-zinc-600 text-zinc-300 px-8 py-4 rounded-xl font-semibold text-lg transition-colors">
              Learn more
            </a>
          </div>

          <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto">
            <div>
              <div className="text-3xl font-bold text-white">85%</div>
              <div className="text-zinc-500 text-sm">Task Completion</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">9</div>
              <div className="text-zinc-500 text-sm">LLM Providers</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-white">4</div>
              <div className="text-zinc-500 text-sm">Core Skills</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 border-t border-zinc-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">Built for Production</h2>
            <p className="text-zinc-400 max-w-xl mx-auto">ROSTR combines four powerful systems to deliver reliable, intelligent AI responses</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-colors">
              <div className="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center mb-6">
                <Zap className="text-cyan-500" size={24} />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">PAL — Prompt Compiler</h3>
              <p className="text-zinc-400">5-stage compilation pipeline transforms vague requests into precise, structured prompts.</p>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-colors">
              <div className="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center mb-6">
                <svg className="text-cyan-500" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">NPAO — Smart Routing</h3>
              <p className="text-zinc-400">Necessity-Priority-Anxiety-Opportunity scoring routes tasks to the optimal model.</p>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-colors">
              <div className="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center mb-6">
                <svg className="text-cyan-500" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v6l4 2" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">RAG-DAL — Knowledge Engine</h3>
              <p className="text-zinc-400">3-tier multi-pass retrieval with credibility scoring for accurate responses.</p>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 hover:border-cyan-500/50 transition-colors">
              <div className="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center mb-6">
                <Shield className="text-cyan-500" size={24} />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">G-Stack — Data Lake</h3>
              <p className="text-zinc-400">Isolated workspaces with S3 data lake and DynamoDB indexing. Enterprise-grade security.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 border-t border-zinc-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to build?</h2>
          <p className="text-zinc-400 mb-8">Start with a free workspace. No credit card required.</p>
          <Link to="/register" className="inline-flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 text-black px-8 py-4 rounded-xl font-semibold text-lg transition-colors">
            Create Free Workspace
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-zinc-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-6 h-6 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded flex items-center justify-center">
                <span className="text-white font-bold text-xs">R</span>
              </div>
              <span className="text-zinc-500 text-sm">2026 ROSTR. All rights reserved.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
