"use client";

import { useChat } from "@vercel/ai/react";
import { useEffect, useRef } from "react";
import { useState } from "react";

export default function ChatPage() {
  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    stop,
  } = useChat({
    api: "/api/orchestrate",
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!mounted) return null;

  return (
    <div className="h-full flex flex-col">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-400">
            <div className="text-center">
              <div className="text-4xl mb-4">💬</div>
              <p>Start a conversation...</p>
            </div>
          </div>
        ) : (
          messages.map((message, i) => (
            <div
              key={i}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              } animate-fade-in`}
            >
              <div
                className={`max-w-md px-4 py-2 rounded-lg ${
                  message.role === "user"
                    ? "bg-cyan-600 text-white rounded-br-none"
                    : "bg-slate-800 text-slate-100 rounded-bl-none"
                }`}
              >
                <p className="text-sm leading-relaxed break-words">
                  {message.content}
                </p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-slate-800 text-slate-100 px-4 py-2 rounded-lg rounded-bl-none">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse delay-100" />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse delay-200" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-800 bg-slate-900/50 backdrop-blur-md p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            value={input}
            onChange={handleInputChange}
            placeholder="Ask me anything... (Ctrl+Enter to send)"
            className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:border-cyan-500 focus:outline-none transition text-white placeholder-slate-500"
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.ctrlKey) {
                handleSubmit(e as any);
              }
            }}
          />
          {isLoading ? (
            <button
              type="button"
              onClick={() => stop()}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="px-6 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 rounded-lg font-semibold transition"
            >
              Send
            </button>
          )}
        </form>

        {/* Info Footer */}
        <div className="text-xs text-slate-500 mt-3 text-center">
          Powered by Vercel AI SDK • Uses your Anthropic key
        </div>
      </div>
    </div>
  );
}
