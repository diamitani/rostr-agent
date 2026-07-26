"use client";

import { useEffect, useState } from "react";

interface BillingStatus {
  plan: string;
  status: string;
  executionsToday: number;
  dailyLimit: number;
  monthlyUsage: number;
  monthlySpend: number;
  nextBillingDate: string;
}

export default function BillingPage() {
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBillingStatus();
    const interval = setInterval(fetchBillingStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchBillingStatus = async () => {
    try {
      const response = await fetch("/api/billing/status");
      if (response.ok) {
        const data = await response.json();
        setBilling(data);
      }
    } catch (error) {
      console.error("Failed to fetch billing status:", error);
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      name: "Free",
      price: "0",
      features: ["10 executions/day", "Basic chat", "1 workspace"],
      current: billing?.plan === "free",
    },
    {
      name: "Pro",
      price: "20",
      features: ["Unlimited executions", "Priority support", "10 workspaces"],
      current: billing?.plan === "pro",
    },
    {
      name: "Enterprise",
      price: "Custom",
      features: ["Custom limits", "Dedicated support", "Unlimited everything"],
      current: billing?.plan === "enterprise",
    },
  ];

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">Billing & Usage</h1>
        <p className="text-slate-400 mb-8">
          Monitor your subscription and track usage metrics
        </p>

        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : (
          <>
            {/* Current Usage */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">Current Plan</div>
                <div className="text-3xl font-bold capitalize">
                  {billing?.plan || "Free"}
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">
                  Today's Executions
                </div>
                <div className="text-3xl font-bold">
                  {billing?.executionsToday || 0} /{" "}
                  <span className="text-lg">{billing?.dailyLimit || 10}</span>
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">
                  Monthly Executions
                </div>
                <div className="text-3xl font-bold">
                  {billing?.monthlyUsage || 0}
                </div>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
                <div className="text-sm text-slate-400 mb-1">This Month</div>
                <div className="text-3xl font-bold">
                  ${billing?.monthlySpend || "0.00"}
                </div>
              </div>
            </div>

            {/* Usage Breakdown */}
            <div className="mb-12">
              <h2 className="text-2xl font-bold mb-4">Usage Breakdown</h2>
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span>Daily Limit</span>
                    <span>
                      {billing?.executionsToday || 0} /{" "}
                      {billing?.dailyLimit || 10}
                    </span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2">
                    <div
                      className="bg-cyan-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          ((billing?.executionsToday || 0) /
                            (billing?.dailyLimit || 10)) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Plans */}
            <div>
              <h2 className="text-2xl font-bold mb-4">Plans</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {plans.map((plan) => (
                  <div
                    key={plan.name}
                    className={`rounded-lg p-6 transition ${
                      plan.current
                        ? "border-2 border-cyan-500 bg-cyan-500/5"
                        : "border border-slate-700 bg-slate-800/50 hover:border-slate-600"
                    }`}
                  >
                    <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                    <div className="text-3xl font-bold mb-4">
                      ${plan.price}
                      {plan.price !== "Custom" && (
                        <span className="text-lg text-slate-400">/month</span>
                      )}
                    </div>
                    <ul className="space-y-2 mb-6">
                      {plan.features.map((feature, i) => (
                        <li
                          key={i}
                          className="text-sm text-slate-300 flex items-center gap-2"
                        >
                          <span className="text-cyan-400">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <button
                      disabled={plan.current}
                      className={`w-full px-4 py-2 rounded-lg font-semibold transition ${
                        plan.current
                          ? "bg-cyan-500 text-white cursor-default"
                          : "bg-slate-700 hover:bg-slate-600"
                      }`}
                    >
                      {plan.current ? "Current Plan" : "Switch"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
