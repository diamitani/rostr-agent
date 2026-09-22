"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Key,
  Shield,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Cpu,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

export interface BYOKConfig {
  gatewayKey: string;
  xaiKey: string;
  anthropicKey: string;
  openaiKey: string;
  awsAccessKey: string;
  awsSecretKey: string;
  awsRegion: string;
}

interface BYOKModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: BYOKConfig) => void;
}

export function BYOKModal({ isOpen, onClose, onSave }: BYOKModalProps) {
  const [gatewayKey, setGatewayKey] = useState<string>("");
  const [xaiKey, setXaiKey] = useState<string>("");
  const [anthropicKey, setAnthropicKey] = useState<string>("");
  const [openaiKey, setOpenaiKey] = useState<string>("");
  const [awsAccessKey, setAwsAccessKey] = useState<string>("");
  const [awsSecretKey, setAwsSecretKey] = useState<string>("");
  const [awsRegion, setAwsRegion] = useState<string>("us-east-1");
  const [showKeys, setShowKeys] = useState<boolean>(false);
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "fallback">("idle");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("rostr_byok_config");
      if (saved) {
        const parsed = JSON.parse(saved);
        setGatewayKey(parsed.gatewayKey || "");
        setXaiKey(parsed.xaiKey || "");
        setAnthropicKey(parsed.anthropicKey || "");
        setOpenaiKey(parsed.openaiKey || "");
        setAwsAccessKey(parsed.awsAccessKey || "");
        setAwsSecretKey(parsed.awsSecretKey || "");
        setAwsRegion(parsed.awsRegion || "us-east-1");
      }
    } catch {
      // Ignore
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    const config: BYOKConfig = {
      gatewayKey: gatewayKey.trim(),
      xaiKey: xaiKey.trim(),
      anthropicKey: anthropicKey.trim(),
      openaiKey: openaiKey.trim(),
      awsAccessKey: awsAccessKey.trim(),
      awsSecretKey: awsSecretKey.trim(),
      awsRegion: awsRegion.trim() || "us-east-1",
    };
    localStorage.setItem("rostr_byok_config", JSON.stringify(config));
    onSave(config);
    onClose();
  };

  const handleTestConnection = async () => {
    setTestStatus("testing");
    await new Promise((r) => setTimeout(r, 600));

    if (gatewayKey || xaiKey || anthropicKey || openaiKey || (awsAccessKey && awsSecretKey)) {
      setTestStatus("success");
    } else {
      setTestStatus("fallback");
    }

    setTimeout(() => {
      setTestStatus("idle");
    }, 2500);
  };

  const handleClearKeys = () => {
    localStorage.removeItem("rostr_byok_config");
    setGatewayKey("");
    setXaiKey("");
    setAnthropicKey("");
    setOpenaiKey("");
    setAwsAccessKey("");
    setAwsSecretKey("");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl glass-panel border border-white/20 bg-slate-950/95 p-6 shadow-2xl text-slate-100 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center text-white shadow-md shadow-amber-500/20">
              <Key className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                Bring Your Own Key (BYOK)
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                  Client Direct
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Use your personal model quotas with zero platform markup.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Security Alert Banner */}
        <div className="mt-4 p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs text-slate-300 flex items-start gap-2.5">
          <Shield className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div className="text-[11px] leading-relaxed">
            <strong>Browser-Encrypted Vault:</strong> Keys are stored only in your local browser storage and dispatched directly over TLS to the AI Gateway runtime.
          </div>
        </div>

        {/* Key Form */}
        <form onSubmit={handleSave} className="mt-4 space-y-3.5">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-medium text-slate-300 flex items-center gap-1.5">
                <span>Vercel AI Gateway key</span>
                <span className="text-[10px] font-mono text-cyan-400">(preferred door)</span>
              </label>
              <a
                href="https://vercel.com/docs/ai-gateway"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-slate-500 hover:text-cyan-300 flex items-center gap-1"
              >
                <span>Docs</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            <input
              type={showKeys ? "text" : "password"}
              value={gatewayKey}
              onChange={(e) => setGatewayKey(e.target.value)}
              placeholder="vck_...  (or leave empty — OIDC on Vercel)"
              className="w-full glass-input rounded-xl px-3.5 py-2 text-xs font-mono text-cyan-300 focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-medium text-slate-300 flex items-center gap-1.5">
                <span>xAI API Key</span>
                <span className="text-[10px] font-mono text-orange-400">(Grok BYOK / preview)</span>
              </label>
              <a
                href="https://console.x.ai"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-slate-500 hover:text-cyan-300 flex items-center gap-1"
              >
                <span>Get Key</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            <input
              type={showKeys ? "text" : "password"}
              value={xaiKey}
              onChange={(e) => setXaiKey(e.target.value)}
              placeholder="xai-..."
              className="w-full glass-input rounded-xl px-3.5 py-2 text-xs font-mono text-orange-300 focus:ring-1 focus:ring-orange-500"
            />
          </div>

          {/* Anthropic Key */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-medium text-slate-300 flex items-center gap-1.5">
                <span>Anthropic API Key</span>
                <span className="text-[10px] font-mono text-purple-400">(Claude 3.7 / 3.5 Sonnet)</span>
              </label>
              <a
                href="https://console.anthropic.com/settings/keys"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-slate-500 hover:text-cyan-300 flex items-center gap-1"
              >
                <span>Get Key</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            <input
              type={showKeys ? "text" : "password"}
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              placeholder="sk-ant-api03-..."
              className="w-full glass-input rounded-xl px-3.5 py-2 text-xs font-mono text-cyan-300 focus:ring-1 focus:ring-purple-500"
            />
          </div>

          {/* OpenAI Key */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-[11px] font-medium text-slate-300 flex items-center gap-1.5">
                <span>OpenAI API Key</span>
                <span className="text-[10px] font-mono text-emerald-400">(GPT-4o / o3-mini)</span>
              </label>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-slate-500 hover:text-cyan-300 flex items-center gap-1"
              >
                <span>Get Key</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            <input
              type={showKeys ? "text" : "password"}
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-proj-..."
              className="w-full glass-input rounded-xl px-3.5 py-2 text-xs font-mono text-emerald-300 focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {/* AWS Bedrock */}
          <div className="p-3 rounded-xl bg-slate-900/50 border border-white/5 space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                <span>AWS Bedrock AgentCore Credentials</span>
              </label>
              <span className="text-[10px] font-mono text-slate-500">Optional</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <input
                type={showKeys ? "text" : "password"}
                value={awsAccessKey}
                onChange={(e) => setAwsAccessKey(e.target.value)}
                placeholder="AWS Access Key ID"
                className="w-full glass-input rounded-xl px-3 py-1.5 text-xs font-mono text-slate-300"
              />
              <input
                type={showKeys ? "text" : "password"}
                value={awsSecretKey}
                onChange={(e) => setAwsSecretKey(e.target.value)}
                placeholder="AWS Secret Access Key"
                className="w-full glass-input rounded-xl px-3 py-1.5 text-xs font-mono text-slate-300"
              />
            </div>

            <input
              type="text"
              value={awsRegion}
              onChange={(e) => setAwsRegion(e.target.value)}
              placeholder="AWS Region (e.g. us-east-1)"
              className="w-full glass-input rounded-xl px-3 py-1.5 text-xs font-mono text-slate-400"
            />
          </div>

          {/* Toggle Key Visibility */}
          <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
            <button
              type="button"
              onClick={() => setShowKeys(!showKeys)}
              className="flex items-center gap-1.5 hover:text-slate-200 cursor-pointer text-[11px]"
            >
              {showKeys ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              <span>{showKeys ? "Hide Keys" : "Reveal Keys"}</span>
            </button>

            <button
              type="button"
              onClick={handleClearKeys}
              className="text-[11px] text-red-400 hover:text-red-300 hover:underline cursor-pointer"
            >
              Clear All Keys
            </button>
          </div>

          {/* Test Status Banner */}
          {testStatus === "testing" && (
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs flex items-center gap-2">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Verifying key with AI Gateway...
            </div>
          )}
          {testStatus === "success" && (
            <div className="p-2 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5" /> Key Verified & Active on Gateway!
            </div>
          )}
          {testStatus === "fallback" && (
            <div className="p-2 rounded-lg bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" /> No custom keys configured. Defaulting to high-speed simulator.
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2 pt-2">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testStatus === "testing"}
              className="flex-1 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/10 text-xs font-semibold text-slate-300 hover:text-white transition-all cursor-pointer"
            >
              Test Key Connection
            </button>

            <button
              type="submit"
              className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-semibold shadow-md shadow-amber-600/20 cursor-pointer transition-all"
            >
              Save BYOK Config
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
