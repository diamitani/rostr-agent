import { streamText } from "@vercel/ai";
import { anthropic } from "@ai-sdk/anthropic";
import { kv } from "@vercel/kv";
import { sql } from "@vercel/postgres";
import { headers } from "next/headers";

export const runtime = "nodejs";
export const maxDuration = 60;

async function getUserId(): Promise<string> {
  const headersList = await headers();
  const authHeader = headersList.get("authorization");
  const token = authHeader?.split(" ")[1];

  if (!token) {
    throw new Error("Unauthorized");
  }

  // In production, validate JWT token
  // For demo, use token as user ID
  return token.split("-")[0] || "demo-user";
}

async function saveExecution(
  userId: string,
  input: string,
  output: string,
  tokensUsed: number
) {
  try {
    await sql`
      INSERT INTO executions (user_id, input, output, tokens_used, created_at)
      VALUES (${userId}, ${input}, ${output}, ${tokensUsed}, NOW())
    `;

    // Track daily usage for free tier
    const today = new Date().toISOString().split("T")[0];
    const cacheKey = `executions:${userId}:${today}`;
    await kv.incr(cacheKey);
    await kv.expire(cacheKey, 86400);
  } catch (error) {
    console.error("Failed to save execution:", error);
  }
}

export async function POST(request: Request) {
  try {
    const userId = await getUserId();

    // Check daily limit for free tier
    const today = new Date().toISOString().split("T")[0];
    const cacheKey = `executions:${userId}:${today}`;
    const count = await kv.get<number>(cacheKey);

    if (count && count >= 10) {
      // Check actual plan
      const user = await sql`SELECT plan FROM users WHERE id = ${userId}`;
      if (user.rows[0]?.plan === "free") {
        return new Response(
          JSON.stringify({ error: "Daily limit exceeded" }),
          { status: 429 }
        );
      }
    }

    const { messages } = await request.json();
    const lastMessage = messages[messages.length - 1];

    // Stream response from Claude
    const result = await streamText({
      model: anthropic("claude-3-5-sonnet-20241022"),
      system: `You are ROSTR, an AI workflow automation assistant powered by Vercel AI SDK.
You help users with:
- Orchestrating complex workflows
- Managing skills and integrations
- Analyzing data and generating insights
- Automating repetitive tasks

Always be helpful, concise, and action-oriented.`,
      messages: messages,
      temperature: 0.7,
      maxTokens: 2048,
    });

    // Collect full response for database
    let fullResponse = "";
    let tokenCount = 0;

    // Stream the response
    const encoder = new TextEncoder();
    const customStream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of result.fullStream) {
            if (
              chunk.type === "text-delta" ||
              chunk.type === "text-content"
            ) {
              const text = "text" in chunk ? chunk.text : "";
              fullResponse += text;
              const encoded = encoder.encode(
                `data: ${JSON.stringify({ type: "text", content: text })}\n\n`
              );
              controller.enqueue(encoded);
            }
            if (chunk.type === "finish") {
              tokenCount = chunk.usage?.totalTokens || 0;
            }
          }

          // Save execution
          await saveExecution(
            userId,
            lastMessage.content,
            fullResponse,
            tokenCount
          );

          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ type: "done" })}\n\n`)
          );
          controller.close();
        } catch (error) {
          console.error("Stream error:", error);
          controller.error(error);
        }
      },
    });

    return new Response(customStream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    console.error("API error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Internal server error",
      }),
      { status: 500 }
    );
  }
}
