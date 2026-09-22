"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Terminal,
  Send,
  Sparkles,
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  Play,
  RotateCcw,
  Sliders,
  Cpu,
  Layers,
  Key,
  Crown,
  Shield,
  Zap,
  Code2,
  CheckCircle2,
  ExternalLink,
  MessageSquare,
  HelpCircle,
  Trash2,
} from "lucide-react";
import { compilePALIntent, PALCompilation } from "@/lib/pal/compiler";
import { SUB_AGENTS_REGISTRY } from "@/lib/pal/subagents";
import { UserSession } from "./auth-modal";
import { BYOKConfig } from "./byok-modal";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  pal?: PALCompilation;
  isStreaming?: boolean;
}

interface ClaudeCodeChatProps {
  userSession: UserSession | null;
  byokConfig: BYOKConfig | null;
  selectedModel: string;
  onOpenBYOK: () => void;
  onOpenPricing: () => void;
  onOpenAuth: () => void;
  onOpenSandboxWithCode?: (code: string, runtime: string) => void;
  onNavigateTab?: (tab: string) => void;
}

const SLASH_COMMANDS = [
  { command: "/help", desc: "Display all available commands & PAL architecture" },
  { command: "/model", desc: "Select AI Provider (Claude Sonnet 4.6, GPT-4o, Bedrock)" },
  { command: "/byok", desc: "Configure your Bring Your Own Key credentials" },
  { command: "/pricing", desc: "View Free vs Pro ($19.99/mo) harness plans" },
  { command: "/pal", desc: "Analyze outcome through 5-stage PAL compiler" },
  { command: "/npao", desc: "Inspect NPAO 4D priority scoring formula" },
  { command: "/subagents", desc: "View registry of all 9 specialist sub-agents" },
  { command: "/sandbox", desc: "Open Vercel Code Sandbox environment" },
  { command: "/evals", desc: "Run EVE automated evaluation benchmark suite" },
  { command: "/video", desc: "Open Patrick Diamitani YouTube Demo Showcase" },
  { command: "/clear", desc: "Clear all messages in active session" },
];

export function ClaudeCodeChat({
  userSession,
  byokConfig,
  selectedModel,
  onOpenBYOK,
  onOpenPricing,
  onOpenAuth,
  onOpenSandboxWithCode,
  onNavigateTab,
}: ClaudeCodeChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showThinking, setShowThinking] = useState<Record<string, boolean>>({});
  const [showCommands, setShowCommands] = useState<boolean>(false);
  const [activeCommandIdx, setActiveCommandIdx] = useState<number>(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Handle slash command autocomplete
  useEffect(() => {
    if (input.startsWith("/")) {
      setShowCommands(true);
    } else {
      setShowCommands(false);
    }
  }, [input]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleThinking = (msgId: string) => {
    setShowThinking((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSlashSelect = (cmd: string) => {
    setShowCommands(false);
    if (cmd === "/clear") {
      setMessages([]);
      setInput("");
      return;
    }
    if (cmd === "/byok") {
      setInput("");
      onOpenBYOK();
      return;
    }
    if (cmd === "/pricing") {
      setInput("");
      onOpenPricing();
      return;
    }
    if (cmd === "/video" && onNavigateTab) {
      setInput("");
      onNavigateTab("video");
      return;
    }
    if (cmd === "/sandbox" && onNavigateTab) {
      setInput("");
      onNavigateTab("sandbox");
      return;
    }
    if (cmd === "/evals" && onNavigateTab) {
      setInput("");
      onNavigateTab("evals");
      return;
    }
    if (cmd === "/pal" && onNavigateTab) {
      setInput("");
      onNavigateTab("pal");
      return;
    }

    setInput(`${cmd} `);
    inputRef.current?.focus();
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const rawText = input.trim();
    setInput("");
    setShowCommands(false);

    // Built-in slash commands handler
    if (rawText === "/clear") {
      setMessages([]);
      return;
    }
    if (rawText === "/byok") {
      onOpenBYOK();
      return;
    }
    if (rawText === "/pricing") {
      onOpenPricing();
      return;
    }

    // Pre-compile PAL intent for trace
    const pal = compilePALIntent(rawText);

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: "user",
      content: rawText,
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
      isStreaming: true,
    };

    setMessages([...newMessages, assistantMsg]);
    setShowThinking((prev) => ({ ...prev, [assistantId]: true }));

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (byokConfig?.gatewayKey) headers["x-ai-gateway-key"] = byokConfig.gatewayKey;
      if (byokConfig?.xaiKey) headers["x-xai-key"] = byokConfig.xaiKey;
      if (byokConfig?.anthropicKey) headers["x-anthropic-key"] = byokConfig.anthropicKey;
      if (byokConfig?.openaiKey) headers["x-openai-key"] = byokConfig.openaiKey;
      if (byokConfig?.awsAccessKey) headers["x-aws-key"] = byokConfig.awsAccessKey;
      if (byokConfig?.awsSecretKey) headers["x-aws-secret"] = byokConfig.awsSecretKey;
      if (byokConfig?.awsRegion) headers["x-aws-region"] = byokConfig.awsRegion;

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
        throw new Error(`Chat API error: ${res.statusText}`);
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
            prev.map((msg) =>
              msg.id === assistantId ? { ...msg, content: accumulated, isStreaming: true } : msg
            )
          );
        }
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId ? { ...msg, isStreaming: false } : msg
        )
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content: `ROSTR Gateway Connection Notice:\n${err?.message || "Streaming complete"}.\n\nOperating under zero-config PAL compiler fallback.`,
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const quickStarters = [
    "Scaffold a Next.js 15 App Router landing page with Stripe pricing table",
    "Research AWS Bedrock AgentCore multi-agent memory latency",
    "Deploy full-stack Vercel harness with CI/CD gates",
    "Run automated test suite and debug stream token exception",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] glass-panel overflow-hidden border border-white/10 rounded-2xl bg-[#090b10]">
      {/* Claude Code Terminal Header */}
      <div className="px-4 py-2.5 bg-slate-950/90 border-b border-white/10 flex flex-wrap items-center justify-between gap-2 text-xs">
        {/* Terminal Breadcrumb */}
        <div className="flex items-center gap-2 font-mono text-slate-300">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-900 border border-white/10 text-cyan-300 text-[11px]">
            <Terminal className="w-3.5 h-3.5" />
            <span>~ / rostr-agent / workspace</span>
          </div>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            branch: <span className="text-emerald-400 font-bold">main</span>
          </span>
        </div>

        {/* Status Pill & Actions */}
        <div className="flex items-center gap-2">
          {/* User Tier Indicator */}
          <button
            onClick={onOpenPricing}
            className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold flex items-center gap-1 transition-all cursor-pointer ${
              userSession?.tier === "pro"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/40"
                : "bg-slate-900 text-slate-300 border border-white/10 hover:border-cyan-500/40"
            }`}
          >
            {userSession?.tier === "pro" ? (
              <>
                <Crown className="w-3 h-3 text-amber-400" /> Pro ($19.99/mo)
              </>
            ) : (
              <>
                <Zap className="w-3 h-3 text-cyan-400" /> Free Plan
              </>
            )}
          </button>

          {/* BYOK Status Button */}
          <button
            onClick={onOpenBYOK}
            className={`px-2 py-0.5 rounded-lg text-[10px] font-mono flex items-center gap-1 transition-all cursor-pointer ${
              byokConfig?.gatewayKey || byokConfig?.xaiKey || byokConfig?.anthropicKey || byokConfig?.openaiKey || byokConfig?.awsAccessKey
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                : "bg-slate-900 text-slate-400 border border-white/5 hover:text-white"
            }`}
          >
            <Key className="w-3 h-3" />
            <span>
              {byokConfig?.anthropicKey
                ? "BYOK (Anthropic)"
                : byokConfig?.openaiKey
                ? "BYOK (OpenAI)"
                : "BYOK Keys"}
            </span>
          </button>

          {/* Clear Button */}
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              title="Clear Session"
              className="p-1 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-900 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-4 md:p-6 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500/20 to-purple-600/20 border border-cyan-500/30 flex items-center justify-center text-cyan-300 shadow-xl shadow-cyan-500/10">
              <Sparkles className="w-7 h-7" />
            </div>

            <div>
              <h2 className="text-base md:text-lg font-bold text-white tracking-tight flex items-center justify-center gap-2">
                ROSTR Governed CTO Agent
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Claude Code Style
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Combines PAL 5-stage intent compilation, NPAO 4D priority weights, 9 specialist sub-agents, and Vercel Code Sandbox execution.
              </p>
            </div>

            {/* Quick Starters */}
            <div className="w-full max-w-xl space-y-2 mt-4 text-left">
              <div className="text-[11px] text-slate-500 font-semibold font-mono uppercase tracking-wider">
                Recommended Outcome Starters:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {quickStarters.map((starter, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(starter);
                      inputRef.current?.focus();
                    }}
                    className="p-3 rounded-xl bg-slate-950/60 hover:bg-cyan-500/10 border border-white/5 hover:border-cyan-500/30 text-xs text-slate-300 hover:text-cyan-200 transition-all text-left flex items-start gap-2 group cursor-pointer"
                  >
                    <ChevronRight className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5 group-hover:translate-x-0.5 transition-transform" />
                    <span>{starter}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((m) => {
            const isUser = m.role === "user";
            return (
              <div
                key={m.id}
                className={`flex flex-col space-y-1.5 ${isUser ? "items-end" : "items-start"}`}
              >
                {/* Role Header */}
                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-500 px-1">
                  <span className="font-bold uppercase text-slate-400">
                    {isUser ? userSession?.name || "Developer" : "ROSTR CTO Agent"}
                  </span>
                  <span>•</span>
                  <span>{m.timestamp || "just now"}</span>
                  {!isUser && m.pal && (
                    <>
                      <span>•</span>
                      <span className="text-cyan-400 font-semibold">Phase: {m.pal.phase}</span>
                      <span>•</span>
                      <span className="text-purple-400 font-semibold">
                        Priority: {m.pal.priorityScore}/10
                      </span>
                    </>
                  )}
                </div>

                {/* Message Box */}
                <div
                  className={`w-full max-w-[92%] md:max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                    isUser
                      ? "bg-gradient-to-r from-cyan-600/90 to-blue-600/90 text-white shadow-lg shadow-cyan-600/10"
                      : "bg-slate-900/90 border border-white/10 text-slate-200 shadow-xl shadow-black/40"
                  }`}
                >
                  {/* Assistant PAL Thinking Accordion */}
                  {!isUser && m.pal && (
                    <div className="mb-3 rounded-xl bg-slate-950/80 border border-white/10 overflow-hidden">
                      <button
                        onClick={() => toggleThinking(m.id)}
                        className="w-full px-3 py-2 flex items-center justify-between text-[11px] font-mono text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      >
                        <div className="flex items-center gap-2">
                          <Layers className="w-3.5 h-3.5 text-cyan-400" />
                          <span>PAL 5-Stage Orchestration & NPAO Trace</span>
                        </div>
                        {showThinking[m.id] ? (
                          <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                        )}
                      </button>

                      {showThinking[m.id] && (
                        <div className="p-3 border-t border-white/5 space-y-2 text-[11px] font-mono">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            <div className="p-2 rounded bg-slate-900 border border-white/5">
                              <span className="text-slate-500 block text-[9px] uppercase">Phase</span>
                              <span className="text-cyan-300 font-bold">{m.pal.phase}</span>
                            </div>
                            <div className="p-2 rounded bg-slate-900 border border-white/5">
                              <span className="text-slate-500 block text-[9px] uppercase">
                                NPAO Priority
                              </span>
                              <span className="text-purple-300 font-bold">
                                {m.pal.priorityScore} / 10
                              </span>
                            </div>
                            <div className="p-2 rounded bg-slate-900 border border-white/5">
                              <span className="text-slate-500 block text-[9px] uppercase">Domain</span>
                              <span className="text-amber-300 font-bold">{m.pal.domain}</span>
                            </div>
                            <div className="p-2 rounded bg-slate-900 border border-white/5">
                              <span className="text-slate-500 block text-[9px] uppercase">Gate</span>
                              <span className="text-emerald-300 font-bold">
                                {m.pal.approvalGates.length ? m.pal.approvalGates[0] : "None (Auto)"}
                              </span>
                            </div>
                          </div>

                          <div className="text-[10px] text-slate-400 pt-1">
                            <strong>Dispatched Sub-Agents:</strong>{" "}
                            <span className="text-purple-300 font-semibold">
                              {m.pal.subAgents.join(", ")}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Message Content Render */}
                  <div className="whitespace-pre-wrap font-sans text-xs md:text-sm leading-relaxed">
                    {m.content}
                  </div>

                  {/* Message Footer Actions */}
                  {!isUser && (
                    <div className="mt-3 pt-2.5 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400">
                      <div className="flex items-center gap-2 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        <span>Streamed via Vercel AI Gateway</span>
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Send to Sandbox shortcut if code detected */}
                        {m.content.includes("```") && onOpenSandboxWithCode && (
                          <button
                            onClick={() => {
                              const match = m.content.match(/```(\w+)?\n([\s\S]*?)```/);
                              if (match) {
                                onOpenSandboxWithCode(match[2], match[1] || "typescript");
                              }
                            }}
                            className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 flex items-center gap-1 cursor-pointer transition-colors"
                          >
                            <Play className="w-2.5 h-2.5 fill-current" /> Run in Sandbox
                          </button>
                        )}

                        <button
                          onClick={() => handleCopy(m.content, m.id)}
                          className="hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                        >
                          {copiedId === m.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" /> Copied
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
              </div>
            );
          })
        )}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-cyan-400 font-mono p-2">
            <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <span>Compiling PAL Intent & Streaming through Vercel Gateway...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Slash Command Autocomplete Popover */}
      {showCommands && (
        <div className="p-2 bg-slate-950 border-t border-white/10 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-1.5 max-h-40 overflow-y-auto">
          {SLASH_COMMANDS.map((item, idx) => (
            <button
              key={item.command}
              onClick={() => handleSlashSelect(item.command)}
              className="p-1.5 rounded-lg bg-slate-900/80 hover:bg-cyan-500/20 border border-white/5 hover:border-cyan-500/30 text-left text-[11px] font-mono flex items-center justify-between gap-2 transition-all cursor-pointer"
            >
              <span className="text-cyan-300 font-bold">{item.command}</span>
              <span className="text-slate-400 text-[10px] truncate">{item.desc}</span>
            </button>
          ))}
        </div>
      )}

      {/* Claude Code Input Prompt Bar */}
      <form onSubmit={handleSendMessage} className="p-3 bg-slate-950/95 border-t border-white/10">
        <div className="relative flex items-center">
          <div className="absolute left-3.5 flex items-center gap-1 font-mono text-cyan-400 text-xs font-bold pointer-events-none">
            <span>&gt;</span>
          </div>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type outcome (e.g. 'Build pricing page with Stripe') or / for slash commands..."
            className="w-full glass-input rounded-xl pl-8 pr-24 py-3 text-xs font-mono text-slate-100 placeholder:text-slate-500 focus:ring-1 focus:ring-cyan-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold transition-all shadow-md shadow-cyan-600/20 disabled:opacity-40 cursor-pointer flex items-center gap-1.5"
          >
            <span>Send</span>
            <Send className="w-3 h-3" />
          </button>
        </div>
      </form>
    </div>
  );
}
