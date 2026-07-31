// GET /api/auth/callback?code=xxx
// Handles Cognito hosted UI OAuth code exchange
import {
  CognitoIdentityProviderClient,
} from "@aws-sdk/client-cognito-identity-provider";

export const runtime = "nodejs";

const COGNITO_DOMAIN = process.env.COGNITO_DOMAIN!; // e.g. artispreneur-agent.auth.us-east-1.amazoncognito.com
const CLIENT_ID = process.env.COGNITO_CLIENT_ID!;
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://app.rostragent.com";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");

  if (error) {
    return Response.redirect(`${APP_URL}/login?error=${encodeURIComponent(error)}`);
  }

  if (!code) {
    return Response.redirect(`${APP_URL}/login?error=no_code`);
  }

  try {
    // Exchange code for tokens
    const tokenRes = await fetch(`https://${COGNITO_DOMAIN}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: CLIENT_ID,
        code,
        redirect_uri: `${APP_URL}/api/auth/callback`,
      }),
    });

    if (!tokenRes.ok) {
      const err = await tokenRes.text();
      return Response.redirect(`${APP_URL}/login?error=${encodeURIComponent(err.slice(0, 100))}`);
    }

    const tokens = await tokenRes.json();
    const idToken = tokens.id_token;

    if (!idToken) {
      return Response.redirect(`${APP_URL}/login?error=no_token`);
    }

    // Set auth cookie and redirect to app
    const headers = new Headers();
    headers.append(
      "Set-Cookie",
      `auth-token=${idToken}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=86400`
    );
    headers.append("Location", `${APP_URL}/app/chat`);

    return new Response(null, { status: 302, headers });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "callback_error";
    return Response.redirect(`${APP_URL}/login?error=${encodeURIComponent(msg)}`);
  }
}

// GET /api/auth/login-url — returns Cognito hosted UI URL for OAuth
export async function POST() {
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    response_type: "code",
    scope: "openid email profile",
    redirect_uri: `${APP_URL}/api/auth/callback`,
  });
  return Response.json({
    url: `https://${COGNITO_DOMAIN}/oauth2/authorize?${params}`,
  });
}
