// POST /api/sandbox/deploy
// Deploys the sandbox files as a static Vercel project
// Returns { url: string }
export const runtime = "nodejs";

const VERCEL_TOKEN = process.env.VERCEL_TOKEN ?? "";
const VERCEL_TEAM  = process.env.VERCEL_TEAM_ID ?? "";

type FileMap = Record<string, { content: string; language: string }>;

// Vercel Deploy API: POST /v13/deployments
async function deployToVercel(files: FileMap): Promise<string> {
  if (!VERCEL_TOKEN) throw new Error("VERCEL_TOKEN env var not set");

  const deploymentFiles = Object.entries(files).map(([name, { content }]) => ({
    file: name,
    data: content,
  }));

  const teamQuery = VERCEL_TEAM ? `?teamId=${VERCEL_TEAM}` : "";
  const res = await fetch(`https://api.vercel.com/v13/deployments${teamQuery}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${VERCEL_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: `rostr-sandbox-${Date.now()}`,
      files: deploymentFiles,
      target: "production",
      projectSettings: {
        framework: null,
        buildCommand: "",
        outputDirectory: ".",
        installCommand: "echo skip",
      },
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Vercel deploy failed (${res.status}): ${err.slice(0, 300)}`);
  }

  const data = await res.json();
  // Poll until ready (max 60s)
  const deployId: string = data.id;
  const url: string = data.url ?? data.alias?.[0] ?? `${deployId}.vercel.app`;

  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 2000));
    const poll = await fetch(`https://api.vercel.com/v13/deployments/${deployId}${teamQuery}`, {
      headers: { Authorization: `Bearer ${VERCEL_TOKEN}` },
    });
    const d = await poll.json();
    if (d.readyState === "READY" || d.status === "READY") break;
    if (d.readyState === "ERROR"  || d.status === "ERROR")
      throw new Error("Vercel deployment errored");
  }

  return `https://${url}`;
}

export async function POST(request: Request) {
  try {
    const { files } = (await request.json()) as { files: FileMap };

    if (!files || typeof files !== "object") {
      return Response.json({ error: "files object required" }, { status: 400 });
    }

    const url = await deployToVercel(files);
    return Response.json({ url });
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : "deploy error" },
      { status: 500 }
    );
  }
}
