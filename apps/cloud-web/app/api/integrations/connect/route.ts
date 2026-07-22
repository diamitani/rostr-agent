import { NextRequest, NextResponse } from "next/server";

const COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v1";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || "";

/**
 * POST /api/integrations/connect
 *
 * Initiates an OAuth connection flow for a specific app.
 * Returns a redirect URL the client should navigate to.
 *
 * Body:
 *   - entity_id (required): The ROSTR user identifier
 *   - app_name (required): The Composio app key (e.g., "slack", "gmail")
 *   - redirect_url (optional): URL to redirect after OAuth completes
 *   - integration_id (optional): Specific integration ID to use
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
    integration_id?: string;
  };

  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 }
    );
  }

  const { entity_id, app_name, redirect_url, integration_id } = body;

  if (!entity_id || !app_name) {
    return NextResponse.json(
      { error: "entity_id and app_name are required" },
      { status: 400 }
    );
  }

  try {
    // Build request payload for Composio
    const payload: Record<string, any> = {
      entityId: entity_id,
      appName: app_name.toLowerCase(),
    };

    if (redirect_url) {
      payload.redirectUrl = redirect_url;
    }

    if (integration_id) {
      payload.integrationId = integration_id;
    }

    const response = await fetch(`${COMPOSIO_BASE_URL}/connectedAccounts`, {
      method: "POST",
      headers: {
        "x-api-key": COMPOSIO_API_KEY,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errText = await response.text();
      return NextResponse.json(
        {
          error: "Failed to initiate connection",
          detail: errText,
          status: response.status,
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      success: true,
      redirectUrl: data.redirectUrl || null,
      connectionId: data.id || data.connectedAccountId || null,
      connectionStatus: data.connectionStatus || data.status || "pending",
    });
  } catch (error: any) {
    console.error("Integration connect error:", error);
    return NextResponse.json(
      { error: "Internal server error", detail: error.message },
      { status: 500 }
    );
  }
}
