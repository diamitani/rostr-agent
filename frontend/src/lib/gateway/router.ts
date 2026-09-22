/**
 * Vercel AI Gateway — the door System Two walks through.
 *
 * Jev (lib/jev) decides the route. This module buys the model.
 *
 * Auth order:
 *   1. AI_GATEWAY_API_KEY  → https://ai-gateway.vercel.sh/v1
 *   2. VERCEL_OIDC_TOKEN   → same door (automatic on a Vercel deploy)
 *   3. XAI_API_KEY         → https://api.x.ai/v1
 *
 * Live catalog slugs use dots (claude-sonnet-4.6), not hyphens.
 */

import { createOpenAI } from "@ai-sdk/openai";
import { createAnthropic } from "@ai-sdk/anthropic";
import { createAmazonBedrock } from "@ai-sdk/amazon-bedrock";

export const GATEWAY_BASE = "https://ai-gateway.vercel.sh/v1";
export const XAI_BASE = "https://api.x.ai/v1";

export type RouteTarget = "frontier" | "subagent" | "cheap" | "background";
export type GatewayProvider = "vercel-ai-gateway" | "xai-direct" | "none";
export type GatewayAuth = "api-key" | "oidc" | "xai-key" | "none";

export interface GatewayModels {
  frontier: string;
  subagent: string;
  cheap: string;
  background: string;
}

export interface ModelProviderConfig {
  id: string;
  name: string;
  provider: "vercel-ai-gateway" | "xai" | "anthropic" | "openai" | "bedrock" | "mock";
  modelId: string;
  route: RouteTarget | "direct";
  contextWindow: number;
  inputCostPer1M: number;
  outputCostPer1M: number;
  avgLatencyMs: number;
  status: "online" | "degraded" | "simulator" | "ready" | "fallback";
}

export const VERCEL_MODELS: GatewayModels = {
  frontier: "spacexai/grok-4.5",
  subagent: "anthropic/claude-sonnet-4.6",
  cheap: "google/gemini-3.1-flash-lite",
  background: "google/gemini-2.5-flash-lite",
};

export const VERCEL_FALLBACKS: Record<RouteTarget, string[]> = {
  frontier: ["spacexai/grok-4.1-fast-reasoning", "anthropic/claude-sonnet-4.6"],
  subagent: ["spacexai/grok-4.5", "anthropic/claude-haiku-4.5"],
  cheap: ["spacexai/grok-4.1-fast-non-reasoning", "google/gemini-2.5-flash-lite"],
  background: ["google/gemini-3.1-flash-lite", "spacexai/grok-4.1-fast-non-reasoning"],
};

const XAI_MODELS: GatewayModels = {
  frontier: "grok-4.5",
  subagent: "grok-4.5",
  cheap: "grok-4.5",
  background: "grok-4.5",
};

function trimEnv(key: string): string | undefined {
  const v = process.env[key]?.trim();
  return v || undefined;
}

export function vercelGatewaySecret(override?: string): string | undefined {
  return override?.trim() || trimEnv("AI_GATEWAY_API_KEY") || trimEnv("VERCEL_OIDC_TOKEN");
}

export function vercelAuthKind(): GatewayAuth {
  if (trimEnv("AI_GATEWAY_API_KEY")) return "api-key";
  if (trimEnv("VERCEL_OIDC_TOKEN")) return "oidc";
  return "none";
}

export function modelFor(route: RouteTarget, models: GatewayModels = VERCEL_MODELS): string {
  return models[route];
}

export function routeFromPhase(phase: string): RouteTarget {
  if (phase === "PreD") return "cheap";
  if (phase === "Design") return "subagent";
  return "frontier";
}

export function resolveGateway(opts?: { gatewayKey?: string; xaiKey?: string }) {
  if (vercelGatewaySecret(opts?.gatewayKey)) {
    return {
      provider: "vercel-ai-gateway" as const,
      auth: opts?.gatewayKey ? ("api-key" as const) : vercelAuthKind(),
      baseUrl: GATEWAY_BASE,
      models: VERCEL_MODELS,
      ready: true,
      key: vercelGatewaySecret(opts?.gatewayKey)!,
    };
  }
  const xai = opts?.xaiKey?.trim() || trimEnv("XAI_API_KEY");
  if (xai) {
    return {
      provider: "xai-direct" as const,
      auth: "xai-key" as const,
      baseUrl: XAI_BASE,
      models: XAI_MODELS,
      ready: true,
      key: xai,
    };
  }
  return {
    provider: "none" as const,
    auth: "none" as const,
    baseUrl: GATEWAY_BASE,
    models: VERCEL_MODELS,
    ready: false,
    key: undefined as string | undefined,
  };
}

function byokBlock(keys: { xai?: string; anthropic?: string; openai?: string }) {
  const byok: Record<string, { apiKey: string }[]> = {};
  if (keys.xai) byok.xai = [{ apiKey: keys.xai }];
  if (keys.anthropic) byok.anthropic = [{ apiKey: keys.anthropic }];
  if (keys.openai) byok.openai = [{ apiKey: keys.openai }];
  return Object.keys(byok).length ? byok : undefined;
}

export function createGatewayModel(
  modelId: string,
  opts?: {
    gatewayKey?: string;
    xaiKey?: string;
    anthropicKey?: string;
    openaiKey?: string;
    route?: RouteTarget;
  },
) {
  const resolved = resolveGateway({ gatewayKey: opts?.gatewayKey, xaiKey: opts?.xaiKey });
  if (!resolved.ready || !resolved.key) return null;

  const openai = createOpenAI({
    apiKey: resolved.key,
    baseURL: resolved.baseUrl,
    headers: {
      "http-referer": "https://rostr.diamitani.com",
      "x-title": "ROSTR agent",
    },
  });

  const slug =
    resolved.provider === "xai-direct"
      ? modelId.includes("grok")
        ? modelId.split("/").pop()!
        : "grok-4.5"
      : modelId;

  return openai.chat(slug);
}

export function gatewayProviderOptions(opts?: {
  route?: RouteTarget;
  xaiKey?: string;
  anthropicKey?: string;
  openaiKey?: string;
}) {
  const resolved = resolveGateway({ xaiKey: opts?.xaiKey });
  if (resolved.provider !== "vercel-ai-gateway") return undefined;
  const fallbacks = opts?.route ? VERCEL_FALLBACKS[opts.route] : [];
  const byok = byokBlock({
    xai: opts?.xaiKey || trimEnv("XAI_API_KEY"),
    anthropic: opts?.anthropicKey,
    openai: opts?.openaiKey,
  });
  return {
    gateway: {
      ...(fallbacks.length ? { models: fallbacks } : {}),
      ...(byok ? { byok } : {}),
    },
  };
}

/** Last-resort: direct Anthropic / Bedrock / OpenAI if the door is closed. */
export function resolveLegacyModel(preferredModelId?: string, keys?: {
  anthropicKey?: string;
  openaiKey?: string;
  awsAccessKey?: string;
  awsSecretKey?: string;
  awsRegion?: string;
}) {
  const modelId = preferredModelId || "";
  if (keys?.anthropicKey && (modelId.includes("claude") || modelId.includes("anthropic") || !modelId)) {
    try {
      return createAnthropic({ apiKey: keys.anthropicKey })("claude-sonnet-4.6");
    } catch {
      /* fall through */
    }
  }
  if (keys?.openaiKey && (modelId.includes("gpt") || modelId.includes("openai"))) {
    try {
      return createOpenAI({ apiKey: keys.openaiKey })("gpt-4o");
    } catch {
      /* fall through */
    }
  }
  if (keys?.awsAccessKey && keys?.awsSecretKey) {
    try {
      return createAmazonBedrock({
        region: keys.awsRegion || "us-east-1",
        accessKeyId: keys.awsAccessKey,
        secretAccessKey: keys.awsSecretKey,
      })("us.anthropic.claude-sonnet-4-6-v1:0");
    } catch {
      /* fall through */
    }
  }
  return null;
}

/** @deprecated Use createGatewayModel. Kept so existing imports compile. */
export function resolveAIModel(preferredModelId?: string) {
  return createGatewayModel(preferredModelId || VERCEL_MODELS.frontier);
}

export const AVAILABLE_MODELS: ModelProviderConfig[] = [
  {
    id: "gateway-grok-4-5",
    name: "Grok 4.5 (Vercel AI Gateway)",
    provider: "vercel-ai-gateway",
    modelId: VERCEL_MODELS.frontier,
    route: "frontier",
    contextWindow: 256000,
    inputCostPer1M: 3.0,
    outputCostPer1M: 15.0,
    avgLatencyMs: 420,
    status: "ready",
  },
  {
    id: "gateway-claude-sonnet-4-6",
    name: "Claude Sonnet 4.6 (Vercel AI Gateway)",
    provider: "vercel-ai-gateway",
    modelId: VERCEL_MODELS.subagent,
    route: "subagent",
    contextWindow: 200000,
    inputCostPer1M: 3.0,
    outputCostPer1M: 15.0,
    avgLatencyMs: 480,
    status: "ready",
  },
  {
    id: "gateway-gemini-flash",
    name: "Gemini 3.1 Flash Lite (cheap route)",
    provider: "vercel-ai-gateway",
    modelId: VERCEL_MODELS.cheap,
    route: "cheap",
    contextWindow: 1000000,
    inputCostPer1M: 0.1,
    outputCostPer1M: 0.4,
    avgLatencyMs: 180,
    status: "ready",
  },
  {
    id: "gateway-gemini-bg",
    name: "Gemini 2.5 Flash Lite (background)",
    provider: "vercel-ai-gateway",
    modelId: VERCEL_MODELS.background,
    route: "background",
    contextWindow: 1000000,
    inputCostPer1M: 0.1,
    outputCostPer1M: 0.4,
    avgLatencyMs: 160,
    status: "ready",
  },
];

export async function fetchGatewayCredits(key?: string) {
  const secret = vercelGatewaySecret(key);
  if (!secret) return null;
  try {
    const res = await fetch(`${GATEWAY_BASE}/credits`, {
      headers: { Authorization: `Bearer ${secret}` },
      signal: AbortSignal.timeout(2500),
    });
    if (!res.ok) return null;
    const json = (await res.json()) as { balance?: string; total_used?: string };
    return { balance: json.balance ?? "0", totalUsed: json.total_used ?? "0" };
  } catch {
    return null;
  }
}

export async function getGatewayStats() {
  const resolved = resolveGateway();
  const credits = resolved.provider === "vercel-ai-gateway" ? await fetchGatewayCredits() : null;
  const onVercel = Boolean(trimEnv("VERCEL") || trimEnv("VERCEL_OIDC_TOKEN"));
  return {
    gatewayStatus: resolved.ready ? "ready" : "offline",
    provider: resolved.provider,
    auth: resolved.auth,
    activeRouter: "Jev route → Vercel AI Gateway",
    note:
      resolved.provider === "vercel-ai-gateway"
        ? resolved.auth === "oidc"
          ? "OIDC is live. No API key in the workspace."
          : "Vercel AI Gateway is the door. Grok is BYOK when XAI_API_KEY is set."
        : resolved.provider === "xai-direct"
          ? "Preview fallback is xAI grok-4.5. OIDC appears on a Vercel publish."
          : "No generator key. Decision API still runs.",
    ready: resolved.ready,
    onVercel,
    credits,
    models: resolved.models,
    fallbacks: resolved.provider === "vercel-ai-gateway" ? VERCEL_FALLBACKS : {},
    providers: AVAILABLE_MODELS.map((p) => ({
      ...p,
      status: resolved.ready ? p.status : ("simulator" as const),
    })),
  };
}
