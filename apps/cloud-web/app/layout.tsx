import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ROSTR Cloud - AI Workflow Engine",
  description: "Cloud-powered AI workflow automation with Vercel AI SDK",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-white">
        {children}
      </body>
    </html>
  );
}
