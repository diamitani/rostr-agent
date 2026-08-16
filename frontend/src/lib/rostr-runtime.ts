"use client";

import type {
  ChatModelAdapter,
  ThreadAssistantMessagePart,
} from "@assistant-ui/react";

/**
 * ROSTR Agent Chat Model Adapter
 *
 * Connects assistant-ui to the ROSTR backend via an OpenAI-compatible
 * /v1/chat/completions endpoint.
 */
export function useRostrModelAdapter(apiKey?: string): ChatModelAdapter {
  const baseUrl =
    process.env.NEXT_PUBLIC_ROSTR_API_URL ||
    (typeof window !== "undefined" &&
      (window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1")
      ? "http://localhost:8080"
      : "https://api.rostragent.com");

  const provider = process.env.NEXT_PUBLIC_LLM_PROVIDER || "agentcore";
  const userKey = apiKey || process.env.NEXT_PUBLIC_BYOK_KEY || "";

  return {
    async run({ messages, abortSignal }) {
      const openaiMessages = messages.map((m) => ({
        role: m.role === "user" ? "user" : "assistant",
        content:
          m.content.length > 0
            ? m.content.map((c: any) =>
                c.type === "text" ? c.text : ""
              ).join("")
            : "",
      }));

      const response = await fetch(`${baseUrl}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${userKey}`,
        },
        body: JSON.stringify({
          model: "rostr-agent",
          messages: openaiMessages,
          stream: false,
          provider,
        }),
        signal: abortSignal,
      });

      if (!response.ok) {
        const errorBody = await response.text().catch(() => "");
        throw new Error(
          `ROSTR API error: ${response.status} ${response.statusText}${
            errorBody ? ` — ${errorBody.slice(0, 200)}` : ""
          }`
        );
      }

      const data = await response.json();
      const replyText =
        data.choices?.[0]?.message?.content || "";

      const content: ThreadAssistantMessagePart[] = [
        {
          type: "text",
          text: replyText,
        },
      ];

      return { content };
    },
  };
}
