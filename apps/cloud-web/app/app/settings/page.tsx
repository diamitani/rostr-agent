"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);

  return (
    <div className="p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Settings</h1>
        <p className="text-slate-400 mb-8">Manage your account and preferences</p>

        {/* LLM Configuration */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">LLM Configuration</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Anthropic API Key
              </label>
              <div className="flex gap-2">
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-ant-..."
                  className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:border-cyan-500 focus:outline-none transition"
                />
                <button
                  onClick={() => setShowKey(!showKey)}
                  className="px-4 py-2 text-slate-400 hover:text-slate-200 transition"
                >
                  {showKey ? "Hide" : "Show"}
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Get your API key from{" "}
                <a
                  href="https://console.anthropic.com"
                  className="text-cyan-400 hover:text-cyan-300"
                >
                  console.anthropic.com
                </a>
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <select className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:border-cyan-500 focus:outline-none transition">
                <option>claude-3-5-sonnet-20241022 (Default)</option>
                <option>claude-3-opus-20250219</option>
                <option>claude-3-haiku-20250307</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Temperature
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                defaultValue="0.7"
                className="w-full"
              />
              <p className="text-xs text-slate-500 mt-1">
                Higher = more creative, Lower = more consistent
              </p>
            </div>

            <button className="w-full px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg font-semibold transition">
              Save
            </button>
          </div>
        </div>

        {/* Account */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Account</h2>

          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400">Email</label>
              <p className="text-white font-medium">user@example.com</p>
            </div>

            <div>
              <label className="text-sm text-slate-400">Subscription</label>
              <p className="text-white font-medium">Free Plan</p>
            </div>

            <button className="px-4 py-2 border border-red-500/30 text-red-400 hover:bg-red-500/10 rounded-lg transition">
              Change Password
            </button>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4 text-red-400">Danger Zone</h2>

          <button className="px-4 py-2 border border-red-500/30 text-red-400 hover:bg-red-500/10 rounded-lg transition">
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}
