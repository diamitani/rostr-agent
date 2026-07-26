import { NextRequest, NextResponse } from "next/server";

const COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v3";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || "";

/**
 * POST /api/integrations/connect
 *
 * Initiates an OAuth connection flow for a specific toolkit.
 * Uses POST /api/v3/connected_accounts/link for Composio-managed OAuth.
 *
 * Body:
 *   - entity_id (required): The ROSTR user identifier
 *   - app_name (required): The toolkit slug (e.g., "slack", "gmail")
 *   - redirect_url (optional): URL to redirect after OAuth completes
 */
export async function POST(req: NextRequest) {
  if (!COMPOSIO_API_KEY) {
    return NextResponse.json(
      { error: "COMPOSIO_API_KEY not configured on server" },
      { status: 500 }
    );
  }

  let body: {
    entity_id?: string;
    app_name?: string;
    redirect_url?: string;
  };

  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { entity_id, app_name, redirect_url } = body;

  if (!entity_id || !app_name) {
    return NextResponse.json(
      { error: "entity_id and app_name are required" },
      { status: 400 }
    );
  }

  try {
    // Step 1: Get the auth config for this toolkit
    const authConfigsRes = await fetch(
      `${COMPOSIO_BASE_URL}/auth_configs?toolkit_slug=${encodeURIComponent(app_name.toLowerCase())}`,
      { headers: { "x-api-key": COMPOSIO_API_KEY } }
    );

    if (!authConfigsRes.ok) {
      return NextResponse.json(
        { error: "Failed to fetch auth configs", detail: await authConfigsRes.text() },
        { status: authConfigsRes.status }
      );
    }

    const authConfigsData = await authConfigsRes.json();
    const authConfigs = authConfigsData.items || [];

    // Prefer composio-managed OAuth config
    const authConfig =
      authConfigs.find((c: any) => c.is_composio_managed) || authConfigs[0];

    if (!authConfig) {
      return NextResponse.json(
        {
          error: `No auth config found for '${app_name}'. Configure it at https://app.composio.dev`,
        },
        { status: 404 }
      );
    }

    // Step 2: Create a connection link
    const linkPayload: Record<string, any> = {
      auth_config_id: authConfig.id,
      user_id: entity_id,
    };

    if (redirect_url) {
      linkPayload.redirect_url = redirect_url;
    }

    const linkRes = await fetch(
      `${COMPOSIO_BASE_URL}/connected_accounts/link`,
      {
        method: "POST",
        headers: {
          "x-api-key": COMPOSIO_API_KEY,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(linkPayload),
      }
    );

    if (!linkRes.ok) {
      const errText = await linkRes.text();
      return NextResponse.json(
        { error: "Failed to create connection link", detail: errText },
        { status: linkRes.status }
      );
    }

    const linkData = await linkRes.json();

    return NextResponse.json({
      success: true,
      redirectUrl: linkData.redirect_url || null,
      linkToken: linkData.link_token || null,
      connectionId: linkData.connected_account_id || null,
      expiresAt: linkData.expires_at || null,
    });
  } catch (error: any) {
    console.error("Integration connect error:", error);
    return NextResponse.json(
      { error: "Internal server error", detail: error.message },
      { status: 500 }
    );
  }
}
