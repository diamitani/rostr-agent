"use client";

import React, { useState, useEffect } from "react";
import { Network, Server, DollarSign, Activity, CheckCircle2, AlertTriangle } from "lucide-react";
import { ModelProviderConfig } from "@/lib/gateway/router";

interface GatewayMonitorProps {
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
}

interface GatewayStats {
  gatewayStatus: string;
  provider: string;
  auth: string;
  activeRouter: string;
  note: string;
  ready: boolean;
  onVercel: boolean;
  credits: { balance: string; totalUsed: string } | null;
  providers: ModelProviderConfig[];
}

export function GatewayMonitor({ selectedModel, onSelectModel }: GatewayMonitorProps) {
  const [stats, setStats] = useState<GatewayStats | null>(null);

  useEffect(() => {
    fetch("/api/gateway/stats")
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error("Failed to load gateway stats", err));
  }, []);

  const ready = Boolean(stats?.ready);
  const credits = stats?.credits;

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1">
                <Network className="w-3.5 h-3.5" /> Vercel AI Gateway
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                {stats?.provider || "resolving…"} · {stats?.auth || "auth"}
              </span>
            </div>
            <h2 className="text-xl font-bold text-white">AI Gateway Routing & Telemetry Engine</h2>
            <p className="text-xs text-slate-400 mt-1">
              {stats?.note || "Jev picks the route. Vercel AI Gateway buys the model."}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${ready ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
            <span className={`text-xs font-mono ${ready ? "text-emerald-300" : "text-amber-300"}`}>
              {ready ? "Door open" : "Decision-only (no generator key)"}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4">
          <div className="text-[11px] text-slate-400">Provider</div>
          <div className="text-lg font-bold text-cyan-400 mt-1 font-mono">
            {stats?.provider || "—"}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">{stats?.activeRouter}</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-[11px] text-slate-400">Auth</div>
          <div className="text-lg font-bold text-emerald-400 mt-1 font-mono">{stats?.auth || "—"}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            {stats?.onVercel ? "Vercel deploy (OIDC available)" : "Local / preview"}
          </div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <DollarSign className="w-3 h-3" /> Gateway credits
          </div>
          <div className="text-2xl font-bold text-purple-400 mt-1">
            {credits?.balance ?? "—"}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">
            Used {credits?.totalUsed ?? "—"}
          </div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-[11px] text-slate-400 flex items-center gap-1">
            <Activity className="w-3 h-3" /> Status
          </div>
          <div className="text-lg font-bold text-amber-400 mt-1">{stats?.gatewayStatus || "…"}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Live catalog, not a fake 18k counter</div>
        </div>
      </div>

      <div className="glass-panel overflow-hidden">
        <div className="p-4 bg-slate-950/60 border-b border-white/10 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            Vercel AI Gateway catalog
          </h3>
          <span className="text-xs text-slate-400 font-mono">Click to pin as preferred model</span>
        </div>

        <div className="divide-y divide-white/5">
          {(stats?.providers ?? []).map((p) => {
            const isSelected = selectedModel === p.modelId || (!selectedModel && p.route === "frontier");
            return (
              <div
                key={p.id}
                onClick={() => onSelectModel(p.modelId)}
                className={`p-4 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 cursor-pointer ${
                  isSelected
                    ? "bg-cyan-500/10 border-l-4 border-l-cyan-400"
                    : "hover:bg-slate-900/40"
                }`}
              >
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="text-sm font-bold text-white">{p.name}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400 uppercase">
                      {p.route}
                    </span>
                    {isSelected && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        Active Model
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-mono text-slate-400 mt-1">ID: {p.modelId}</div>
                </div>

                <div className="flex items-center gap-6 text-xs text-slate-400">
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Context</div>
                    <div className="font-mono text-slate-200">{(p.contextWindow / 1000).toFixed(0)}k tokens</div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Cost (In/Out 1M)</div>
                    <div className="font-mono text-slate-200">${p.inputCostPer1M} / ${p.outputCostPer1M}</div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Avg Latency</div>
                    <div className="font-mono text-cyan-300">{p.avgLatencyMs}ms</div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Status</div>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400">
                      {p.status === "simulator" ? (
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                      ) : (
                        <CheckCircle2 className="w-3 h-3" />
                      )}
                      {p.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
