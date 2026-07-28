"use client";

import { useState, useRef, useEffect, type FormEvent } from "react";

/* ── Types ─────────────────────────────────────────────── */

type Message = {
  role: "user" | "assistant";
  content: string;
};

/* ── ROSTR API call ────────────────────────────────────── */

async function callRostr(
  messages: Message[],
  apiKey: string,
  provider: string,
  signal?: AbortSignal
): Promise<string> {
  const baseUrl =
    process.env.NEXT_PUBLIC_ROSTR_API_URL ||
    (typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
      ? "http://localhost:8080"
      : "https://api.rostragent.com");

  const res = await fetch(`${baseUrl}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "rostr-agent",
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      stream: false,
      provider,
    }),
    signal,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`ROSTR API error: ${res.status} ${body.slice(0, 200)}`);
  }

  const data = await res.json();
  return data.choices?.[0]?.message?.content || "";
}

/* ── Chat Message Bubble ───────────────────────────────── */

function ChatBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "" : ""}`}>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold mt-1">
        {isUser ? (
          <span className="bg-zinc-700 text-zinc-200 h-8 w-8 rounded-full flex items-center justify-center">U</span>
        ) : (
          <span className="bg-gradient-to-br from-[#c9a227] to-[#a67c00] text-black h-8 w-8 rounded-full flex items-center justify-center">R</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-medium text-zinc-400 mb-1">
          {isUser ? "You" : "ROSTR Agent"}
        </p>
        <div className="text-sm text-zinc-100 leading-relaxed whitespace-pre-wrap">{msg.content}</div>
      </div>
    </div>
  );
}

/* ── Main Page ─────────────────────────────────────────── */

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [showConfig, setShowConfig] = useState(false);
  const [provider, setProvider] = useState("openai");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    const allMessages = [...messages, userMsg];
    setMessages(allMessages);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const reply = await callRostr(allMessages, apiKey, provider);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#09090b]">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-zinc-800 bg-[#09090b]/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#c9a227] to-[#a67c00] flex items-center justify-center text-xs font-bold text-black">R</div>
          <div>
            <h1 className="text-sm font-semibold text-white tracking-tight">ROSTR Agent</h1>
            <p className="text-[10px] text-zinc-500 font-mono">PAL · NPAO · RAG-DAL · Hub</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-zinc-600 font-mono hidden sm:inline">BYOK · api.rostragent.com</span>
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-[11px] px-3 py-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
          >
            {showConfig ? "Done" : "Config"}
          </button>
        </div>
      </header>

      {/* Config Bar */}
      {showConfig && (
        <div className="px-6 py-3 border-b border-zinc-800 bg-zinc-900/50">
          <div className="max-w-3xl mx-auto flex flex-wrap items-center gap-3">
            <label className="text-[11px] text-zinc-400 font-medium">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-... or your API key"
              className="flex-1 min-w-[200px] px-3 py-1.5 text-xs bg-zinc-800 border border-zinc-700 rounded-md text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#c9a227]"
            />
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="px-3 py-1.5 text-xs bg-zinc-800 border border-zinc-700 rounded-md text-zinc-200"
            >
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="bedrock">AWS Bedrock</option>
            </select>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && !isLoading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#c9a227] to-[#a67c00] flex items-center justify-center text-2xl font-bold text-black mb-4">R</div>
            <h2 className="text-xl font-semibold text-white mb-2">ROSTR Agent</h2>
            <p className="text-sm text-zinc-400 text-center max-w-md mb-4">
              PAL-powered AI agent platform. Bring your own API key.
            </p>
            <div className="grid grid-cols-2 gap-2 w-full max-w-md">
              {[
                "Build a landing page for my EP",
                "Design a marketing campaign",
                "Analyze this GitHub repo",
                "Create a PRD for a SaaS tool",
              ].map((text) => (
                <button
                  key={text}
                  onClick={() => {
                    setInput(text);
                    // Auto-submit on suggestion click
                    setTimeout(() => {
                      const form = document.querySelector("form");
                      form?.requestSubmit();
                    }, 100);
                  }}
                  className="px-3 py-2 text-xs text-zinc-300 bg-zinc-800/50 rounded-lg border border-zinc-700/50 hover:bg-zinc-700/50 hover:border-[#c9a227]/30 transition-colors text-left"
                >
                  {text}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => <ChatBubble key={i} msg={msg} />)
        )}

        {isLoading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#c9a227] to-[#a67c00] text-black text-xs font-bold">R</div>
            <div className="flex items-center gap-1 pt-2">
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-red-900/30 border border-red-800 text-red-300 text-xs">{error}</div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex items-end gap-2 px-4 py-3 border-t border-zinc-800 bg-zinc-900/50">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message ROSTR Agent..."
          className="flex-1 min-h-[44px] rounded-xl bg-zinc-800 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 outline-none ring-1 ring-zinc-700 focus:ring-[#c9a227]/50 disabled:opacity-50"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="flex h-[44px] w-[44px] items-center justify-center rounded-xl bg-[#c9a227] text-black font-bold text-sm hover:bg-[#a67c00] transition-colors disabled:opacity-30"
        >
          →
        </button>
      </form>

      {/* Footer */}
      <footer className="px-6 py-1.5 border-t border-zinc-800/50 bg-[#09090b]">
        <p className="text-[10px] text-zinc-600 text-center font-mono">ROSTR Agent v1.0 — Runtime · Orchestration · State · Tools · Reference</p>
      </footer>
    </div>
  );
}
