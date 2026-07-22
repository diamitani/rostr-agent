import { NextRequest, NextResponse } from "next/server";

const COMPOSIO_BASE_URL = "https://backend.composio.dev/api/v1";
const COMPOSIO_API_KEY = process.env.COMPOSIO_API_KEY || "";

/**
 * POST /api/integrations/execute
 *
 * Execute a Composio action on behalf of a user.
 *
 * Body:
 *   - entity_id (required): The ROSTR user identifier
 *   - action (required): Action name (e.g., "SLACK_SEND_MESSAGE")
 *   - params (required): Action-specific input parameters
 *   - connected_account_id (optional): Specific connected account to use
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
    action?: string;
    params?: Record<string, any>;
    connected_account_id?: string;
  };

  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 }
    );
  }

  const { entity_id, action, params, connected_account_id } = body;

  if (!entity_id || !action || !params) {
    return NextResponse.json(
      { error: "entity_id, action, and params are required" },
      { status: 400 }
    );
  }

  try {
    const payload: Record<string, any> = {
      entityId: entity_id,
      input: params,
    };

    if (connected_account_id) {
      payload.connectedAccountId = connected_account_id;
    }

    const response = await fetch(
      `${COMPOSIO_BASE_URL}/actions/${encodeURIComponent(action)}/execute`,
      {
        method: "POST",
        headers: {
          "x-api-key": COMPOSIO_API_KEY,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      const errText = await response.text();
      return NextResponse.json(
        {
          error: "Action execution failed",
          action,
          detail: errText,
          status: response.status,
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      success: true,
      action,
      result: data,
    });
  } catch (error: any) {
    console.error("Integration execute error:", error);
    return NextResponse.json(
      { error: "Internal server error", detail: error.message },
      { status: 500 }
    );
  }
}
