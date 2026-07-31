// POST /api/auth/login
// Authenticates with Cognito USER_PASSWORD_AUTH, returns JWT tokens
import {
  CognitoIdentityProviderClient,
  InitiateAuthCommand,
} from "@aws-sdk/client-cognito-identity-provider";

export const runtime = "nodejs";

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });
const CLIENT_ID = process.env.COGNITO_CLIENT_ID!;

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    if (!email || !password) {
      return Response.json({ error: "Email and password required" }, { status: 400 });
    }

    const result = await client.send(new InitiateAuthCommand({
      AuthFlow: "USER_PASSWORD_AUTH",
      ClientId: CLIENT_ID,
      AuthParameters: {
        USERNAME: email,
        PASSWORD: password,
      },
    }));

    const auth = result.AuthenticationResult;
    if (!auth?.IdToken) {
      return Response.json({ error: "Authentication failed" }, { status: 401 });
    }

    // Return Cognito ID token (JWT) — client stores as cookie
    return Response.json({
      token: auth.IdToken,
      accessToken: auth.AccessToken,
      refreshToken: auth.RefreshToken,
      expiresIn: auth.ExpiresIn,
    });
  } catch (err: unknown) {
    const e = err as { name?: string; message?: string };
    if (
      e.name === "NotAuthorizedException" ||
      e.name === "UserNotFoundException"
    ) {
      return Response.json({ error: "Invalid email or password" }, { status: 401 });
    }
    if (e.name === "UserNotConfirmedException") {
      return Response.json(
        { error: "Email not verified", unconfirmed: true },
        { status: 403 }
      );
    }
    return Response.json({ error: e.message ?? "Login failed" }, { status: 500 });
  }
}
