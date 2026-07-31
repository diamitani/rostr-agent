"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { html } from "@codemirror/lang-html";
import { css } from "@codemirror/lang-css";
import { oneDark } from "@codemirror/theme-one-dark";
import { python } from "@codemirror/lang-python";

// ── Types ─────────────────────────────────────────────────────────────────────

type FileEntry = { content: string; language: string };
type FileMap = Record<string, FileEntry>;

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  fileChanges?: Array<{ path: string; content: string }>;
  commands?: string[];
  timestamp: Date;
};

type TerminalLine = {
  id: string;
  type: "output" | "error" | "info" | "done";
  text: string;
};

type ComposioTool = {
  id: string;
  name: string;
  description: string;
  connected: boolean;
  icon: string;
  actions: string[];
};

// ── Default files ─────────────────────────────────────────────────────────────

const DEFAULT_FILES: FileMap = {
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
    <p>Chat with the AI agent to build your app. Try: "add a login form"</p>
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
  margin: 0;
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
    content: `document.getElementById('btn')?.addEventListener('click', () => {
  alert('ROSTR Agent says hi! 👋');
});
console.log('App loaded.');`,
  },
};

// ── Language detection ─────────────────────────────────────────────────────────

function getLanguage(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "js":
    case "jsx":
    case "ts":
    case "tsx":
      return javascript({ jsx: true, typescript: ext === "ts" || ext === "tsx" });
    case "html":
      return html();
    case "css":
      return css();
    case "py":
      return python();
    default:
      return javascript();
  }
}

function getLangName(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    js: "javascript", jsx: "javascript", ts: "typescript", tsx: "typescript",
    html: "html", css: "css", py: "python", json: "json", md: "markdown",
  };
  return map[ext] || "text";
}

function generateId() {
  return Math.random().toString(36).slice(2);
}

// ── Main IDE Component ─────────────────────────────────────────────────────────

export default function SandboxIDE() {
  const [files, setFiles] = useState<FileMap>(DEFAULT_FILES);
  const [activeFile, setActiveFile] = useState("index.html");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionLoading, setSessionLoading] = useState(false);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: generateId(),
      role: "assistant",
      content: "Hello! I'm your AI coding agent. Tell me what you want to build and I'll write the code. Try: \"add a login form\" or \"create a todo list app\"",
      timestamp: new Date(),
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const [terminalLines, setTerminalLines] = useState<TerminalLine[]>([
    { id: generateId(), type: "info", text: "ROSTR Terminal — ready. Connect a sandbox to run commands." },
  ]);
  const [terminalInput, setTerminalInput] = useState("");
  const [terminalRunning, setTerminalRunning] = useState(false);
  const [terminalOpen, setTerminalOpen] = useState(true);

  const [composioTools, setComposioTools] = useState<ComposioTool[]>([]);
  const [sidebarTab, setSidebarTab] = useState<"files" | "tools">("files");
  const [newFileName, setNewFileName] = useState("");
  const [showNewFile, setShowNewFile] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [deployUrl, setDeployUrl] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // ── Init ──────────────────────────────────────────────────────────────────

  useEffect(() => {
    // Load Composio tools
    fetch("/api/composio/tools")
      .then((r) => r.json())
      .then((d) => setComposioTools(d.tools || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [terminalLines]);

  // ── Session management ─────────────────────────────────────────────────────

  const createSession = useCallback(async () => {
    setSessionLoading(true);
    addTerminalLine("info", "Creating sandbox container…");
    try {
      const res = await fetch("/api/sandbox/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "create" }),
      });
      const data = await res.json();
      if (data.session_id) {
        setSessionId(data.session_id);
        addTerminalLine("info", `✓ Sandbox ready — session: ${data.session_id}`);
        // Sync current files to container
        await syncFilesToContainer(data.session_id);
      } else {
        addTerminalLine("error", `Failed: ${data.error || "unknown"}`);
      }
    } catch (e) {
      addTerminalLine("error", `Connection failed: ${e}`);
    } finally {
      setSessionLoading(false);
    }
  }, [files]);

  const syncFilesToContainer = useCallback(async (sid: string) => {
    const fileContents: Record<string, string> = {};
    Object.entries(files).forEach(([path, f]) => {
      fileContents[path] = f.content;
    });
    try {
      await fetch("/api/sandbox/files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid, files: fileContents }),
      });
      addTerminalLine("info", `✓ Synced ${Object.keys(fileContents).length} files to container`);
    } catch (e) {
      addTerminalLine("error", `File sync failed: ${e}`);
    }
  }, [files]);

  // ── Terminal ───────────────────────────────────────────────────────────────

  const addTerminalLine = (type: TerminalLine["type"], text: string) => {
    setTerminalLines((prev) => [...prev, { id: generateId(), type, text }]);
  };

  const runCommand = useCallback(async (command: string) => {
    if (!command.trim()) return;
    if (!sessionId) {
      addTerminalLine("error", "No sandbox session. Click 'Start Sandbox' first.");
      return;
    }
    setTerminalRunning(true);
    addTerminalLine("info", `$ ${command}`);
    setTerminalInput("");

    try {
      const res = await fetch("/api/sandbox/terminal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, command }),
      });

      if (!res.ok) {
        addTerminalLine("error", `Error: ${await res.text()}`);
        setTerminalRunning(false);
        return;
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      if (!reader) {
        setTerminalRunning(false);
        return;
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === "output") addTerminalLine("output", evt.text);
              else if (evt.type === "error") addTerminalLine("error", evt.text);
              else if (evt.type === "done") {
                addTerminalLine("info", "─────────");
              }
            } catch {}
          }
        }
      }
    } catch (e) {
      addTerminalLine("error", `Terminal error: ${e}`);
    } finally {
      setTerminalRunning(false);
    }
  }, [sessionId]);

  // ── Agent chat ─────────────────────────────────────────────────────────────

  const sendChat = useCallback(async () => {
    if (!chatInput.trim() || chatLoading) return;
    const prompt = chatInput.trim();
    setChatInput("");
    setChatLoading(true);

    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content: prompt,
      timestamp: new Date(),
    };
    setChatMessages((prev) => [...prev, userMsg]);

    // Build files context
    const filesContext: Record<string, string> = {};
    Object.entries(files).forEach(([path, f]) => {
      filesContext[path] = f.content;
    });

    // Placeholder assistant message for streaming
    const assistantId = generateId();
    setChatMessages((prev) => [
      ...prev,
      {
        id: assistantId,
        role: "assistant",
        content: "▌",
        timestamp: new Date(),
      },
    ]);

    try {
      const res = await fetch("/api/agent/invoke", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          session_id: sessionId || "browser-default",
          files_context: filesContext,
          tools: composioTools.filter((t) => t.connected).map((t) => t.id),
          provider: "bedrock",
        }),
      });

      if (!res.ok) {
        const err = await res.text();
        setChatMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: `Error: ${err}` }
              : m
          )
        );
        setChatLoading(false);
        return;
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let tokenBuffer = "";
      let finalResult: { reply?: string; file_changes?: Array<{ path: string; content: string }>; commands?: string[] } | null = null;

      if (!reader) { setChatLoading(false); return; }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === "token") {
                tokenBuffer += evt.text;
                setChatMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: tokenBuffer + "▌" }
                      : m
                  )
                );
              } else if (evt.type === "result") {
                finalResult = evt.data;
              }
            } catch {}
          }
        }
      }

      // Apply result
      if (finalResult) {
        const reply = finalResult.reply || tokenBuffer;
        const fileChanges = finalResult.file_changes || [];
        const commands = finalResult.commands || [];

        // Apply file changes
        if (fileChanges.length > 0) {
          setFiles((prev) => {
            const updated = { ...prev };
            for (const fc of fileChanges) {
              updated[fc.path] = {
                content: fc.content,
                language: getLangName(fc.path),
              };
            }
            return updated;
          });
          // Switch to first changed file
          if (fileChanges[0]) setActiveFile(fileChanges[0].path);

          // Sync to container if session exists
          if (sessionId) {
            const fileContents: Record<string, string> = {};
            fileChanges.forEach((fc) => { fileContents[fc.path] = fc.content; });
            fetch("/api/sandbox/files", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: sessionId, files: fileContents }),
            }).catch(() => {});
          }
        }

        setChatMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: reply, fileChanges, commands }
              : m
          )
        );

        // Auto-run commands if session exists
        if (commands.length > 0 && sessionId) {
          for (const cmd of commands) {
            addTerminalLine("info", `Agent suggests: ${cmd}`);
          }
        }
      } else {
        setChatMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: tokenBuffer || "Done." }
              : m
          )
        );
      }
    } catch (e) {
      setChatMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Error: ${e}` }
            : m
        )
      );
    } finally {
      setChatLoading(false);
    }
  }, [chatInput, chatLoading, files, sessionId, composioTools]);

  // ── Deploy ─────────────────────────────────────────────────────────────────

  const deploy = useCallback(async () => {
    setDeploying(true);
    addTerminalLine("info", "Deploying to Vercel…");
    try {
      const res = await fetch("/api/sandbox/deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files }),
      });
      const data = await res.json();
      if (data.url) {
        setDeployUrl(data.url);
        addTerminalLine("info", `✓ Deployed: ${data.url}`);
      } else {
        addTerminalLine("error", `Deploy failed: ${data.error || "unknown"}`);
      }
    } catch (e) {
      addTerminalLine("error", `Deploy error: ${e}`);
    } finally {
      setDeploying(false);
    }
  }, [files]);

  // ── File tree ──────────────────────────────────────────────────────────────

  const addFile = () => {
    if (!newFileName.trim()) return;
    const name = newFileName.trim();
    setFiles((prev) => ({
      ...prev,
      [name]: { content: "", language: getLangName(name) },
    }));
    setActiveFile(name);
    setNewFileName("");
    setShowNewFile(false);
  };

  const deleteFile = (name: string) => {
    if (Object.keys(files).length <= 1) return;
    setFiles((prev) => {
      const updated = { ...prev };
      delete updated[name];
      return updated;
    });
    if (activeFile === name) {
      setActiveFile(Object.keys(files).filter((f) => f !== name)[0] || "");
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  const terminalH = terminalOpen ? 220 : 36;

  return (
    <div className="flex flex-col h-screen bg-[#0d0d0d] text-zinc-100 overflow-hidden font-mono text-sm">
      {/* ── Top bar ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#111] border-b border-zinc-800 shrink-0">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-cyan-400 tracking-wider">ROSTR IDE</span>
          <span className="text-zinc-600 text-xs">v1.0</span>
        </div>
        <div className="flex items-center gap-2">
          {sessionId ? (
            <span className="text-xs bg-green-900/40 text-green-400 px-2 py-0.5 rounded-full border border-green-800">
              ● Sandbox: {sessionId.slice(0, 8)}…
            </span>
          ) : (
            <button
              onClick={createSession}
              disabled={sessionLoading}
              className="text-xs bg-cyan-900/40 hover:bg-cyan-800/60 text-cyan-400 px-3 py-1 rounded border border-cyan-800 transition-colors disabled:opacity-50"
            >
              {sessionLoading ? "Starting…" : "▶ Start Sandbox"}
            </button>
          )}
          {sessionId && (
            <>
              <button
                onClick={() => { if (sessionId) syncFilesToContainer(sessionId); }}
                className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2 py-1 rounded border border-zinc-700 transition-colors"
              >
                ↑ Sync
              </button>
              <button
                onClick={() => runCommand("npm install")}
                disabled={terminalRunning}
                className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2 py-1 rounded border border-zinc-700 transition-colors"
              >
                npm install
              </button>
              <button
                onClick={() => runCommand("npm run dev")}
                disabled={terminalRunning}
                className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2 py-1 rounded border border-zinc-700 transition-colors"
              >
                npm run dev
              </button>
            </>
          )}
          <button
            onClick={deploy}
            disabled={deploying}
            className="text-xs bg-black hover:bg-zinc-900 text-white px-3 py-1 rounded border border-zinc-600 font-semibold transition-colors disabled:opacity-50"
          >
            {deploying ? "Deploying…" : "▲ Deploy"}
          </button>
          {deployUrl && (
            <a
              href={deployUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-cyan-400 hover:underline truncate max-w-[180px]"
            >
              {deployUrl}
            </a>
          )}
        </div>
      </div>

      {/* ── Main content ────────────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: File tree + Composio */}
        <div className="w-52 shrink-0 flex flex-col bg-[#111] border-r border-zinc-800">
          {/* Sidebar tabs */}
          <div className="flex border-b border-zinc-800">
            <button
              onClick={() => setSidebarTab("files")}
              className={`flex-1 text-xs py-2 transition-colors ${sidebarTab === "files" ? "text-cyan-400 border-b-2 border-cyan-400" : "text-zinc-500 hover:text-zinc-300"}`}
            >
              Files
            </button>
            <button
              onClick={() => setSidebarTab("tools")}
              className={`flex-1 text-xs py-2 transition-colors ${sidebarTab === "tools" ? "text-cyan-400 border-b-2 border-cyan-400" : "text-zinc-500 hover:text-zinc-300"}`}
            >
              Tools
            </button>
          </div>

          {/* Files panel */}
          {sidebarTab === "files" && (
            <div className="flex-1 overflow-y-auto">
              <div className="flex items-center justify-between px-3 pt-2 pb-1">
                <span className="text-zinc-500 text-xs uppercase tracking-wider">Explorer</span>
                <button
                  onClick={() => setShowNewFile(true)}
                  className="text-zinc-500 hover:text-cyan-400 text-lg leading-none transition-colors"
                  title="New file"
                >+</button>
              </div>
              {showNewFile && (
                <div className="px-2 pb-2">
                  <input
                    autoFocus
                    value={newFileName}
                    onChange={(e) => setNewFileName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") addFile();
                      if (e.key === "Escape") { setShowNewFile(false); setNewFileName(""); }
                    }}
                    placeholder="filename.tsx"
                    className="w-full bg-zinc-900 text-zinc-200 text-xs px-2 py-1 rounded border border-zinc-700 focus:outline-none focus:border-cyan-600"
                  />
                </div>
              )}
              <div className="space-y-0.5 px-1">
                {Object.keys(files).map((name) => (
                  <div
                    key={name}
                    className={`group flex items-center justify-between px-2 py-1 rounded cursor-pointer text-xs transition-colors ${
                      activeFile === name
                        ? "bg-zinc-700 text-zinc-100"
                        : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                    }`}
                    onClick={() => setActiveFile(name)}
                  >
                    <span className="truncate">{name}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteFile(name); }}
                      className="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-red-400 transition-opacity ml-1"
                    >×</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Composio Tools panel */}
          {sidebarTab === "tools" && (
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              <p className="text-zinc-600 text-xs px-1 pt-1 uppercase tracking-wider">Integrations</p>
              {composioTools.map((tool) => (
                <div key={tool.id} className="rounded border border-zinc-800 bg-zinc-900/50 p-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span>{tool.icon}</span>
                      <span className="text-xs font-medium text-zinc-300">{tool.name}</span>
                    </div>
                    {tool.connected ? (
                      <span className="text-xs text-green-400">✓</span>
                    ) : (
                      <button
                        onClick={() => {
                          window.open(
                            `/api/composio/tools`,
                            "_blank"
                          );
                        }}
                        className="text-xs text-cyan-500 hover:text-cyan-400"
                      >
                        Connect
                      </button>
                    )}
                  </div>
                  <p className="text-zinc-600 text-xs mt-1 line-clamp-2">{tool.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* CENTER: Editor + Terminal */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* File tabs */}
          <div className="flex items-center bg-[#111] border-b border-zinc-800 overflow-x-auto shrink-0">
            {Object.keys(files).map((name) => (
              <button
                key={name}
                onClick={() => setActiveFile(name)}
                className={`px-4 py-2 text-xs whitespace-nowrap border-r border-zinc-800 transition-colors ${
                  activeFile === name
                    ? "bg-[#0d0d0d] text-zinc-100 border-t-2 border-t-cyan-500"
                    : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
                }`}
              >
                {name}
              </button>
            ))}
          </div>

          {/* CodeMirror editor */}
          <div className="flex-1 overflow-hidden" style={{ height: `calc(100% - ${terminalH}px - 35px)` }}>
            {files[activeFile] && (
              <CodeMirror
                key={activeFile}
                value={files[activeFile].content}
                height="100%"
                theme={oneDark}
                extensions={[getLanguage(activeFile)]}
                onChange={(value) => {
                  setFiles((prev) => ({
                    ...prev,
                    [activeFile]: { ...prev[activeFile], content: value },
                  }));
                }}
                style={{ height: "100%", fontSize: "13px" }}
              />
            )}
          </div>

          {/* Terminal drawer */}
          <div
            className="border-t border-zinc-800 bg-[#0a0a0a] flex flex-col shrink-0 transition-all duration-150"
            style={{ height: `${terminalH}px` }}
          >
            <div
              className="flex items-center justify-between px-3 py-1 border-b border-zinc-800 cursor-pointer select-none"
              onClick={() => setTerminalOpen((p) => !p)}
            >
              <span className="text-zinc-500 text-xs">TERMINAL {terminalRunning && "●"}</span>
              <span className="text-zinc-600">{terminalOpen ? "▼" : "▲"}</span>
            </div>
            {terminalOpen && (
              <>
                <div className="flex-1 overflow-y-auto px-3 py-1 space-y-0.5">
                  {terminalLines.map((line) => (
                    <div
                      key={line.id}
                      className={`text-xs font-mono leading-5 ${
                        line.type === "error"
                          ? "text-red-400"
                          : line.type === "info"
                          ? "text-zinc-500"
                          : line.type === "done"
                          ? "text-zinc-600"
                          : "text-zinc-300"
                      }`}
                    >
                      {line.text}
                    </div>
                  ))}
                  <div ref={terminalEndRef} />
                </div>
                <div className="flex items-center px-3 py-1 border-t border-zinc-800">
                  <span className="text-green-500 text-xs mr-2">$</span>
                  <input
                    value={terminalInput}
                    onChange={(e) => setTerminalInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") runCommand(terminalInput);
                    }}
                    placeholder={sessionId ? "Enter command…" : "Start sandbox first"}
                    disabled={terminalRunning || !sessionId}
                    className="flex-1 bg-transparent text-zinc-300 text-xs focus:outline-none placeholder:text-zinc-700 disabled:opacity-50"
                  />
                </div>
              </>
            )}
          </div>
        </div>

        {/* RIGHT: Chat panel */}
        <div className="w-80 shrink-0 flex flex-col border-l border-zinc-800 bg-[#0f0f0f]">
          <div className="px-3 py-2 border-b border-zinc-800 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
            <span className="text-xs font-semibold text-zinc-300">ROSTR Agent</span>
          </div>

          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[90%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-cyan-900/60 text-cyan-100 border border-cyan-800"
                      : "bg-zinc-800/60 text-zinc-200 border border-zinc-700"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  {msg.fileChanges && msg.fileChanges.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-zinc-600">
                      <p className="text-zinc-500 text-xs mb-1">Files changed:</p>
                      {msg.fileChanges.map((fc) => (
                        <button
                          key={fc.path}
                          onClick={() => setActiveFile(fc.path)}
                          className="block text-cyan-400 hover:text-cyan-300 text-xs"
                        >
                          📄 {fc.path}
                        </button>
                      ))}
                    </div>
                  )}
                  {msg.commands && msg.commands.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-zinc-600">
                      <p className="text-zinc-500 text-xs mb-1">Suggested commands:</p>
                      {msg.commands.map((cmd) => (
                        <button
                          key={cmd}
                          onClick={() => runCommand(cmd)}
                          className="block text-xs bg-zinc-900 hover:bg-zinc-700 text-green-400 px-2 py-0.5 rounded mb-1 transition-colors font-mono"
                          title="Click to run"
                        >
                          $ {cmd}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-zinc-800/60 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-zinc-400">
                  <span className="animate-pulse">Thinking…</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat input */}
          <div className="border-t border-zinc-800 p-2">
            <div className="flex items-end gap-2">
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendChat();
                  }
                }}
                placeholder="Ask the agent to build something… (Enter to send)"
                disabled={chatLoading}
                rows={3}
                className="flex-1 bg-zinc-900 text-zinc-200 text-xs px-3 py-2 rounded-lg border border-zinc-700 focus:outline-none focus:border-cyan-600 resize-none placeholder:text-zinc-600 disabled:opacity-50"
              />
              <button
                onClick={sendChat}
                disabled={chatLoading || !chatInput.trim()}
                className="p-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white rounded-lg transition-colors self-end"
                title="Send (Enter)"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
