import { useAuth } from "../context/AuthContext";
import { useNavigate, Link } from "react-router-dom";
import { Plus, MessageSquare, Settings, LogOut } from "lucide-react";
import { useState } from "react";

export function DashboardPage() {
  const { user, workspaces, currentWorkspace, selectWorkspace, createWorkspace, logout } = useAuth();
  const navigate = useNavigate();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) return;
    
    setIsCreating(true);
    try {
      await createWorkspace(newWorkspaceName);
      setShowCreateModal(false);
      setNewWorkspaceName("");
    } catch (error) {
      console.error("Failed to create workspace:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleLaunchWorkspace = (workspace: any) => {
    selectWorkspace(workspace);
    navigate(`/workspace/${workspace.id}`);
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Header */}
      <header className="bg-zinc-900 border-b border-zinc-800">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="text-white font-semibold">ROSTR</span>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="text-zinc-400 text-sm">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Your Workspaces</h1>
          <p className="text-zinc-400">Select a workspace to launch or create a new one</p>
        </div>

        {/* Workspace Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Create New Card */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="group relative bg-zinc-900 border border-zinc-800 hover:border-cyan-500/50 rounded-2xl p-8 transition-all hover:shadow-lg hover:shadow-cyan-500/10 text-left"
          >
            <div className="w-12 h-12 bg-cyan-500/10 rounded-xl flex items-center justify-center mb-4 group-hover:bg-cyan-500/20 transition-colors">
              <Plus className="text-cyan-500" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Create Workspace</h3>
            <p className="text-zinc-500 text-sm">Start a new project with ROSTR</p>
          </button>

          {/* Existing Workspaces */}
          {workspaces.map((workspace) => (
            <div
              key={workspace.id}
              className="group relative bg-zinc-900 border border-zinc-800 hover:border-cyan-500/50 rounded-2xl p-8 transition-all hover:shadow-lg hover:shadow-cyan-500/10"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-cyan-500 rounded-xl flex items-center justify-center mb-4">
                <MessageSquare className="text-white" size={24} />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{workspace.name}</h3>
              <p className="text-zinc-500 text-sm mb-4">
                Created {new Date(workspace.createdAt).toLocaleDateString()}
              </p>
              
              <div className="flex gap-3">
                <button
                  onClick={() => handleLaunchWorkspace(workspace)}
                  className="flex-1 py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-medium rounded-lg transition-colors"
                >
                  Launch
                </button>
                <button
                  className="p-2 border border-zinc-700 hover:border-zinc-600 rounded-lg text-zinc-400 hover:text-white transition-colors"
                >
                  <Settings size={20} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {workspaces.length === 0 && (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-zinc-900 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="text-zinc-600" size={32} />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No workspaces yet</h3>
            <p className="text-zinc-500">Create your first workspace to get started</p>
          </div>
        )}
      </main>

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold text-white mb-4">Create New Workspace</h2>
            <input
              type="text"
              value={newWorkspaceName}
              onChange={(e) => setNewWorkspaceName(e.target.value)}
              placeholder="Workspace name"
              className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-lg text-white placeholder-zinc-600 focus:outline-none focus:border-cyan-500 transition-colors mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewWorkspaceName("");
                }}
                className="flex-1 py-2 border border-zinc-700 hover:border-zinc-600 text-zinc-300 font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWorkspace}
                disabled={isCreating || !newWorkspaceName.trim()}
                className="flex-1 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black font-medium rounded-lg transition-colors"
              >
                {isCreating ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
