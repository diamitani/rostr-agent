// POST /api/auth/signup
// Creates a new user in Cognito user pool
import {
  CognitoIdentityProviderClient,
  SignUpCommand,
} from "@aws-sdk/client-cognito-identity-provider";

export const runtime = "nodejs";

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });
const CLIENT_ID = process.env.COGNITO_CLIENT_ID!;

export async function POST(request: Request) {
  try {
    const { email, password, name } = await request.json();

    if (!email || !password) {
      return Response.json({ error: "Email and password required" }, { status: 400 });
    }
    if (password.length < 8) {
      return Response.json({ error: "Password must be at least 8 characters" }, { status: 400 });
    }

    await client.send(new SignUpCommand({
      ClientId: CLIENT_ID,
      Username: email,
      Password: password,
      UserAttributes: [
        { Name: "email", Value: email },
        ...(name ? [{ Name: "name", Value: name }] : []),
      ],
    }));

    return Response.json({
      success: true,
      message: "Account created. Check your email for a verification code.",
    });
  } catch (err: unknown) {
    const e = err as { name?: string; message?: string };
    if (e.name === "UsernameExistsException") {
      return Response.json({ error: "An account with this email already exists" }, { status: 409 });
    }
    if (e.name === "InvalidPasswordException") {
      return Response.json({ error: e.message ?? "Password does not meet requirements" }, { status: 400 });
    }
    return Response.json({ error: e.message ?? "Signup failed" }, { status: 500 });
  }
}
