import { NextRequest, NextResponse } from "next/server";
import { jwtVerify, createRemoteJWKSet } from "jose";

const COGNITO_POOL_ID = process.env.COGNITO_POOL_ID || "us-east-1_VyKGNlV9r";
const REGION = "us-east-1";
const JWKS_URL = `https://cognito-idp.${REGION}.amazonaws.com/${COGNITO_POOL_ID}/.well-known/jwks.json`;

const JWKS = createRemoteJWKSet(new URL(JWKS_URL));

async function verifyToken(token: string): Promise<boolean> {
  try {
    await jwtVerify(token, JWKS, {
      issuer: `https://cognito-idp.${REGION}.amazonaws.com/${COGNITO_POOL_ID}`,
    });
    return true;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes
  const publicPrefixes = [
    "/", "/login", "/signup", "/api/auth",
    "/_next", "/favicon", "/static",
  ];
  if (publicPrefixes.some((p) => pathname === p || pathname.startsWith(p + "/"))) {
    return NextResponse.next();
  }
  // Exact root match
  if (pathname === "/") return NextResponse.next();

  // Protected — validate Cognito JWT
  const token = request.cookies.get("auth-token")?.value;
  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const valid = await verifyToken(token);
  if (!valid) {
    const res = NextResponse.redirect(new URL("/login", request.url));
    res.cookies.delete("auth-token");
    return res;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/api/protected/:path*"],
};
