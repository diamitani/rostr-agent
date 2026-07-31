// POST /api/auth/confirm
// Confirms signup with the verification code sent to email
import {
  CognitoIdentityProviderClient,
  ConfirmSignUpCommand,
  ResendConfirmationCodeCommand,
} from "@aws-sdk/client-cognito-identity-provider";

export const runtime = "nodejs";

const client = new CognitoIdentityProviderClient({ region: "us-east-1" });
const CLIENT_ID = process.env.COGNITO_CLIENT_ID!;

export async function POST(request: Request) {
  try {
    const { email, code, resend } = await request.json();

    if (!email) return Response.json({ error: "Email required" }, { status: 400 });

    if (resend) {
      await client.send(new ResendConfirmationCodeCommand({
        ClientId: CLIENT_ID,
        Username: email,
      }));
      return Response.json({ success: true, message: "Verification code resent" });
    }

    if (!code) return Response.json({ error: "Verification code required" }, { status: 400 });

    await client.send(new ConfirmSignUpCommand({
      ClientId: CLIENT_ID,
      Username: email,
      ConfirmationCode: code,
    }));

    return Response.json({ success: true, message: "Email verified. You can now sign in." });
  } catch (err: unknown) {
    const e = err as { name?: string; message?: string };
    if (e.name === "CodeMismatchException") {
      return Response.json({ error: "Invalid verification code" }, { status: 400 });
    }
    if (e.name === "ExpiredCodeException") {
      return Response.json({ error: "Code expired. Request a new one." }, { status: 400 });
    }
    return Response.json({ error: e.message ?? "Confirmation failed" }, { status: 500 });
  }
}
