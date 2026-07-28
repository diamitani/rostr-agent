import { useState, useEffect, createContext, useContext } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3001";

interface User {
  id: string;
  email: string;
  name?: string;
}

interface Workspace {
  id: string;
  name: string;
  status: string;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  selectWorkspace: (workspace: Workspace) => void;
  createWorkspace: (name: string) => Promise<void>;
  refreshWorkspaces: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("rostr_token"));
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const init = async () => {
      if (token) {
        try {
          const res = await fetch(`${API_URL}/api/me`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          
          if (res.ok) {
            const data = await res.json();
            setUser(data.user);
            setWorkspaces(data.workspaces);
            
            // Auto-select first workspace
            if (data.workspaces.length > 0 && !currentWorkspace) {
              setCurrentWorkspace(data.workspaces[0]);
            }
          } else {
            // Token invalid, clear it
            localStorage.removeItem("rostr_token");
            setToken(null);
          }
        } catch (error) {
          console.error("Auth check error:", error);
        }
      }
      setIsLoading(false);
    };
    
    init();
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "Login failed");
    }

    const data = await res.json();
    localStorage.setItem("rostr_token", data.token);
    setToken(data.token);
    setUser(data.user);
    setWorkspaces(data.workspaces);
    setCurrentWorkspace(data.workspaces[0] || null);
  };

  const register = async (email: string, password: string, name?: string) => {
    const res = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "Registration failed");
    }

    // After registration, log in
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem("rostr_token");
    setToken(null);
    setUser(null);
    setWorkspaces([]);
    setCurrentWorkspace(null);
  };

  const selectWorkspace = (workspace: Workspace) => {
    setCurrentWorkspace(workspace);
  };

  const createWorkspace = async (name: string) => {
    const res = await fetch(`${API_URL}/api/workspaces`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "Failed to create workspace");
    }

    // Refresh workspaces
    await refreshWorkspaces();
  };

  const refreshWorkspaces = async () => {
    const res = await fetch(`${API_URL}/api/workspaces`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.ok) {
      const data = await res.json();
      setWorkspaces(data.workspaces);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        workspaces,
        currentWorkspace,
        isLoading,
        login,
        register,
        logout,
        selectWorkspace,
        createWorkspace,
        refreshWorkspaces,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
