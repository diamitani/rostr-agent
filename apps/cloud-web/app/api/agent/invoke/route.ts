// POST /api/agent/invoke
// Proxies to EC2:8788/invoke/stream, streams SSE to browser
export const runtime = "nodejs";

const AGENTCORE_URL = process.env.AGENTCORE_URL || "http://localhost:8788";

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Proxy the streaming request to agentcore API
    const upstreamRes = await fetch(`${AGENTCORE_URL}/invoke/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!upstreamRes.ok) {
      const errText = await upstreamRes.text();
      return new Response(
        JSON.stringify({ error: `AgentCore error: ${errText}` }),
        { status: upstreamRes.status, headers: { "Content-Type": "application/json" } }
      );
    }

    // Stream SSE response back to browser
    return new Response(upstreamRes.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "invoke error";
    return Response.json({ error: message }, { status: 500 });
  }
}

export async function GET() {
  return Response.json({ status: "ok", service: "agent-invoke" });
}
