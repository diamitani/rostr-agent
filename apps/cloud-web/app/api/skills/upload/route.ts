import { sql } from "@vercel/postgres";
import { headers } from "next/headers";

async function getUserId(): Promise<string> {
  const headersList = await headers();
  const auth = headersList.get("authorization");
  return auth?.split(" ")[1]?.split("-")[0] || "demo-user";
}

export async function POST(request: Request) {
  try {
    const userId = await getUserId();
    const formData = await request.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return new Response(
        JSON.stringify({ error: "No file provided" }),
        { status: 400 }
      );
    }

    // Validate file type
    const validTypes = [".skill", ".js", ".ts"];
    const fileName = file.name;
    const isValidType = validTypes.some((type) =>
      fileName.endsWith(type)
    );

    if (!isValidType) {
      return new Response(
        JSON.stringify({ error: "Invalid file type" }),
        { status: 400 }
      );
    }

    // Read file content
    const content = await file.text();

    // Extract metadata (basic parsing)
    const nameMatch = content.match(/name:\s*["']([^"']+)["']/);
    const name = nameMatch ? nameMatch[1] : fileName.split(".")[0];

    try {
      const result = await sql`
        INSERT INTO skills (user_id, name, description, code, schema, created_at)
        VALUES (
          ${userId},
          ${name},
          ${"User-uploaded skill"},
          ${content},
          ${"{}"},
          NOW()
        )
        RETURNING id, name, description, created_at
      `;

      const skill = result.rows[0];
      return new Response(JSON.stringify(skill), { status: 201 });
    } catch (dbError) {
      console.log("Database not configured, returning demo response");
      // Demo response if DB not available
      return new Response(
        JSON.stringify({
          id: Math.random().toString(36).slice(2),
          name,
          description: "User-uploaded skill",
          created_at: new Date().toISOString(),
        }),
        { status: 201 }
      );
    }
  } catch (error) {
    console.error("Upload error:", error);
    return new Response(
      JSON.stringify({ error: "Upload failed" }),
      { status: 500 }
    );
  }
}
