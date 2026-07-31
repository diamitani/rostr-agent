// POST /api/sandbox/ai-gen
// Prompt + current files → returns updated files
import {
  BedrockRuntimeClient,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";

export const runtime = "nodejs";

const MODEL_ID = process.env.BEDROCK_MODEL_ID ?? "us.anthropic.claude-sonnet-4-6";

const client = new BedrockRuntimeClient({
  region: process.env.AWS_REGION ?? "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
    ...(process.env.AWS_SESSION_TOKEN ? { sessionToken: process.env.AWS_SESSION_TOKEN } : {}),
  },
});

type FileMap = Record<string, { content: string; language: string }>;

const SYSTEM = `You are ROSTR Sandbox AI — a code generation assistant.
The user has a web project (HTML/CSS/JS files). They will describe a change.
You must return ONLY a JSON object with this exact shape:
{
  "files": {
    "filename.ext": { "content": "...", "language": "html|css|javascript|typescript" }
  }
}
Only include files that should be changed or created. Do not explain. Return valid JSON only.`;

export async function POST(request: Request) {
  try {
    const { prompt, files } = (await request.json()) as { prompt: string; files: FileMap };

    if (!prompt?.trim()) return Response.json({ error: "prompt required" }, { status: 400 });

    // Build a summary of current files for context
    const fileContext = Object.entries(files)
      .map(([name, { content }]) => `=== ${name} ===\n${content.slice(0, 2000)}`)
      .join("\n\n");

    const userMessage = `Current project files:\n\n${fileContext}\n\n---\nUser request: ${prompt}\n\nReturn the updated files as JSON.`;

    const body = JSON.stringify({
      anthropic_version: "bedrock-2023-05-31",
      max_tokens: 4096,
      system: SYSTEM,
      messages: [{ role: "user", content: userMessage }],
    });

    const command = new InvokeModelCommand({
      modelId: MODEL_ID,
      contentType: "application/json",
      accept: "application/json",
      body: new TextEncoder().encode(body),
    });

    const response = await client.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    const text: string = responseBody.content?.[0]?.text ?? "";

    // Extract JSON from response (may be wrapped in markdown code block)
    const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/) ??
                      text.match(/(\{[\s\S]*\})/);
    if (!jsonMatch) throw new Error("AI did not return valid JSON");

    const parsed = JSON.parse(jsonMatch[1]);
    if (!parsed.files || typeof parsed.files !== "object") {
      throw new Error("AI response missing 'files' key");
    }

    return Response.json({ files: parsed.files });
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : "ai-gen error" },
      { status: 500 }
    );
  }
}
