"use client";

import { useState } from "react";

interface Integration {
  name: string;
  description: string;
  icon: string;
  connected: boolean;
  fields?: { label: string; placeholder: string }[];
}

const integrations: Integration[] = [
  {
    name: "Telegram",
    description: "Connect your Telegram bot for messaging automation",
    icon: "📱",
    connected: false,
    fields: [{ label: "Bot Token", placeholder: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" }],
  },
  {
    name: "WhatsApp",
    description: "Send and receive messages via WhatsApp Business API",
    icon: "💬",
    connected: false,
    fields: [
      { label: "Phone Number", placeholder: "+1234567890" },
      { label: "API Key", placeholder: "whatsapp_api_key" },
    ],
  },
  {
    name: "iMessage",
    description: "Integrate with Apple iMessage for notifications",
    icon: "💌",
    connected: false,
    fields: [{ label: "Apple ID", placeholder: "you@icloud.com" }],
  },
  {
    name: "Signal",
    description: "Encrypted messaging via Signal Protocol",
    icon: "🔐",
    connected: false,
    fields: [{ label: "Signal Account", placeholder: "+1234567890" }],
  },
  {
    name: "Slack",
    description: "Post messages and commands to Slack channels",
    icon: "🎯",
    connected: false,
    fields: [{ label: "Webhook URL", placeholder: "https://hooks.slack.com/services/..." }],
  },
  {
    name: "Email",
    description: "Send and receive emails with IMAP/SMTP",
    icon: "📧",
    connected: false,
    fields: [
      { label: "Email", placeholder: "you@example.com" },
      { label: "App Password", placeholder: "••••••••••••••••" },
    ],
  },
];

export default function IntegrationsPage() {
  const [items, setItems] = useState(integrations);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleIntegration = (name: string) => {
    if (expandedId === name) {
      setExpandedId(null);
    } else {
      setExpandedId(name);
    }
  };

  const connectIntegration = (name: string) => {
    setItems(
      items.map((item) =>
        item.name === name ? { ...item, connected: !item.connected } : item
      )
    );
  };

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Integrations</h1>
        <p className="text-slate-400 mb-8">
          Connect ROSTR with messaging and communication platforms via Composio
        </p>

        {/* Integration Grid */}
        <div className="space-y-3">
          {items.map((integration) => (
            <div
              key={integration.name}
              className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden hover:border-slate-600 transition"
            >
              <div
                className="p-6 cursor-pointer flex items-center justify-between group"
                onClick={() => toggleIntegration(integration.name)}
              >
                <div className="flex items-center gap-4">
                  <div className="text-4xl">{integration.icon}</div>
                  <div>
                    <h3 className="font-semibold text-lg group-hover:text-cyan-400 transition">
                      {integration.name}
                    </h3>
                    <p className="text-slate-400 text-sm">
                      {integration.description}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      connectIntegration(integration.name);
                    }}
                    className={`px-4 py-2 rounded-lg font-semibold transition ${
                      integration.connected
                        ? "bg-green-500/20 text-green-400"
                        : "bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30"
                    }`}
                  >
                    {integration.connected ? "✓ Connected" : "Connect"}
                  </button>
                  <span
                    className="text-slate-400 group-hover:text-slate-300 transition"
                  >
                    {expandedId === integration.name ? "▼" : "▶"}
                  </span>
                </div>
              </div>

              {/* Expanded form */}
              {expandedId === integration.name && integration.fields && (
                <div className="border-t border-slate-700 bg-slate-900/30 p-6 space-y-4">
                  {integration.fields.map((field, i) => (
                    <div key={i}>
                      <label className="block text-sm font-medium mb-2">
                        {field.label}
                      </label>
                      <input
                        type="text"
                        placeholder={field.placeholder}
                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:border-cyan-500 focus:outline-none transition text-white"
                      />
                    </div>
                  ))}
                  <button className="w-full px-4 py-2 bg-cyan-500 hover:bg-cyan-600 rounded-lg font-semibold transition">
                    Save
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Documentation */}
        <div className="mt-12 bg-slate-800/50 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Need help?</h2>
          <p className="text-slate-400 mb-4">
            Integrations are powered by{" "}
            <a
              href="https://composio.dev"
              className="text-cyan-400 hover:text-cyan-300"
            >
              Composio
            </a>
            , providing secure OAuth connections to 50+ services.
          </p>
          <p className="text-slate-400 text-sm">
            All credentials are encrypted at rest and never stored in plain text.
          </p>
        </div>
      </div>
    </div>
  );
}
