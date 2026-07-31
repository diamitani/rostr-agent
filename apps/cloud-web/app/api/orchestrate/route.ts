import {
  BedrockRuntimeClient,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";
import {
  createUIMessageStreamResponse,
  createUIMessageStream,
} from "ai";

export const runtime = "nodejs";
export const maxDuration = 60;

const MODEL_ID =
  process.env.BEDROCK_MODEL_ID ?? "us.anthropic.claude-sonnet-4-6";

const client = new BedrockRuntimeClient({
  region: process.env.AWS_REGION ?? "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
    ...(process.env.AWS_SESSION_TOKEN
      ? { sessionToken: process.env.AWS_SESSION_TOKEN }
      : {}),
  },
});

const SYSTEM = `You are ROSTR Agent — a production AI assistant powered by the ROSTR framework.
You help users build, deploy, and orchestrate intelligent AI workflows.
You have built-in PAL (Prompt Compiler), NPAO (Smart Routing), RAG DAL (Grounded Retrieval), and Hub (Persistent Memory).
Be specific, actionable, and concise. Lead with the answer, then explain.`;

export async function POST(request: Request) {
  try {
    const { messages } = await request.json();

    // ai@5 sends UIMessage[] with parts: [{type:"text", text:"..."}]
    // Normalise to plain {role, content} for Bedrock
    const normalised = (messages as Array<{
      role: string;
      parts?: Array<{ type: string; text?: string }>;
      content?: string | Array<{ type: string; text: string }>;
    }>).map((m) => ({
      role: m.role === "user" || m.role === "assistant" ? m.role : "user",
      content: m.parts
        ? m.parts
            .filter((p) => p.type === "text")
            .map((p) => p.text ?? "")
            .join("")
        : typeof m.content === "string"
        ? m.content
        : Array.isArray(m.content)
        ? m.content
            .filter((p) => p.type === "text")
            .map((p) => p.text)
            .join("")
        : "",
    })).filter((m) => m.content.length > 0);

    const body = JSON.stringify({
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 2048,
      system: SYSTEM,
      messages: normalised,
    });

    const command = new InvokeModelWithResponseStreamCommand({
      modelId: MODEL_ID,
      contentType: "application/json",
      accept: "application/json",
      body: new TextEncoder().encode(body),
    });

    const bedrockResponse = await client.send(command);
    const partId = crypto.randomUUID();

    // Build a UIMessageStream that the @ai-sdk/react client understands
    const uiStream = createUIMessageStream({
      execute: async ({ writer }) => {
        writer.write({ type: "text-start", id: partId });
        for await (const event of bedrockResponse.body!) {
          const chunk = event.chunk?.bytes;
          if (!chunk) continue;
          const parsed = JSON.parse(new TextDecoder().decode(chunk));
          if (
            parsed.type === "content_block_delta" &&
            parsed.delta?.type === "text_delta"
          ) {
            writer.write({
              type: "text-delta",
              id: partId,
              delta: parsed.delta.text ?? "",
            });
          }
        }
        writer.write({ type: "text-end", id: partId });
      },
    });

    return createUIMessageStreamResponse({ stream: uiStream });
  } catch (error) {
    console.error("Orchestrate error:", error);
    return new Response(
      JSON.stringify({
        error:
          error instanceof Error ? error.message : "Internal server error",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
