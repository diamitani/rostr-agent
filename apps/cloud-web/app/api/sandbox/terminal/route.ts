// POST /api/sandbox/terminal — proxy SSE from EC2:8787/exec/stream
export const runtime = "nodejs";

const SANDBOX_URL = process.env.SANDBOX_URL || "http://localhost:8787";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { session_id, command, workdir } = body;

    if (!session_id || !command) {
      return Response.json(
        { error: "session_id and command required" },
        { status: 400 }
      );
    }

    const res = await fetch(`${SANDBOX_URL}/exec/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id, command, workdir: workdir || "/workspace" }),
    });

    if (!res.ok) {
      return Response.json(
        { error: `Sandbox error: ${await res.text()}` },
        { status: res.status }
      );
    }

    // Proxy SSE stream back
    return new Response(res.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "terminal error";
    return Response.json({ error: message }, { status: 500 });
  }
}
