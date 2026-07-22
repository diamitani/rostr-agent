"use client";

import { useEffect, useState } from "react";

interface Workspace {
  id: string;
  name: string;
  state: string;
  createdAt: string;
}

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    // Demo workspaces
    setWorkspaces([
      {
        id: "1",
        name: "Default",
        state: "{}",
        createdAt: new Date().toISOString(),
      },
      {
        id: "2",
        name: "Research Project",
        state: "{}",
        createdAt: new Date(Date.now() - 86400000).toISOString(),
      },
    ]);
  };

  const createWorkspace = async () => {
    if (!newName.trim()) return;

    setCreating(true);
    try {
      const ws: Workspace = {
        id: Math.random().toString(36).slice(2),
        name: newName,
        state: "{}",
        createdAt: new Date().toISOString(),
      };
      setWorkspaces([...workspaces, ws]);
      setNewName("");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Workspaces</h1>
        <p className="text-slate-400 mb-8">Organize your workflows and data</p>

        {/* Create New */}
        <div className="mb-12">
          <div className="flex gap-3">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Workspace name..."
              className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:border-cyan-500 focus:outline-none"
              onKeyDown={(e) => e.key === "Enter" && createWorkspace()}
            />
            <button
              onClick={createWorkspace}
              disabled={creating}
              className="px-6 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-slate-600 rounded-lg font-semibold transition"
            >
              Create
            </button>
          </div>
        </div>

        {/* Workspaces List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workspaces.map((ws) => (
            <div
              key={ws.id}
              className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-cyan-500 transition group cursor-pointer"
            >
              <h3 className="font-semibold text-lg mb-2 group-hover:text-cyan-400 transition">
                {ws.name}
              </h3>
              <p className="text-slate-400 text-sm mb-4">
                Created {new Date(ws.createdAt).toLocaleDateString()}
              </p>
              <div className="flex gap-2">
                <button className="flex-1 px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 rounded text-sm transition">
                  Open
                </button>
                <button className="px-3 py-1 text-slate-400 hover:text-slate-200 text-sm transition">
                  ⋯
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
