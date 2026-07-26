import { sql } from "@vercel/postgres";
import { headers } from "next/headers";

async function getUserId(): Promise<string> {
  const headersList = await headers();
  const auth = headersList.get("authorization");
  return auth?.split(" ")[1]?.split("-")[0] || "demo-user";
}

export async function GET() {
  try {
    const userId = await getUserId();

    try {
      const result = await sql`
        SELECT id, name, description, created_at
        FROM skills
        WHERE user_id = ${userId}
        ORDER BY created_at DESC
      `;

      return new Response(
        JSON.stringify({ skills: result.rows || [] }),
        { status: 200 }
      );
    } catch (dbError) {
      console.log("Database not configured, returning demo skills");
      // Demo skills if DB not available
      const demoSkills = [
        {
          id: "1",
          name: "Web Scraper",
          description: "Extract data from web pages using CSS selectors",
          created_at: new Date().toISOString(),
        },
        {
          id: "2",
          name: "Email Scheduler",
          description: "Schedule and send emails with templates",
          created_at: new Date().toISOString(),
        },
      ];
      return new Response(
        JSON.stringify({ skills: demoSkills }),
        { status: 200 }
      );
    }
  } catch (error) {
    console.error("API error:", error);
    return new Response(
      JSON.stringify({ error: "Failed to fetch skills" }),
      { status: 500 }
    );
  }
}
