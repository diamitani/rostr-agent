// POST /api/auth/refresh  
// Refreshes Cognito tokens using refresh token
import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
} from "@aws-sdk/client-cognito-identity-provider";

export const runtime = "nodejs";

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });
const CLIENT_ID = process.env.COGNITO_CLIENT_ID!;

export async function POST(request: Request) {
  try {
    const { refreshToken } = await request.json();
    if (!refreshToken) return Response.json({ error: "Refresh token required" }, { status: 400 });

    const result = await client.send(new InitiateAuthCommand({
      AuthFlow: "REFRESH_TOKEN_AUTH",
      ClientId: CLIENT_ID,
      AuthParameters: { REFRESH_TOKEN: refreshToken },
    }));

    const auth = result.AuthenticationResult;
    if (!auth?.IdToken) return Response.json({ error: "Refresh failed" }, { status: 401 });

    const headers = new Headers();
    headers.append("Content-Type", "application/json");
    headers.append(
      "Set-Cookie",
      `auth-token=${auth.IdToken}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=86400`
    );

    return new Response(
      JSON.stringify({ token: auth.IdToken, accessToken: auth.AccessToken }),
      { status: 200, headers }
    );
  } catch (err: unknown) {
    const e = err as { message?: string };
    return Response.json({ error: e.message ?? "Refresh failed" }, { status: 401 });
  }
}
