import { NextRequest, NextResponse } from "next/server";

const COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v1";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || "";

interface ComposioApp {
  name: string;
  key: string;
  appId: string;
  description: string;
  logo: string;
  categories: string[];
}

interface Connection {
  id: string;
  appName: string;
  status: string;
  createdAt: string;
}

/**
 * GET /api/integrations/list
 *
 * Lists all available Composio apps and the current user's connected accounts.
 * Query params:
 *   - entity_id (required): The ROSTR user identifier
 */
export async function GET(req: NextRequest) {
  const entityId = req.nextUrl.searchParams.get("entity_id");

  if (!entityId) {
    return NextResponse.json(
      { error: "entity_id query parameter is required" },
      { status: 400 }
    );
  }

  if (!COMPOSIO_API_KEY) {
    return NextResponse.json(
      { error: "COMPOSIO_API_KEY not configured on server" },
      { status: 500 }
    );
  }

  try {
    // Fetch available apps and user connections in parallel
    const [appsResponse, connectionsResponse] = await Promise.all([
      fetch(`${COMPOSIO_BASE_URL}/apps`, {
        headers: { "x-api-key": COMPOSIO_API_KEY },
      }),
      fetch(
        `${COMPOSIO_BASE_URL}/connectedAccounts?user_uuid=${encodeURIComponent(entityId)}`,
        {
          headers: { "x-api-key": COMPOSIO_API_KEY },
        }
      ),
    ]);

    if (!appsResponse.ok) {
      const errText = await appsResponse.text();
      return NextResponse.json(
        { error: "Failed to fetch apps from Composio", detail: errText },
        { status: appsResponse.status }
      );
    }

    const appsData = await appsResponse.json();
    const apps: ComposioApp[] = Array.isArray(appsData)
      ? appsData
      : appsData.items || appsData.apps || [];

    // Connections may be empty if entity has none yet
    let connections: Connection[] = [];
    if (connectionsResponse.ok) {
      const connData = await connectionsResponse.json();
      connections = Array.isArray(connData)
        ? connData
        : connData.items || connData.connectedAccounts || [];
    }

    // Build connected app set
    const connectedApps = new Set(
      connections
        .filter((c) => c.status === "active")
        .map((c) => c.appName?.toLowerCase())
    );

    // Merge into unified response
    const integrations = apps.map((app) => {
      const appKey = (app.key || app.name || "").toLowerCase();
      return {
        name: app.name || app.key,
        key: app.key || app.name,
        appId: app.appId || app.key,
        description: app.description || "",
        logo: app.logo || "",
        categories: app.categories || [],
        connected: connectedApps.has(appKey),
      };
    });

    return NextResponse.json({
      integrations,
      totalApps: integrations.length,
      connectedCount: connections.filter((c) => c.status === "active").length,
    });
  } catch (error: any) {
    console.error("Integrations list error:", error);
    return NextResponse.json(
      { error: "Internal server error", detail: error.message },
      { status: 500 }
    );
  }
}
