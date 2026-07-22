"use client";

import { useState, useEffect, useCallback } from "react";

interface IntegrationApp {
  name: string;
  key: string;
  appId: string;
  description: string;
  logo: string;
  categories: string[];
  connected: boolean;
}

interface IntegrationsResponse {
  integrations: IntegrationApp[];
  totalApps: number;
  connectedCount: number;
}

// Default entity ID — in production, derive from authenticated user session
const ENTITY_ID = "rostr-default-user";

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<IntegrationApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "connected" | "available">("all");
  const [connecting, setConnecting] = useState<string | null>(null);

  const fetchIntegrations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `/api/integrations/list?entity_id=${encodeURIComponent(ENTITY_ID)}`
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      const data: IntegrationsResponse = await response.json();
      setIntegrations(data.integrations);
    } catch (err: any) {
      setError(err.message || "Failed to load integrations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  const handleConnect = async (app: IntegrationApp) => {
    if (app.connected) return;

    setConnecting(app.key);
    try {
      const response = await fetch("/api/integrations/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          entity_id: ENTITY_ID,
          app_name: app.key,
          redirect_url: window.location.href,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.redirectUrl) {
        // OAuth flow — redirect user to authorize
        window.location.href = data.redirectUrl;
      } else {
        // Non-OAuth connection (API key based) — refresh list
        await fetchIntegrations();
      }
    } catch (err: any) {
      setError(`Failed to connect ${app.name}: ${err.message}`);
    } finally {
      setConnecting(null);
    }
  };

  // Filter and search
  const filteredIntegrations = integrations.filter((app) => {
    const matchesSearch =
      !searchQuery ||
      app.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      app.categories.some((c) =>
        c.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesFilter =
      filter === "all" ||
      (filter === "connected" && app.connected) ||
      (filter === "available" && !app.connected);

    return matchesSearch && matchesFilter;
  });

  const connectedCount = integrations.filter((i) => i.connected).length;

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Integrations</h1>
        <p className="text-slate-400 mb-8">
          Connect ROSTR with 100+ services via Composio — OAuth, API keys, and
          more handled automatically.
        </p>

        {/* Stats Bar */}
        <div className="flex items-center gap-6 mb-6">
          <div className="text-sm text-slate-400">
            <span className="text-white font-semibold">{integrations.length}</span>{" "}
            apps available
          </div>
          <div className="text-sm text-slate-400">
            <span className="text-green-400 font-semibold">{connectedCount}</span>{" "}
            connected
          </div>
        </div>

        {/* Search and Filter */}
        <div className="flex gap-4 mb-6">
          <input
            type="text"
            placeholder="Search integrations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:border-cyan-500 focus:outline-none transition text-white placeholder-slate-500"
          />
          <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
            {(["all", "connected", "available"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                  filter === f
                    ? "bg-cyan-500/20 text-cyan-400"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            <p className="font-medium">Error</p>
            <p className="text-sm mt-1">{error}</p>
            <button
              onClick={() => {
                setError(null);
                fetchIntegrations();
              }}
              className="mt-2 text-sm text-red-300 underline hover:text-red-200"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="space-y-3">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 animate-pulse"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-slate-700 rounded-lg" />
                  <div className="flex-1">
                    <div className="h-5 bg-slate-700 rounded w-32 mb-2" />
                    <div className="h-4 bg-slate-700/50 rounded w-64" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Integration Grid */}
        {!loading && (
          <div className="space-y-3">
            {filteredIntegrations.length === 0 && (
              <div className="text-center py-12 text-slate-400">
                {searchQuery
                  ? `No integrations matching "${searchQuery}"`
                  : "No integrations found"}
              </div>
            )}

            {filteredIntegrations.map((app) => (
              <div
                key={app.key || app.name}
                className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden hover:border-slate-600 transition"
              >
                <div className="p-6 flex items-center justify-between group">
                  <div className="flex items-center gap-4">
                    {app.logo ? (
                      <img
                        src={app.logo}
                        alt={app.name}
                        className="w-12 h-12 rounded-lg object-contain bg-white/5 p-1"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-slate-700 flex items-center justify-center text-lg font-bold text-slate-400">
                        {app.name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold text-lg group-hover:text-cyan-400 transition">
                        {app.name}
                      </h3>
                      <p className="text-slate-400 text-sm line-clamp-1">
                        {app.description || "Connect and automate with " + app.name}
                      </p>
                      {app.categories.length > 0 && (
                        <div className="flex gap-1.5 mt-1">
                          {app.categories.slice(0, 3).map((cat) => (
                            <span
                              key={cat}
                              className="text-xs px-2 py-0.5 bg-slate-700/50 text-slate-400 rounded"
                            >
                              {cat}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => handleConnect(app)}
                    disabled={app.connected || connecting === app.key}
                    className={`px-5 py-2 rounded-lg font-semibold text-sm transition whitespace-nowrap ${
                      app.connected
                        ? "bg-green-500/20 text-green-400 cursor-default"
                        : connecting === app.key
                          ? "bg-slate-700 text-slate-400 cursor-wait"
                          : "bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 cursor-pointer"
                    }`}
                  >
                    {app.connected
                      ? "Connected"
                      : connecting === app.key
                        ? "Connecting..."
                        : "Connect"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Documentation */}
        <div className="mt-12 bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">About Integrations</h2>
          <p className="text-slate-400 mb-4">
            Integrations are powered by{" "}
            <a
              href="https://composio.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300"
            >
              Composio
            </a>
            , providing secure OAuth connections to 100+ services including Slack,
            Gmail, HubSpot, GitHub, Salesforce, and more.
          </p>
          <p className="text-slate-400 text-sm">
            All credentials are encrypted at rest and managed securely. ROSTR never
            stores raw OAuth tokens — Composio handles the full authentication
            lifecycle.
          </p>
        </div>
      </div>
    </div>
  );
}
