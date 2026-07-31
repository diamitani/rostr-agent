// POST /api/sandbox/files — write files to sandbox container
// GET  /api/sandbox/files?session_id=xxx — read files from container
export const runtime = "nodejs";

const SANDBOX_URL = process.env.SANDBOX_URL || "http://localhost:8787";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { session_id, files, workdir } = body;

    if (!session_id || !files) {
      return Response.json({ error: "session_id and files required" }, { status: 400 });
    }

    const res = await fetch(`${SANDBOX_URL}/files`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id, files, workdir: workdir || "/workspace" }),
    });

    const data = await res.json();
    return Response.json(data, { status: res.ok ? 200 : res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "files error";
    return Response.json({ error: message }, { status: 500 });
  }
}

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get("session_id");
    const workdir = url.searchParams.get("workdir") || "/workspace";

    if (!sessionId) {
      return Response.json({ error: "session_id required" }, { status: 400 });
    }

    const res = await fetch(
      `${SANDBOX_URL}/files/${sessionId}?workdir=${encodeURIComponent(workdir)}`
    );
    const data = await res.json();
    return Response.json(data, { status: res.ok ? 200 : res.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "files error";
    return Response.json({ error: message }, { status: 500 });
  }
}
