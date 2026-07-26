import { NextRequest, NextResponse } from "next/server";

const COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || "";

interface ToolkitMeta {
  description: string;
  logo: string;
  categories: { id: string; name: string }[];
  tools_count: number;
  triggers_count: number;
}

interface Toolkit {
  name: string;
  slug: string;
  type: string;
  auth_schemes: string[];
  no_auth: boolean;
  meta: ToolkitMeta;
}

interface Connection {
  id: string;
  toolkit: { slug: string };
  status: string;
  authScheme: string;
}

/**
 * GET /api/integrations/list
 *
 * Lists all available Composio toolkits and the current user's connected accounts.
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
    // Fetch available toolkits and user connections in parallel
    const [toolkitsResponse, connectionsResponse] = await Promise.all([
      fetch(`${COMPOSIO_BASE_URL}/toolkits`, {
        headers: { "x-api-key": COMPOSIO_API_KEY },
      }),
      fetch(
        `${COMPOSIO_BASE_URL}/connected_accounts?user_uuid=${encodeURIComponent(entityId)}`,
        {
          headers: { "x-api-key": COMPOSIO_API_KEY },
        }
      ),
    ]);

    if (!toolkitsResponse.ok) {
      const errText = await toolkitsResponse.text();
      return NextResponse.json(
        { error: "Failed to fetch toolkits from Composio", detail: errText },
        { status: toolkitsResponse.status }
      );
    }

    const toolkitsData = await toolkitsResponse.json();
    const toolkits: Toolkit[] = toolkitsData.items || [];

    // Connections may be empty if entity has none yet
    let connections: Connection[] = [];
    if (connectionsResponse.ok) {
      const connData = await connectionsResponse.json();
      connections = connData.items || [];
    }

    // Build connected toolkit slugs set
    const connectedSlugs = new Set(
      connections
        .filter((c) => c.status?.toUpperCase() === "ACTIVE")
        .map((c) => c.toolkit?.slug?.toLowerCase())
        .filter(Boolean)
    );

    // Merge into unified response
    const integrations = toolkits.map((tk) => ({
      name: tk.name,
      key: tk.slug,
      slug: tk.slug,
      description: tk.meta?.description || "",
      logo: tk.meta?.logo || "",
      categories: (tk.meta?.categories || []).map((c) => c.name || c.id),
      authSchemes: tk.auth_schemes || [],
      noAuth: tk.no_auth || false,
      toolsCount: tk.meta?.tools_count || 0,
      connected: connectedSlugs.has(tk.slug?.toLowerCase()),
    }));

    return NextResponse.json({
      integrations,
      totalApps: toolkitsData.total_items || integrations.length,
      connectedCount: connections.filter(
        (c) => c.status?.toUpperCase() === "ACTIVE"
      ).length,
    });
  } catch (error: any) {
    console.error("Integrations list error:", error);
    return NextResponse.json(
      { error: "Internal server error", detail: error.message },
      { status: 500 }
    );
  }
}
