"use client";

import dynamic from "next/dynamic";
import { useState, useRef, useCallback } from "react";

const CodeEditor = dynamic(() => import("./CodeEditor"), { ssr: false });

// ── Default project template ──────────────────────────────────────────────────
const DEFAULT_FILES: Record<string, { content: string; language: "typescript" | "html" | "css" | "javascript" }> = {
  "index.html": {
    language: "html",
    content: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My App</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div id="app">
    <h1>Hello from ROSTR Sandbox</h1>
    <p>Edit the files and click Run to preview.</p>
    <button id="btn">Click me</button>
  </div>
  <script src="main.js"></script>
</body>
</html>`,
  },
  "style.css": {
    language: "css",
    content: `body {
  font-family: system-ui, sans-serif;
  background: #09090b;
  color: #fafafa;
  padding: 2rem;
}

h1 { color: #06b6d4; }

button {
  background: #06b6d4;
  color: #09090b;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  margin-top: 1rem;
}
button:hover { background: #0891b2; }`,
  },
  "main.js": {
    language: "javascript",
    content: `document.getElementById('btn').addEventListener('click', () => {
  alert('ROSTR Agent says hi! 👋');
});

console.log('App loaded successfully.');`,
  },
};

type LogLine = { type: "info" | "error" | "success" | "warn"; text: string };

export default function SandboxPage() {
  const [files, setFiles] = useState(DEFAULT_FILES);
  const [activeFile, setActiveFile] = useState("index.html");
  const [logs, setLogs] = useState<LogLine[]>([
    { type: "info", text: "ROSTR Sandbox ready. Edit files, hit Run to preview or Deploy to ship." },
  ]);
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [deployUrl, setDeployUrl] = useState<string | null>(null);
  const [newFileName, setNewFileName] = useState("");
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [tab, setTab] = useState<"editor" | "preview" | "terminal">("editor");
  const logEndRef = useRef<HTMLDivElement>(null);

  const log = useCallback((type: LogLine["type"], text: string) => {
    setLogs((prev) => [...prev, { type, text }]);
    setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }, []);

  // ── Run: build inline preview from files ─────────────────────────────────
  const handleRun = useCallback(async () => {
    setRunning(true);
    log("info", "Building preview...");
    try {
      const res = await fetch("/api/sandbox/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Run failed");

      // Show console output from sandbox
      (data.logs as string[] ?? []).forEach((l: string) => {
        const isErr = /error|exception|throw/i.test(l);
        log(isErr ? "error" : "info", l);
      });

      setPreviewSrc(data.html);
      setTab("preview");
      log("success", "Preview ready.");
    } catch (e: unknown) {
      log("error", e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }, [files, log]);

  // ── Deploy to Vercel ──────────────────────────────────────────────────────
  const handleDeploy = useCallback(async () => {
    setDeploying(true);
    log("info", "Deploying to Vercel...");
    try {
      const res = await fetch("/api/sandbox/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Deploy failed");
      setDeployUrl(data.url);
      log("success", `Deployed! → ${data.url}`);
    } catch (e: unknown) {
      log("error", e instanceof Error ? e.message : String(e));
    } finally {
      setDeploying(false);
    }
  }, [files, log]);

  // ── AI code generation ────────────────────────────────────────────────────
  const handleAiGen = useCallback(async () => {
    if (!aiPrompt.trim()) return;
    setAiLoading(true);
    log("info", `AI: "${aiPrompt}"`);
    try {
      const res = await fetch("/api/sandbox/ai-gen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: aiPrompt, files }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "AI gen failed");
      // Merge returned files into state
      setFiles((prev) => ({ ...prev, ...data.files }));
      log("success", `AI updated: ${Object.keys(data.files).join(", ")}`);
      setAiPrompt("");
    } catch (e: unknown) {
      log("error", e instanceof Error ? e.message : String(e));
    } finally {
      setAiLoading(false);
    }
  }, [aiPrompt, files, log]);

  // ── Add new file ──────────────────────────────────────────────────────────
  const addFile = useCallback(() => {
    const name = newFileName.trim();
    if (!name) return;
    const ext = name.split(".").pop() ?? "";
    const langMap: Record<string, "typescript" | "html" | "css" | "javascript"> = {
      ts: "typescript", tsx: "typescript", js: "javascript", jsx: "javascript",
      html: "html", htm: "html", css: "css",
    };
    const language = langMap[ext] ?? "javascript";
    setFiles((prev) => ({ ...prev, [name]: { content: "", language } }));
    setActiveFile(name);
    setNewFileName("");
  }, [newFileName]);

  const deleteFile = useCallback((name: string) => {
    setFiles((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
    if (activeFile === name) setActiveFile(Object.keys(files).find((f) => f !== name) ?? "");
  }, [activeFile, files]);

  const currentFile = files[activeFile];

  return (
    <div className="flex flex-col h-full bg-slate-950 text-white">

      {/* ── Top toolbar ── */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-800 bg-slate-900/60 shrink-0 flex-wrap">
        <span className="font-bold text-cyan-400 mr-2">🖥️ Sandbox</span>

        {/* Tab switcher */}
        {(["editor", "preview", "terminal"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1 rounded text-xs font-semibold transition ${
              tab === t ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}>
            {t === "editor" ? "📝 Editor" : t === "preview" ? "🌐 Preview" : "📋 Terminal"}
          </button>
        ))}

        <div className="flex-1" />

        {/* AI prompt */}
        <input
          value={aiPrompt}
          onChange={(e) => setAiPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAiGen()}
          placeholder="Ask AI to modify code..."
          className="hidden sm:block w-56 px-3 py-1 text-xs bg-slate-800 border border-slate-700 rounded focus:outline-none focus:border-cyan-500 text-white placeholder-slate-500"
          disabled={aiLoading}
        />
        <button onClick={handleAiGen} disabled={aiLoading || !aiPrompt.trim()}
          className="px-3 py-1 text-xs rounded bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 font-semibold transition">
          {aiLoading ? "..." : "✨ AI"}
        </button>

        <button onClick={handleRun} disabled={running}
          className="px-3 py-1 text-xs rounded bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 font-semibold transition">
          {running ? "▶ Running..." : "▶ Run"}
        </button>

        <button onClick={handleDeploy} disabled={deploying}
          className="px-3 py-1 text-xs rounded bg-green-600 hover:bg-green-700 disabled:bg-slate-700 font-semibold transition">
          {deploying ? "🚀 Deploying..." : "🚀 Deploy"}
        </button>

        {deployUrl && (
          <a href={deployUrl} target="_blank" rel="noreferrer"
            className="px-3 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600 transition truncate max-w-[160px]">
            🔗 {deployUrl.replace("https://", "")}
          </a>
        )}
      </div>

      {/* ── Main area ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* File tree */}
        <div className="w-44 shrink-0 border-r border-slate-800 bg-slate-900 flex flex-col overflow-y-auto">
          <div className="px-3 py-2 text-xs text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-800">
            Files
          </div>
          <div className="flex-1 overflow-y-auto py-1">
            {Object.keys(files).map((name) => (
              <div key={name}
                className={`group flex items-center justify-between px-3 py-1.5 cursor-pointer text-sm transition ${
                  activeFile === name
                    ? "bg-cyan-600/20 text-cyan-300 border-l-2 border-cyan-500"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
                onClick={() => { setActiveFile(name); setTab("editor"); }}>
                <span className="truncate">{name}</span>
                {Object.keys(files).length > 1 && (
                  <button onClick={(e) => { e.stopPropagation(); deleteFile(name); }}
                    className="hidden group-hover:block text-red-400 hover:text-red-300 ml-1 text-xs">✕</button>
                )}
              </div>
            ))}
          </div>
          {/* New file input */}
          <div className="p-2 border-t border-slate-800">
            <input
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addFile()}
              placeholder="new-file.js"
              className="w-full px-2 py-1 text-xs bg-slate-800 border border-slate-700 rounded focus:outline-none focus:border-cyan-500 text-white placeholder-slate-600"
            />
            <button onClick={addFile} disabled={!newFileName.trim()}
              className="mt-1 w-full text-xs py-1 bg-slate-700 hover:bg-slate-600 rounded disabled:opacity-40 transition">
              + Add file
            </button>
          </div>
        </div>

        {/* Content panel */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {tab === "editor" && currentFile && (
            <CodeEditor
              key={activeFile}
              value={currentFile.content}
              language={currentFile.language}
              onChange={(v) =>
                setFiles((prev) => ({
                  ...prev,
                  [activeFile]: { ...prev[activeFile], content: v },
                }))
              }
            />
          )}

          {tab === "preview" && (
            <div className="flex-1 bg-white">
              {previewSrc ? (
                <iframe
                  srcDoc={previewSrc}
                  sandbox="allow-scripts allow-same-origin"
                  className="w-full h-full border-0"
                  title="Preview"
                />
              ) : (
                <div className="h-full flex items-center justify-center bg-slate-900 text-slate-400 text-sm">
                  Click ▶ Run to build the preview
                </div>
              )}
            </div>
          )}

          {tab === "terminal" && (
            <div className="flex-1 overflow-y-auto bg-slate-950 p-4 font-mono text-xs space-y-1">
              {logs.map((l, i) => (
                <div key={i} className={
                  l.type === "error" ? "text-red-400" :
                  l.type === "success" ? "text-green-400" :
                  l.type === "warn" ? "text-yellow-400" :
                  "text-slate-300"
                }>
                  <span className="text-slate-600 mr-2 select-none">
                    {l.type === "error" ? "✗" : l.type === "success" ? "✓" : l.type === "warn" ? "⚠" : "›"}
                  </span>
                  {l.text}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Mobile AI prompt */}
      <div className="sm:hidden flex gap-2 p-2 border-t border-slate-800 bg-slate-900">
        <input
          value={aiPrompt}
          onChange={(e) => setAiPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAiGen()}
          placeholder="Ask AI to modify code..."
          className="flex-1 px-3 py-2 text-sm bg-slate-800 border border-slate-700 rounded focus:outline-none focus:border-cyan-500 text-white placeholder-slate-500"
          disabled={aiLoading}
        />
        <button onClick={handleAiGen} disabled={aiLoading || !aiPrompt.trim()}
          className="px-4 py-2 text-sm rounded bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 font-semibold transition">
          {aiLoading ? "..." : "✨"}
        </button>
      </div>
    </div>
  );
}
