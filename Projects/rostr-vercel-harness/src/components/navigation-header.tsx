"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Sparkles,
  Home as HomeIcon,
  MessageSquare,
  Cpu,
  Youtube,
  Layers,
  Terminal,
  ShieldCheck,
  Activity,
  Users,
  Map,
  Key,
  Crown,
  Github,
  ChevronDown,
  Menu,
  X,
  Zap,
} from "lucide-react";
import { UserSession } from "@/components/auth-modal";
import { BYOKConfig } from "@/components/byok-modal";

export type NavTab =
  | "home"
  | "agency"
  | "video"
  | "chat"
  | "studio"
  | "pal"
  | "sandbox"
  | "evals"
  | "gateway";

interface NavigationHeaderProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  userSession: UserSession | null;
  byokConfig: BYOKConfig | null;
  onOpenAuth: () => void;
  onOpenPricing: () => void;
  onOpenBYOK: () => void;
  onOpenSitemap: () => void;
}

export function NavigationHeader({
  activeTab,
  onSelectTab,
  selectedModel,
  onSelectModel,
  userSession,
  byokConfig,
  onOpenAuth,
  onOpenPricing,
  onOpenBYOK,
  onOpenSitemap,
}: NavigationHeaderProps) {
  const [platformDropdownOpen, setPlatformDropdownOpen] = useState(false);
  const [agentCoreDropdownOpen, setAgentCoreDropdownOpen] = useState(false);
  const [devToolsDropdownOpen, setDevToolsDropdownOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const platformRef = useRef<HTMLDivElement>(null);
  const agentCoreRef = useRef<HTMLDivElement>(null);
  const devToolsRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (platformRef.current && !platformRef.current.contains(event.target as Node)) {
        setPlatformDropdownOpen(false);
      }
      if (agentCoreRef.current && !agentCoreRef.current.contains(event.target as Node)) {
        setAgentCoreDropdownOpen(false);
      }
      if (devToolsRef.current && !devToolsRef.current.contains(event.target as Node)) {
        setDevToolsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isPlatformActive = ["home", "agency", "video"].includes(activeTab);
  const isAgentCoreActive = ["chat", "studio", "pal"].includes(activeTab);
  const isDevToolsActive = ["sandbox", "evals", "gateway"].includes(activeTab);

  const hasBYOK = !!(
    byokConfig?.gatewayKey ||
    byokConfig?.xaiKey ||
    byokConfig?.anthropicKey ||
    byokConfig?.openaiKey ||
    byokConfig?.awsAccessKey
  );

  return (
    <header className="h-16 border-b border-slate-200 bg-white/95 backdrop-blur-xl px-4 md:px-6 flex items-center justify-between sticky top-0 z-40 shadow-xs">
      {/* Brand Lockup */}
      <div className="flex items-center gap-3">
        <div
          onClick={() => {
            onSelectTab("home");
            setMobileMenuOpen(false);
          }}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-600/20 group-hover:scale-105 transition-transform">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold text-slate-900 tracking-tight">ROSTR</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-50 text-cyan-700 border border-cyan-200 font-semibold hidden sm:inline-block">
                PAL · NPAO · Hub
              </span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse hidden md:inline-block" title="System Online" />
            </div>
            <div className="text-[11px] text-slate-500 hidden md:block">
              DI-CTO Governed Multi-Agent Platform
            </div>
          </div>
        </div>
      </div>

      {/* Desktop Grouped Navigation Bar */}
      <nav className="hidden lg:flex items-center gap-1.5 bg-slate-100/80 p-1 rounded-xl border border-slate-200/80">
        {/* 1. Platform Group */}
        <div className="relative" ref={platformRef}>
          <button
            onClick={() => {
              setPlatformDropdownOpen(!platformDropdownOpen);
              setAgentCoreDropdownOpen(false);
              setDevToolsDropdownOpen(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isPlatformActive
                ? "bg-white text-cyan-700 shadow-xs font-bold border border-slate-200/60"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
            }`}
          >
            <HomeIcon className="w-3.5 h-3.5 text-cyan-600" />
            <span>Platform</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${platformDropdownOpen ? "rotate-180" : ""}`} />
          </button>

          {platformDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-64 rounded-xl bg-white border border-slate-200 shadow-xl p-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold px-2 py-1">
                Platform & Agency
              </div>
              <button
                onClick={() => {
                  onSelectTab("home");
                  setPlatformDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "home"
                    ? "bg-cyan-50 text-cyan-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-cyan-100 text-cyan-700 flex items-center justify-center shrink-0">
                  <HomeIcon className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Platform Overview</div>
                  <div className="text-[10px] text-slate-500">4 Core Pillars & Architecture</div>
                </div>
              </button>

              <button
                onClick={() => {
                  onSelectTab("agency");
                  setPlatformDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "agency"
                    ? "bg-purple-50 text-purple-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                  <Users className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">9 Specialist AI Managers</div>
                  <div className="text-[10px] text-slate-500">Autonomous Roster & Direct Chat</div>
                </div>
              </button>

              <button
                onClick={() => {
                  onSelectTab("video");
                  setPlatformDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "video"
                    ? "bg-red-50 text-red-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-red-100 text-red-700 flex items-center justify-center shrink-0">
                  <Youtube className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Patrick Diamitani Demo</div>
                  <div className="text-[10px] text-slate-500">Video Showcase & Chapters</div>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* 2. Agent Core Group */}
        <div className="relative" ref={agentCoreRef}>
          <button
            onClick={() => {
              setAgentCoreDropdownOpen(!agentCoreDropdownOpen);
              setPlatformDropdownOpen(false);
              setDevToolsDropdownOpen(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isAgentCoreActive
                ? "bg-white text-indigo-700 shadow-xs font-bold border border-slate-200/60"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-indigo-600" />
            <span>Agent Core</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${agentCoreDropdownOpen ? "rotate-180" : ""}`} />
          </button>

          {agentCoreDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-64 rounded-xl bg-white border border-slate-200 shadow-xl p-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold px-2 py-1">
                Agent Core & Runtime
              </div>
              <button
                onClick={() => {
                  onSelectTab("chat");
                  setAgentCoreDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "chat"
                    ? "bg-indigo-50 text-indigo-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                  <MessageSquare className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Governed Agent Console</div>
                  <div className="text-[10px] text-slate-500">Live Streaming Chat + PAL Trace</div>
                </div>
              </button>

              <button
                onClick={() => {
                  onSelectTab("studio");
                  setAgentCoreDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "studio"
                    ? "bg-emerald-50 text-emerald-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <Cpu className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Runtime Studio</div>
                  <div className="text-[10px] text-slate-500">5-Stage Stepper & Vector Memory</div>
                </div>
              </button>

              <button
                onClick={() => {
                  onSelectTab("pal");
                  setAgentCoreDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "pal"
                    ? "bg-purple-50 text-purple-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                  <Layers className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">PAL & NPAO Protocol</div>
                  <div className="text-[10px] text-slate-500">Compiler & 4D Formula Calculator</div>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* 3. Dev Tools Group */}
        <div className="relative" ref={devToolsRef}>
          <button
            onClick={() => {
              setDevToolsDropdownOpen(!devToolsDropdownOpen);
              setPlatformDropdownOpen(false);
              setAgentCoreDropdownOpen(false);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isDevToolsActive
                ? "bg-white text-emerald-700 shadow-xs font-bold border border-slate-200/60"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
            }`}
          >
            <Terminal className="w-3.5 h-3.5 text-emerald-600" />
            <span>Dev Tools</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${devToolsDropdownOpen ? "rotate-180" : ""}`} />
          </button>

          {devToolsDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-64 rounded-xl bg-white border border-slate-200 shadow-xl p-2 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold px-2 py-1">
                Developer Runtime & Evals
              </div>
              <button
                onClick={() => {
                  onSelectTab("sandbox");
                  setDevToolsDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "sandbox"
                    ? "bg-amber-50 text-amber-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                  <Terminal className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">Code Sandbox</div>
                  <div className="text-[10px] text-slate-500">Live JS/TS/Python Execution</div>
                </div>
              </button>

              <button
                onClick={() => {
                  onSelectTab("evals");
                  setDevToolsDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "evals"
                    ? "bg-indigo-50 text-indigo-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">EVE Benchmarks</div>
                  <div className="text-[10px] text-slate-500">10 Automated Test Suites</div>
                </div>
              </button>

              <button
                onClick={() => {
                  onSelectTab("gateway");
                  setDevToolsDropdownOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 p-2 rounded-lg text-xs transition-all text-left cursor-pointer ${
                  activeTab === "gateway"
                    ? "bg-cyan-50 text-cyan-800 font-semibold"
                    : "text-slate-700 hover:bg-slate-50"
                }`}
              >
                <div className="w-6 h-6 rounded-md bg-cyan-100 text-cyan-700 flex items-center justify-center shrink-0">
                  <Activity className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="font-semibold text-slate-900">AI Gateway Telemetry</div>
                  <div className="text-[10px] text-slate-500">Latency & Model Routing Metrics</div>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* 4. Quick Direct Jump Tabs */}
        <button
          onClick={() => onSelectTab("chat")}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
            activeTab === "chat"
              ? "bg-cyan-600 text-white shadow-xs font-bold"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
          }`}
        >
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>Agent Console</span>
        </button>

        {/* 5. Sitemap Modal Button */}
        <button
          onClick={onOpenSitemap}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-all cursor-pointer border border-transparent hover:border-indigo-200"
          title="Open Platform Sitemap & Index"
        >
          <Map className="w-3.5 h-3.5 text-indigo-500" />
          <span>Sitemap</span>
        </button>
      </nav>

      {/* Right Controls & Utilities */}
      <div className="flex items-center gap-2">
        {/* Model Selector Pill */}
        <div className="hidden xl:flex items-center gap-1.5 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 text-xs">
          <span className="text-slate-400 text-[10px] font-mono uppercase font-semibold">Model:</span>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            aria-label="Select AI Model"
            className="bg-transparent text-cyan-700 text-xs font-semibold font-mono focus:outline-none cursor-pointer pr-1"
          >
            <option value="spacexai/grok-4.5" className="bg-white text-slate-900">
              Grok 4.5 (Vercel AI Gateway)
            </option>
            <option value="anthropic/claude-sonnet-4.6" className="bg-white text-slate-900">
              Claude Sonnet 4.6 (Gateway)
            </option>
            <option value="google/gemini-3.1-flash-lite" className="bg-white text-slate-900">
              Gemini Flash Lite (cheap)
            </option>
          </select>
        </div>

        {/* BYOK Button */}
        <button
          onClick={onOpenBYOK}
          className={`px-2.5 py-1.5 rounded-lg border text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-2xs ${
            hasBYOK
              ? "bg-amber-50/80 border-amber-300 text-amber-800 font-semibold"
              : "bg-white border-slate-200 hover:border-amber-400 text-slate-700 hover:text-amber-700"
          }`}
          title="Configure API Keys Vault (BYOK)"
        >
          <Key className={`w-3.5 h-3.5 ${hasBYOK ? "text-amber-600 fill-amber-500/20" : "text-amber-500"}`} />
          <span className="hidden sm:inline font-medium">BYOK</span>
          {hasBYOK && <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />}
        </button>

        {/* Pricing / Pro Button */}
        <button
          onClick={onOpenPricing}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs ${
            userSession?.tier === "pro"
              ? "bg-purple-50 text-purple-700 border border-purple-200 font-bold"
              : "bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white shadow-md shadow-purple-600/20"
          }`}
        >
          <Crown className="w-3.5 h-3.5 text-amber-300" />
          <span className="hidden sm:inline">
            {userSession?.tier === "pro" ? "Pro Active" : "Pro Plan ($19.99)"}
          </span>
          <span className="sm:hidden">{userSession?.tier === "pro" ? "Pro" : "$19.99"}</span>
        </button>

        {/* OAuth / User Profile Button */}
        {userSession ? (
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-2 p-1 pl-2 pr-3 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 hover:border-cyan-500 transition-all cursor-pointer shadow-2xs"
          >
            {userSession.provider === "github" ? (
              <Github className="w-3.5 h-3.5 text-slate-900" />
            ) : (
              <div className="w-5 h-5 rounded-full bg-cyan-600 flex items-center justify-center text-[10px] font-bold text-white">
                {userSession.name[0]?.toUpperCase() || "U"}
              </div>
            )}
            <span className="font-semibold max-w-[80px] truncate">{userSession.name}</span>
          </button>
        ) : (
          <button
            onClick={onOpenAuth}
            className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-white transition-all cursor-pointer flex items-center gap-1.5 shadow-xs"
          >
            <Github className="w-3.5 h-3.5" />
            <span className="hidden md:inline">Sign In</span>
          </button>
        )}

        {/* Mobile Menu Toggle Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="lg:hidden p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-all cursor-pointer"
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>
      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed top-16 left-0 right-0 bottom-0 bg-white/98 backdrop-blur-2xl border-b border-slate-200 z-50 p-4 overflow-y-auto space-y-4 animate-in fade-in duration-200">
          {/* Quick Sitemap Banner */}
          <button
            onClick={() => {
              setMobileMenuOpen(false);
              onOpenSitemap();
            }}
            className="w-full p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-800 text-xs font-bold flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Map className="w-4 h-4 text-indigo-600" />
              <span>Open Interactive Platform Sitemap</span>
            </div>
            <span>→</span>
          </button>

          {/* Platform Group */}
          <div className="space-y-1">
            <div className="text-[10px] font-mono uppercase font-bold text-slate-400 px-1">
              Platform & Agency
            </div>
            <button
              onClick={() => {
                onSelectTab("home");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "home" ? "bg-cyan-50 text-cyan-800 border border-cyan-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <HomeIcon className="w-4 h-4 text-cyan-600" />
              <span>Platform Overview & 4 Pillars</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("agency");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "agency" ? "bg-purple-50 text-purple-800 border border-purple-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <Users className="w-4 h-4 text-purple-600" />
              <span>9 Specialist AI Managers</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("video");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "video" ? "bg-red-50 text-red-800 border border-red-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <Youtube className="w-4 h-4 text-red-600" />
              <span>Patrick Diamitani Demo Video</span>
            </button>
          </div>

          {/* Agent Core Group */}
          <div className="space-y-1">
            <div className="text-[10px] font-mono uppercase font-bold text-slate-400 px-1">
              Agent Core & Runtime
            </div>
            <button
              onClick={() => {
                onSelectTab("chat");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "chat" ? "bg-indigo-50 text-indigo-800 border border-indigo-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <MessageSquare className="w-4 h-4 text-indigo-600" />
              <span>Governed Agent Console</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("studio");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "studio" ? "bg-emerald-50 text-emerald-800 border border-emerald-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <Cpu className="w-4 h-4 text-emerald-600" />
              <span>Runtime Studio & Vector Memory</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("pal");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "pal" ? "bg-purple-50 text-purple-800 border border-purple-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <Layers className="w-4 h-4 text-purple-600" />
              <span>PAL & NPAO Protocol Inspector</span>
            </button>
          </div>

          {/* Dev Tools Group */}
          <div className="space-y-1">
            <div className="text-[10px] font-mono uppercase font-bold text-slate-400 px-1">
              Developer Tools & Evals
            </div>
            <button
              onClick={() => {
                onSelectTab("sandbox");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "sandbox" ? "bg-amber-50 text-amber-800 border border-amber-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <Terminal className="w-4 h-4 text-amber-600" />
              <span>Code Sandbox (JS/TS/Python)</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("evals");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "evals" ? "bg-indigo-50 text-indigo-800 border border-indigo-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <span>EVE Benchmark Suite (10 Evals)</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("gateway");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl text-xs font-semibold text-left ${
                activeTab === "gateway" ? "bg-cyan-50 text-cyan-800 border border-cyan-200" : "text-slate-700 bg-slate-50"
              }`}
            >
              <Activity className="w-4 h-4 text-cyan-600" />
              <span>AI Gateway Monitor & Telemetry</span>
            </button>
          </div>

          {/* Mobile Model Selector */}
          <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
            <div className="text-[10px] font-mono uppercase font-bold text-slate-500">
              Active LLM Gateway Model:
            </div>
            <select
              value={selectedModel}
              onChange={(e) => onSelectModel(e.target.value)}
              className="w-full p-2 rounded-lg bg-white border border-slate-200 text-xs font-semibold text-slate-800 focus:outline-none"
            >
              <option value="spacexai/grok-4.5">Grok 4.5 (Vercel AI Gateway)</option>
              <option value="anthropic/claude-sonnet-4.6">Claude Sonnet 4.6 (Gateway)</option>
              <option value="google/gemini-3.1-flash-lite">Gemini Flash Lite (cheap)</option>
            </select>
          </div>
        </div>
      )}
    </header>
  );
}
