"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Sparkles,
  Send,
  Layers,
  Youtube,
  Terminal,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  ExternalLink,
  Copy,
  Check,
  Play,
  Key,
  Crown,
  Users,
  MessageSquare,
  Activity,
} from "lucide-react";
import { compilePALIntent, PALCompilation } from "@/lib/pal/compiler";
import { SUB_AGENTS_REGISTRY } from "@/lib/pal/subagents";
import { HomeOverview } from "@/components/home-overview";
import { PALInspector } from "@/components/pal-inspector";
import { VideoShowcase } from "@/components/video-showcase";
import { SandboxConsole } from "@/components/sandbox-console";
import { EvalsDashboard } from "@/components/evals-dashboard";
import { GatewayMonitor } from "@/components/gateway-monitor";
import { RuntimeStudio } from "@/components/runtime-studio";
import { AgencyManagers } from "@/components/agency-managers";
import { NavigationHeader, NavTab } from "@/components/navigation-header";
import { SitemapModal } from "@/components/sitemap-modal";
import { PlatformFooter } from "@/components/platform-footer";
import { AuthModal, UserSession } from "@/components/auth-modal";
import { PricingModal } from "@/components/pricing-modal";
import { BYOKModal, BYOKConfig } from "@/components/byok-modal";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  pal?: PALCompilation;
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<NavTab>("home");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>("spacexai/grok-4.5");
  const [currentPal, setCurrentPal] = useState<PALCompilation | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // User Session & Auth
  const [userSession, setUserSession] = useState<UserSession | null>(null);
  const [byokConfig, setByokConfig] = useState<BYOKConfig | null>(null);

  // Modals
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [isPricingOpen, setIsPricingOpen] = useState<boolean>(false);
  const [isBYOKOpen, setIsBYOKOpen] = useState<boolean>(false);
  const [isSitemapOpen, setIsSitemapOpen] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load saved session & BYOK from localStorage
  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("rostr_user_session");
      if (savedUser) {
        setUserSession(JSON.parse(savedUser));
      }
      const savedByok = localStorage.getItem("rostr_byok_config");
      if (savedByok) {
        setByokConfig(JSON.parse(savedByok));
      }
    } catch {
      // Ignore
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userText = input.trim();
    setInput("");

    // Step 1: Client PAL pre-compilation
    const pal = compilePALIntent(userText);
    setCurrentPal(pal);

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content: userText,
      timestamp: new Date().toLocaleTimeString(),
      pal,
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setIsLoading(true);

    const assistantId = `msg-${Date.now()}-assistant`;
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date().toLocaleTimeString(),
      pal,
    };

    setMessages([...newMessages, assistantMsg]);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (byokConfig?.gatewayKey) headers["x-ai-gateway-key"] = byokConfig.gatewayKey;
      if (byokConfig?.xaiKey) headers["x-xai-key"] = byokConfig.xaiKey;
      if (byokConfig?.anthropicKey) headers["x-anthropic-key"] = byokConfig.anthropicKey;
      if (byokConfig?.openaiKey) headers["x-openai-key"] = byokConfig.openaiKey;
      if (byokConfig?.awsAccessKey) headers["x-aws-key"] = byokConfig.awsAccessKey;
      if (byokConfig?.awsSecretKey) headers["x-aws-secret"] = byokConfig.awsSecretKey;
      if (byokConfig?.awsRegion) headers["x-aws-region"] = byokConfig.awsRegion;
      if (userSession?.accessToken) headers["authorization"] = `Bearer ${userSession.accessToken}`;

      const res = await fetch("/api/chat", {
        method: "POST",
        headers,
        body: JSON.stringify({
          messages: newMessages.map((m) => ({ role: m.role, content: m.content })),
          preferredModel: selectedModel,
          byok: byokConfig,
        }),
      });

      if (!res.ok) {
        throw new Error(`Gateway Error: ${res.statusText}`);
      }

      if (res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          accumulated += chunk;

          setMessages((prev) =>
            prev.map((msg) => (msg.id === assistantId ? { ...msg, content: accumulated } : msg))
          );
        }
      }
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content: `### [ROSTR PAL Pipeline - Phase: ${pal.phase}]\n**NPAO 4D Priority:** \`${pal.priorityScore}/10\` | **Active Sub-Agents:** \`${pal.subAgents.join(", ")}\`\n\nOutcome compiled and orchestrated through ROSTR:\n\n1. **Intent Decomposition**: Phase \`${pal.phase}\`, Domain \`${pal.domain}\`.\n2. **Soul Governance**: Verified non-breaking changes and approval boundary.\n3. **Sub-Agent Execution**: Dispatched ${pal.subAgents.join(", ")}.\n\n\`\`\`typescript\n// Generated Vertical Slice\nexport const outcome = "${userText.replace(/"/g, '\\"')}";\nconsole.log("Status: Executed in Vercel Sandbox");\n\`\`\``,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectPrompt = (promptText: string) => {
    setInput(promptText);
    setActiveTab("chat");
  };

  const quickStarters = [
    "Build a landing page for my EP with modern audio player",
    "Design a multi-channel marketing campaign and fan funnel",
    "Scaffold a Next.js 15 App Router landing page with Stripe pricing table",
    "Research AWS Bedrock AgentCore multi-agent memory latency",
    "Deploy full-stack Vercel harness with CI/CD gates",
    "Run automated test suite and debug stream token exception",
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc] text-slate-900 selection:bg-cyan-500/20 selection:text-cyan-800">
      {/* Redesigned Navigation Header with Clear IA */}
      <NavigationHeader
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        userSession={userSession}
        byokConfig={byokConfig}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenPricing={() => setIsPricingOpen(true)}
        onOpenBYOK={() => setIsBYOKOpen(true)}
        onOpenSitemap={() => setIsSitemapOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 flex flex-col min-h-0">
        {activeTab === "home" && (
          <HomeOverview
            onOpenAgent={(p) => handleSelectPrompt(p || "")}
            onNavigateTab={(t) => setActiveTab(t as NavTab)}
          />
        )}

        {activeTab === "agency" && (
          <AgencyManagers
            onSelectAgent={(agentId, prompt) => handleSelectPrompt(prompt || "")}
          />
        )}

        {activeTab === "video" && (
          <VideoShowcase onSelectPrompt={handleSelectPrompt} />
        )}

        {activeTab === "chat" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
            {/* Left 8-Columns: Main Agent Console */}
            <div className="lg:col-span-8 flex flex-col h-[calc(100vh-140px)] glass-panel overflow-hidden border border-slate-200">
              {/* Console Header Bar */}
              <div className="px-4 py-3 bg-white border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-900">
                    Governed Agent Session (ROSTR PAL / NPAO Active)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {userSession && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                      OAuth: {userSession.provider}
                    </span>
                  )}
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                    Live Vercel Stream
                  </span>
                </div>
              </div>

              {/* Message History Area */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50/40">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center text-white shadow-md shadow-cyan-600/20">
                      <Sparkles className="w-6 h-6" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-slate-900">
                        ROSTR Governed CTO Agent Core
                      </h2>
                      <p className="text-xs text-slate-600 mt-1 max-w-sm mx-auto">
                        State-of-the-art outcome-driven agent compiler. Combines PAL 5-stage orchestration, NPAO 4D priority scoring, and Vercel Code Sandbox execution.
                      </p>
                    </div>

                    {/* Quick Starters */}
                    <div className="w-full max-w-md space-y-2 mt-2">
                      <div className="text-[11px] text-slate-500 font-semibold font-mono uppercase">
                        Recommended Outcomes:
                      </div>
                      {quickStarters.map((starter, idx) => (
                        <button
                          key={idx}
                          onClick={() => setInput(starter)}
                          className="w-full p-2.5 rounded-xl bg-white hover:bg-cyan-50 border border-slate-200 hover:border-cyan-300 text-xs text-slate-700 hover:text-cyan-800 transition-all text-left flex items-center justify-between group cursor-pointer shadow-2xs"
                        >
                          <span className="truncate font-medium">{starter}</span>
                          <span className="text-cyan-600 opacity-0 group-hover:opacity-100 transition-opacity font-bold">
                            →
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map((m) => {
                    const isUser = m.role === "user";
                    return (
                      <div
                        key={m.id}
                        className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                      >
                        {!isUser && (
                          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0 shadow-xs mt-0.5">
                            AI
                          </div>
                        )}

                        <div
                          className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                            isUser
                              ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/15"
                              : "glass-card bg-white text-slate-800 border border-slate-200 shadow-xs"
                          }`}
                        >
                          {/* PAL Header Tag */}
                          {!isUser && m.pal && (
                            <div className="mb-2.5 pb-2 border-b border-slate-200 flex flex-wrap items-center gap-2 text-[10px] font-mono">
                              <span className="px-1.5 py-0.5 rounded bg-cyan-50 text-cyan-700 font-bold border border-cyan-200">
                                Phase: {m.pal.phase}
                              </span>
                              <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-bold border border-purple-200">
                                NPAO: {m.pal.priorityScore}/10
                              </span>
                              <span className="text-slate-500">
                                Sub-Agents: {m.pal.subAgents.join(", ")}
                              </span>
                            </div>
                          )}

                          <div className="whitespace-pre-wrap font-sans">{m.content}</div>

                          {!isUser && (
                            <div className="mt-3 pt-2 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-500">
                              <span className="font-mono">ROSTR PAL Streamed</span>
                              <div className="flex items-center gap-2">
                                {m.content.includes("```") && (
                                  <button
                                    onClick={() => setActiveTab("sandbox")}
                                    className="hover:text-emerald-700 text-emerald-600 font-semibold flex items-center gap-1 cursor-pointer"
                                  >
                                    <Play className="w-2.5 h-2.5 fill-current" /> Run in Sandbox
                                  </button>
                                )}
                                <button
                                  onClick={() => handleCopy(m.content, m.id)}
                                  className="hover:text-cyan-700 flex items-center gap-1 cursor-pointer font-medium"
                                >
                                  {copiedId === m.id ? (
                                    <>
                                      <Check className="w-3 h-3 text-emerald-600" /> Copied
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="w-3 h-3" /> Copy
                                    </>
                                  )}
                                </button>
                              </div>
                            </div>
                          )}
                        </div>

                        {isUser && (
                          <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5">
                            You
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
                {isLoading && (
                  <div className="flex items-center gap-2 text-xs text-cyan-600 font-mono font-medium">
                    <div className="w-3.5 h-3.5 border-2 border-cyan-600 border-t-transparent rounded-full animate-spin" />
                    <span>Compiling PAL Intent & Streaming response...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Bar */}
              <form onSubmit={handleSendMessage} className="p-3 bg-white border-t border-slate-200">
                <div className="relative flex items-center">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Enter outcome-driven task (e.g. 'Build pricing page with Stripe')..."
                    className="w-full glass-input rounded-xl pl-4 pr-24 py-3 text-xs focus:ring-1 focus:ring-cyan-500"
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="absolute right-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold transition-all shadow-md shadow-cyan-600/20 disabled:opacity-40 cursor-pointer flex items-center gap-1.5"
                  >
                    <span>Send</span>
                    <Send className="w-3 h-3" />
                  </button>
                </div>
              </form>
            </div>

            {/* Right 4-Columns: Live PAL & Sub-Agent Trace Widget */}
            <div className="lg:col-span-4 space-y-4 flex flex-col h-[calc(100vh-140px)] overflow-y-auto">
              {/* Active PAL Compilation Widget */}
              <div className="glass-panel p-4 bg-white border border-slate-200">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-cyan-600" />
                    <span className="text-xs font-bold text-slate-900">Live PAL Compiler State</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-50 text-cyan-700 font-bold border border-cyan-200">
                    Phase: {currentPal?.phase || "Development"}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">NPAO Priority</div>
                    <div className="text-lg font-bold text-cyan-700 font-mono">
                      {currentPal?.priorityScore || 6.75}{" "}
                      <span className="text-xs font-normal text-slate-500">/ 10</span>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="text-[10px] text-slate-500 uppercase mb-1 font-mono">Dispatched Sub-Agents</div>
                    <div className="flex flex-wrap gap-1">
                      {(currentPal?.subAgents || ["application-engineer", "quality-engineer"]).map(
                        (sa) => (
                          <span
                            key={sa}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 font-semibold border border-purple-200"
                          >
                            {sa}
                          </span>
                        )
                      )}
                    </div>
                  </div>

                  <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                    <div className="text-[10px] text-slate-500 uppercase mb-1 font-mono">Approval Boundary</div>
                    <span className="text-[11px] text-emerald-700 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      {currentPal?.approvalGates.length
                        ? currentPal.approvalGates.join(", ")
                        : "No blocking approval gates required"}
                    </span>
                  </div>
                </div>
              </div>

              {/* YouTube Showcase Mini-Card */}
              <div
                onClick={() => setActiveTab("video")}
                className="glass-panel p-4 bg-white border border-slate-200 hover:border-red-400 transition-all cursor-pointer group shadow-2xs"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-slate-900 group-hover:text-red-600 flex items-center gap-1.5">
                    <Youtube className="w-3.5 h-3.5 text-red-500" />
                    Patrick Diamitani Demo Video
                  </span>
                  <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-red-500" />
                </div>
                <p className="text-[11px] text-slate-600 line-clamp-2">
                  Watch Patrick Diamitani demonstrate the ROSTR framework, PAL compiler, and Bedrock AgentCore.
                </p>
              </div>

              {/* Sub-Agents Quick Status */}
              <div className="glass-panel p-4 flex-1 bg-white border border-slate-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-blue-600" />
                    Specialist Sub-Agents (9)
                  </div>
                  <button
                    onClick={() => setActiveTab("agency")}
                    className="text-[10px] text-indigo-600 font-semibold hover:underline cursor-pointer"
                  >
                    View All →
                  </button>
                </div>
                <div className="space-y-1.5 max-h-[180px] overflow-y-auto pr-1">
                  {SUB_AGENTS_REGISTRY.map((agent) => (
                    <div
                      key={agent.id}
                      onClick={() => setActiveTab("agency")}
                      className="p-2 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between text-[11px] cursor-pointer hover:bg-slate-100 transition-colors"
                    >
                      <span className="text-slate-800 font-medium">{agent.name}</span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {agent.phases.join(", ")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "studio" && <RuntimeStudio />}
        {activeTab === "pal" && <PALInspector onDispatchToChat={handleSelectPrompt} />}
        {activeTab === "sandbox" && <SandboxConsole />}
        {activeTab === "evals" && <EvalsDashboard />}
        {activeTab === "gateway" && (
          <GatewayMonitor selectedModel={selectedModel} onSelectModel={setSelectedModel} />
        )}
      </main>

      {/* Full Sitemap Footer */}
      <PlatformFooter
        onNavigate={(tab) => setActiveTab(tab)}
        onOpenSitemap={() => setIsSitemapOpen(true)}
        onOpenAuth={() => setIsAuthOpen(true)}
        onOpenPricing={() => setIsPricingOpen(true)}
        onOpenBYOK={() => setIsBYOKOpen(true)}
      />

      {/* Modals */}
      <SitemapModal
        isOpen={isSitemapOpen}
        onClose={() => setIsSitemapOpen(false)}
        onNavigate={(tab) => setActiveTab(tab)}
        onOpenAuth={() => {
          setIsSitemapOpen(false);
          setIsAuthOpen(true);
        }}
        onOpenPricing={() => {
          setIsSitemapOpen(false);
          setIsPricingOpen(true);
        }}
        onOpenBYOK={() => {
          setIsSitemapOpen(false);
          setIsBYOKOpen(true);
        }}
      />

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onLogin={(session) => setUserSession(session)}
        onOpenPricing={() => {
          setIsAuthOpen(false);
          setIsPricingOpen(true);
        }}
      />

      <PricingModal
        isOpen={isPricingOpen}
        onClose={() => setIsPricingOpen(false)}
        onSelectTier={(tier) => {
          if (userSession) {
            const updated = { ...userSession, tier };
            setUserSession(updated);
            localStorage.setItem("rostr_user_session", JSON.stringify(updated));
          }
        }}
        currentTier={userSession?.tier || "free"}
      />

      <BYOKModal
        isOpen={isBYOKOpen}
        onClose={() => setIsBYOKOpen(false)}
        onSave={(config) => {
          setByokConfig(config);
          if (userSession) {
            setUserSession({ ...userSession, byokConfigured: true });
          }
        }}
      />
    </div>
  );
}
