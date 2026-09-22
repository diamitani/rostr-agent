import { streamText } from "ai";
import {
  createGatewayModel,
  gatewayProviderOptions,
  modelFor,
  resolveGateway,
  resolveLegacyModel,
  routeFromPhase,
  VERCEL_MODELS,
} from "@/lib/gateway/router";
import { compilePALIntent } from "@/lib/pal/compiler";
import { memoryStore } from "@/lib/pal/memory";

export const maxDuration = 45;

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { messages, preferredModel, customWeights, byok } = body;

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response(JSON.stringify({ error: "Messages array is required" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const gatewayKey =
      req.headers.get("x-ai-gateway-key") || byok?.gatewayKey || process.env.AI_GATEWAY_API_KEY;
    const xaiKey = req.headers.get("x-xai-key") || byok?.xaiKey || process.env.XAI_API_KEY;
    const anthropicKey =
      req.headers.get("x-anthropic-key") || byok?.anthropicKey || process.env.ANTHROPIC_API_KEY;
    const openaiKey =
      req.headers.get("x-openai-key") || byok?.openaiKey || process.env.OPENAI_API_KEY;
    const awsAccessKey =
      req.headers.get("x-aws-key") || byok?.awsAccessKey || process.env.AWS_ACCESS_KEY_ID;
    const awsSecretKey =
      req.headers.get("x-aws-secret") || byok?.awsSecretKey || process.env.AWS_SECRET_ACCESS_KEY;
    const awsRegion =
      req.headers.get("x-aws-region") || byok?.awsRegion || process.env.AWS_REGION || "us-east-1";

    const lastUserMessage = [...messages].reverse().find((m: { role: string }) => m.role === "user")?.content || "";

    const pal = compilePALIntent(lastUserMessage, customWeights);

    memoryStore.add({
      namespace: "rostr_decisions",
      content: `Compiled: "${pal.intent}" -> Phase: ${pal.phase}, Priority: ${pal.priorityScore}/10`,
      phase: pal.phase,
      tags: [pal.domain, pal.phase.toLowerCase(), ...pal.subAgents],
      metadata: { subAgents: pal.subAgents, priorityScore: pal.priorityScore },
    });

    const route = routeFromPhase(pal.phase);
    const resolved = resolveGateway({ gatewayKey, xaiKey });
    const catalog = Object.values(VERCEL_MODELS);
    const modelId =
      preferredModel && catalog.includes(preferredModel)
        ? preferredModel
        : modelFor(route, resolved.models);

    const systemPrompt = `You are DI-CTO, the Diamitani Industries governed CTO AI agent.
Operating under the ROSTR / PAL Framework:
- Phase: ${pal.phase}
- Domain: ${pal.domain}
- Priority Score: ${pal.priorityScore}/10
- Jev route: ${route} → ${modelId} via ${resolved.provider}
- Active Sub-Agents: ${pal.subAgents.join(", ")}
- Approval Gates: ${pal.approvalGates.join(", ") || "None (Auto-Approved)"}
- Operating Principles: Start with user outcome, preserve intent discipline, prefer vertical slices, make work traceable.

Deliver clear, production-grade solutions, vertical slices, and architectural code.`;

    const modelInstance =
      createGatewayModel(modelId, {
        gatewayKey,
        xaiKey,
        anthropicKey,
        openaiKey,
        route,
      }) ||
      resolveLegacyModel(preferredModel, {
        anthropicKey,
        openaiKey,
        awsAccessKey,
        awsSecretKey,
        awsRegion,
      });

    if (modelInstance) {
      try {
        const result = streamText({
          model: modelInstance,
          system: systemPrompt,
          messages: messages.map((m: { role: string; content: string }) => ({
            role: m.role as "user" | "assistant" | "system",
            content: m.content,
          })),
          temperature: 0.2,
          providerOptions: gatewayProviderOptions({
            route,
            xaiKey,
            anthropicKey,
            openaiKey,
          }),
        });

        return result.toTextStreamResponse();
      } catch {
        // Continue to simulator if stream fails
      }
    }

    const simulatedResponse = `### [ROSTR PAL Pipeline - Phase: ${pal.phase}]
**NPAO 4D Priority Score:** \`${pal.priorityScore}/10\` | **Jev route:** \`${route}\` → \`${modelId}\`
**Door:** \`${resolved.provider}\` (${resolved.auth})

I have compiled and orchestrated your request through the 5-stage ROSTR / PAL compiler. Generation is waiting on Vercel AI Gateway (set \`AI_GATEWAY_API_KEY\`, publish for OIDC, or add an xAI key).

1. **Intent Decomposition:** Domain: \`${pal.domain}\` in Phase: \`${pal.phase}\`.
2. **Governance & Soul Directive:** Loaded CTO Soul rules and active workspace blueprints.
3. **NPAO 4D Weighting:** Phase (35%), Dependency (30%), Business (25%), Resource (10%).
4. **Approval Boundary:** ${
      pal.approvalGates.length > 0
        ? `⚠️ Active Gate: \`${pal.approvalGates.join(", ")}\` (Recorded in session audit).`
        : `✅ Zero blocking approval gates required.`
    }
5. **Memory Compounding:** Persisted state vector to namespace \`rostr_decisions\`.`;

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const chunks = simulatedResponse.split(" ");
        for (let i = 0; i < chunks.length; i++) {
          const textChunk = (i === 0 ? "" : " ") + chunks[i];
          controller.enqueue(encoder.encode(textChunk));
          await new Promise((res) => setTimeout(res, 12));
        }
        controller.close();
      },
    });

    return new Response(stream, {
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Internal server error";
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
