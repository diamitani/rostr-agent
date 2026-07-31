// POST /api/auth/logout
// Clears auth cookie
export const runtime = "nodejs";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://app.rostragent.com";
const COGNITO_DOMAIN = process.env.COGNITO_DOMAIN!;
const CLIENT_ID = process.env.COGNITO_CLIENT_ID!;

export async function POST() {
  const headers = new Headers();
  headers.append(
    "Set-Cookie",
    "auth-token=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0"
  );
  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers,
  });
}

// GET /api/auth/logout — full Cognito hosted logout redirect
export async function GET() {
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    logout_uri: `${APP_URL}/login`,
  });
  return Response.redirect(`https://${COGNITO_DOMAIN}/logout?${params}`);
}
