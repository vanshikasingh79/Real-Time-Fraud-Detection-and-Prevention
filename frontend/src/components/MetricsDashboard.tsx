"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Ban, ChartNoAxesCombined } from "lucide-react";

import { fetchFraudMetrics, type FraudMetrics } from "@/lib/api";

const metricCards = [
  { key: "total_evaluations", label: "Total evaluations", icon: Activity },
  { key: "fraud_rate_pct", label: "High-risk rate", icon: AlertTriangle },
  { key: "repeat_offenders_blocked", label: "Repeat offenders blocked", icon: Ban },
] as const;

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState<FraudMetrics | null>(null);
  const [localRepeatBlocked, setLocalRepeatBlocked] = useState(() => {
    if (typeof window === "undefined") return 0;
    const storedCount = Number.parseInt(localStorage.getItem("fg_repeat_blocked") ?? "0", 10);
    return Number.isNaN(storedCount) ? 0 : storedCount;
  });

  useEffect(() => {
    function handleRepeatBlocked() {
      const nextCount = Number.parseInt(localStorage.getItem("fg_repeat_blocked") ?? "0", 10) + 1;
      localStorage.setItem("fg_repeat_blocked", String(nextCount));
      setLocalRepeatBlocked(nextCount);
    }

    window.addEventListener("fg-repeat-blocked", handleRepeatBlocked);
    fetchFraudMetrics().then(setMetrics).catch(() => setMetrics(null));
    return () => window.removeEventListener("fg-repeat-blocked", handleRepeatBlocked);
  }, []);

  const repeatOffendersBlocked = metrics?.repeat_offenders_blocked || localRepeatBlocked;

  return (
    <section aria-label="Fraud metrics" className="w-full max-w-6xl">
      <div className="mb-4 flex items-center gap-2">
        <ChartNoAxesCombined className="size-4 text-cyan-700" />
        <h2 className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-700">
          Operations snapshot
        </h2>
      </div>
      <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {metricCards.map(({ key, label, icon: Icon }) => (
          <div key={key} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_18px_50px_-34px_rgba(15,23,42,0.35)]">
            <Icon className="size-5 text-blue-600" />
            <p className="mt-5 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              {metrics
                ? key === "fraud_rate_pct"
                  ? `${metrics[key].toFixed(1)}%`
                  : key === "repeat_offenders_blocked"
                    ? repeatOffendersBlocked.toLocaleString()
                    : metrics[key].toLocaleString()
                : key === "repeat_offenders_blocked"
                  ? repeatOffendersBlocked.toLocaleString()
                  : "--"}
            </p>
          </div>
        ))}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_18px_50px_-34px_rgba(15,23,42,0.35)]">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Risk distribution</p>
          <div className="mt-4 space-y-2 text-sm">
            {(["HIGH", "MEDIUM", "LOW"] as const).map((level) => (
              <div key={level} className="flex items-center justify-between">
                <span className="font-medium text-slate-600">{level}</span>
                <span className="font-semibold text-slate-950">{metrics?.risk_distribution[level] ?? "--"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}