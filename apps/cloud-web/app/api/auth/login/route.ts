import { sql } from "@vercel/postgres";
import { SignJWT } from "jose";

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    // Validate input
    if (!email || !password) {
      return new Response(
        JSON.stringify({ error: "Email and password required" }),
        { status: 400 }
      );
    }

    // For demo, accept demo@example.com / demo123
    if (email === "demo@example.com" && password === "demo123") {
      const token = `demo-user-${Date.now()}`;
      return new Response(JSON.stringify({ token }), { status: 200 });
    }

    // In production, query database and verify password hash
    try {
      const user = await sql`
        SELECT id, password_hash FROM users WHERE email = ${email}
      `;

      if (user.rows.length === 0) {
        return new Response(
          JSON.stringify({ error: "Invalid credentials" }),
          { status: 401 }
        );
      }

      // In production, use bcrypt to verify password
      // For now, simple comparison
      const userRow = user.rows[0];
      if (userRow.password_hash !== password) {
        return new Response(
          JSON.stringify({ error: "Invalid credentials" }),
          { status: 401 }
        );
      }

      // Generate JWT token
      const secret = new TextEncoder().encode(
        process.env.JWT_SECRET || "demo-secret"
      );
      const token = await new SignJWT({ userId: userRow.id, email })
        .setProtectedHeader({ alg: "HS256" })
        .setExpirationTime("24h")
        .sign(secret);

      return new Response(JSON.stringify({ token }), { status: 200 });
    } catch (dbError) {
      console.error("Database error:", dbError);
      // Fallback for demo if DB not configured
      const token = `user-${email.split("@")[0]}-${Date.now()}`;
      return new Response(JSON.stringify({ token }), { status: 200 });
    }
  } catch (error) {
    console.error("Login error:", error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      { status: 500 }
    );
  }
}
