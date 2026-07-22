import { sql } from "@vercel/postgres";
import { kv } from "@vercel/kv";
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
      // Get user plan
      const userResult = await sql`
        SELECT plan, created_at FROM users WHERE id = ${userId}
      `;

      const userRow =
        userResult.rows.length > 0
          ? userResult.rows[0]
          : { plan: "free", created_at: new Date().toISOString() };

      // Get daily execution count
      const today = new Date().toISOString().split("T")[0];
      const dailyCount = await kv.get<number>(`executions:${userId}:${today}`);

      // Get monthly execution count
      const monthStart = new Date();
      monthStart.setDate(1);
      const monthKey = monthStart.toISOString().slice(0, 7);

      const monthlyResult = await sql`
        SELECT COUNT(*) as count FROM executions
        WHERE user_id = ${userId}
        AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', NOW())
      `;

      const monthlyCount =
        monthlyResult.rows.length > 0
          ? parseInt(monthlyResult.rows[0].count || "0")
          : 0;

      // Calculate spend ($0.10 per 1000 executions)
      const monthlySpend = (monthlyCount / 1000) * 0.1;

      // Calculate next billing date
      const nextBilling = new Date();
      nextBilling.setDate(nextBilling.getDate() + 30);

      return new Response(
        JSON.stringify({
          plan: userRow.plan || "free",
          status: "active",
          executionsToday: dailyCount || 0,
          dailyLimit: userRow.plan === "free" ? 10 : 1000,
          monthlyUsage: monthlyCount,
          monthlySpend: monthlySpend.toFixed(2),
          nextBillingDate: nextBilling.toISOString(),
        }),
        { status: 200 }
      );
    } catch (dbError) {
      console.log("Database not configured, returning demo status");
      // Demo response if DB not available
      return new Response(
        JSON.stringify({
          plan: "free",
          status: "active",
          executionsToday: 3,
          dailyLimit: 10,
          monthlyUsage: 45,
          monthlySpend: "0.00",
          nextBillingDate: new Date(Date.now() + 30 * 86400000).toISOString(),
        }),
        { status: 200 }
      );
    }
  } catch (error) {
    console.error("API error:", error);
    return new Response(
      JSON.stringify({ error: "Failed to fetch billing status" }),
      { status: 500 }
    );
  }
}
