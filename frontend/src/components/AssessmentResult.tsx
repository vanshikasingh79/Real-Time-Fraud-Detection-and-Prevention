"use client";

import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  CheckCircle2,
  CircleHelp,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import type { FraudAssessmentResponse } from "@/lib/api";

type AssessmentResultProps = {
  assessment: FraudAssessmentResponse;
};

type RiskPresentation = {
  label: string;
  action: string;
  banner: string;
  icon: typeof CheckCircle2;
};

function getRiskPresentation(
  level: FraudAssessmentResponse["risk_level"],
): RiskPresentation {
  if (level === "HIGH") {
    return {
      label: "High risk",
      action: "Block application",
      banner: "border-red-200 bg-red-50 text-red-950",
      icon: AlertTriangle,
    };
  }
  if (level === "MEDIUM") {
    return {
      label: "Medium risk",
      action: "Step-up authentication",
      banner: "border-amber-200 bg-amber-50 text-amber-950",
      icon: AlertTriangle,
    };
  }
  return {
    label: "Low risk",
    action: "Approve application",
    banner: "border-emerald-200 bg-emerald-50 text-emerald-950",
    icon: CheckCircle2,
  };
}

function scoreBarColor(level: FraudAssessmentResponse["risk_level"]): string {
  if (level === "HIGH") return "from-red-500 to-rose-600";
  if (level === "MEDIUM") return "from-amber-400 to-orange-500";
  return "from-emerald-400 to-teal-500";
}

export default function AssessmentResult({ assessment }: AssessmentResultProps) {
  const risk = getRiskPresentation(assessment.risk_level);
  const RiskIcon = risk.icon;
  const scorePercent = Math.max(0, Math.min(1, assessment.risk_score)) * 100;

  return (
    <section aria-label="Fraud assessment result" className="w-full max-w-5xl space-y-5">
      <div className={`flex flex-col gap-5 rounded-2xl border p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between sm:p-6 ${risk.banner}`}>
        <div className="flex items-center gap-4">
          <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-white/75 shadow-sm">
            <RiskIcon className="size-6" />
          </span>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] opacity-65">Assessment decision</p>
            <h2 className="mt-1 text-2xl font-bold tracking-tight">{risk.label}</h2>
            <p className="mt-1 text-sm font-medium opacity-80">{risk.action}</p>
          </div>
        </div>
        <div className="rounded-xl bg-white/70 px-4 py-3 text-left sm:min-w-32 sm:text-right">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] opacity-65">Risk score</p>
          <p className="mt-1 text-3xl font-bold tabular-nums">{Math.round(scorePercent)}%</p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Signal intensity</p>
              <h3 className="mt-1 text-lg font-semibold text-slate-900">Fraud risk meter</h3>
            </div>
            <span className="text-sm font-semibold tabular-nums text-slate-700">{assessment.risk_score.toFixed(2)} / 1.00</span>
          </div>
          <div className="mt-7" aria-label={`Risk score ${assessment.risk_score.toFixed(2)} out of 1`} role="meter" aria-valuemin={0} aria-valuemax={1} aria-valuenow={assessment.risk_score}>
            <div className="h-4 overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200">
              <div className={`h-full rounded-full bg-linear-to-r transition-all ${scoreBarColor(assessment.risk_level)}`} style={{ width: `${scorePercent}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-[11px] font-medium text-slate-400"><span>0.0 · low</span><span>0.5 · review</span><span>1.0 · high</span></div>
          </div>
          <div className="mt-7 border-t border-slate-100 pt-4">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Observed risk factors</p>
            <ul className="mt-3 space-y-2">
              {assessment.top_risk_factors.map((factor) => <li key={factor} className="flex gap-2 text-sm leading-5 text-slate-700"><ArrowUpRight className="mt-0.5 size-4 shrink-0 text-slate-400" />{factor}</li>)}
            </ul>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center gap-2"><Sparkles className="size-5 text-blue-600" /><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Explainability</p><h3 className="mt-1 text-lg font-semibold text-slate-900">AI assessment rationale</h3></div></div>
          {assessment.explanation ? <div className="mt-5 space-y-5"><div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4"><p className="text-xs font-bold uppercase tracking-[0.14em] text-blue-700">Executive summary</p><p className="mt-2 text-sm leading-6 text-slate-700">{assessment.explanation.plain_english_summary}</p></div><ExplanationList title="Why this was flagged" items={assessment.explanation.risk_justification_points} /><ExplanationList title="Recommended next steps" items={assessment.explanation.recommended_next_steps} /></div> : <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm leading-6 text-slate-500">No AI explanation was requested for this assessment.</div>}
        </div>
      </div>

      <footer className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Compliance controls</p><p className="mt-1 text-xs text-slate-500">Application {assessment.application_id} · {new Date(assessment.evaluated_at).toLocaleString()}</p></div>
        <div className="flex flex-wrap gap-2"><StatusBadge label="PII Sanitized" enabled={assessment.pii_sanitized} /><StatusBadge label="AI Grounded (Verified)" enabled={assessment.explanation?.is_grounded === true} tooltip="Verified means each AI risk justification matched a factor identified by the fraud model." /></div>
      </footer>
    </section>
  );
}

function ExplanationList({ title, items }: { title: string; items: string[] }) {
  return <div><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">{title}</p><ul className="mt-2 space-y-2">{items.map((item) => <li key={item} className="flex gap-2 text-sm leading-5 text-slate-700"><span className="mt-1 flex size-4 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500"><Check className="size-3" /></span>{item}</li>)}</ul></div>;
}

function StatusBadge({ label, enabled, tooltip }: { label: string; enabled: boolean; tooltip?: string }) {
  return <span title={tooltip} className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ${enabled ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-slate-200 bg-white text-slate-500"}`}>{enabled ? <ShieldCheck className="size-3.5" /> : <CircleHelp className="size-3.5" />}{label}</span>;
}
