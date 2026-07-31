// POST /api/sandbox/session — create/destroy Docker sandbox session
// GET  /api/sandbox/session?id=xxx — get session info
export const runtime = "nodejs";

const SANDBOX_URL = process.env.SANDBOX_URL || "http://localhost:8787";

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const action = body.action || "create";

    if (action === "create") {
      const res = await fetch(`${SANDBOX_URL}/session`, { method: "POST" });
      if (!res.ok) throw new Error(`Sandbox error: ${await res.text()}`);
      const data = await res.json();
      return Response.json(data);
    }

    if (action === "destroy" && body.session_id) {
      const res = await fetch(`${SANDBOX_URL}/session/${body.session_id}`, {
        method: "DELETE",
      });
      const data = await res.json().catch(() => ({ status: "destroyed" }));
      return Response.json(data);
    }

    return Response.json({ error: "Unknown action" }, { status: 400 });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "session error";
    return Response.json({ error: message }, { status: 500 });
  }
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const sessionId = url.searchParams.get("id");
  if (!sessionId) {
    const res = await fetch(`${SANDBOX_URL}/health`);
    return Response.json(await res.json());
  }
  return Response.json({ session_id: sessionId, status: "active" });
}
