import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ROSTR Agent — Cloud AI Agent Platform",
  description:
    "ROSTR Agent: Runtime, Orchestration, State, Tools, Reference. PAL-powered AI agent platform with AWS Agent Core.",
  openGraph: {
    title: "ROSTR Agent",
    description: "Production AI Agent Platform — ROSTR/PAL + AWS Agent Core",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
