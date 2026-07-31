"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useCallback, useEffect } from "react";

// Dynamically import the full IDE (client-only, heavy deps)
const SandboxIDE = dynamic(() => import("./SandboxIDE"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-screen bg-[#0d0d0d] text-zinc-400">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm">Loading ROSTR IDE…</p>
      </div>
    </div>
  ),
});

export default function SandboxPage() {
  return <SandboxIDE />;
}
