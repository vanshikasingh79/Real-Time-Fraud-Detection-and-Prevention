"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  CheckCircle2,
  CircleHelp,
  ClipboardCheck,
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
  const [analystNote, setAnalystNote] = useState("");
  const [loggedDecision, setLoggedDecision] = useState<{
    status: "APPROVED" | "REJECTED" | "FALSE_POSITIVE";
    timestamp: string;
    note: string;
  } | null>(null);
  const risk = getRiskPresentation(assessment.risk_level);
  const RiskIcon = risk.icon;
  const scorePercent = Math.max(0, Math.min(1, assessment.risk_score)) * 100;

  function logDecision(status: "APPROVED" | "REJECTED" | "FALSE_POSITIVE") {
    const override = {
      application_id: assessment.application_id,
      status,
      timestamp: new Date().toISOString(),
      note: analystNote.trim(),
    };
    try {
      const stored = JSON.parse(localStorage.getItem("fg_analyst_overrides") ?? "[]");
      localStorage.setItem(
        "fg_analyst_overrides",
        JSON.stringify(Array.isArray(stored) ? [...stored, override] : [override]),
      );
    } catch {
      localStorage.setItem("fg_analyst_overrides", JSON.stringify([override]));
    }
    setLoggedDecision(override);
  }

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

      {assessment.similar_cases && assessment.similar_cases.length > 0 && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6" aria-labelledby="similar-cases-heading">
          <div className="flex items-center gap-2">
            <ClipboardCheck className="size-5 text-blue-600" />
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Historical context</p>
              <h3 id="similar-cases-heading" className="mt-1 text-lg font-semibold text-slate-900">Similar Historical Cases</h3>
            </div>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {assessment.similar_cases.map((similarCase) => (
              <div key={similarCase.application_id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="truncate text-sm font-semibold text-slate-900">{similarCase.application_id}</p>
                <p className="mt-2 text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Similarity</p>
                <p className="mt-1 text-2xl font-bold tabular-nums text-slate-800">{Math.round(similarCase.similarity_score * 100)}%</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Human-in-the-Loop (HITL) MLOps Feedback Loop */}
      <section className="rounded-2xl border border-slate-700 bg-slate-900 p-5 text-slate-100 shadow-sm sm:p-6" aria-labelledby="analyst-decision-heading">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-400">Analyst review</p>
            <h3 id="analyst-decision-heading" className="mt-1 text-lg font-semibold">Analyst Decision &amp; Human-in-the-Loop Override</h3>
          </div>
          <ClipboardCheck className="size-5 shrink-0 text-slate-400" />
        </div>
        <label className="mt-5 block text-sm font-medium text-slate-300" htmlFor="analyst-notes">Analyst Notes / Justification</label>
        <textarea id="analyst-notes" value={analystNote} onChange={(event) => setAnalystNote(event.target.value)} rows={3} className="mt-2 w-full rounded-xl border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30" placeholder="Add context for this decision (optional)" />
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="button" onClick={() => logDecision("APPROVED")} className="rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-400">Approve Application</button>
          <button type="button" onClick={() => logDecision("REJECTED")} className="rounded-lg bg-red-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-red-400">Reject Application</button>
          <button type="button" onClick={() => logDecision("FALSE_POSITIVE")} className="rounded-lg bg-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-amber-300">Mark False Positive</button>
        </div>
        {loggedDecision && (
          <div className="mt-5 rounded-xl border border-emerald-400/40 bg-emerald-400/10 p-4 text-sm" role="status">
            <p className="font-bold text-emerald-300">Decision Logged</p>
            <p className="mt-2 text-slate-300">Status: <span className="font-semibold text-white">{loggedDecision.status}</span></p>
            <p className="mt-1 text-slate-300">Timestamp: <span className="font-mono text-xs text-white">{loggedDecision.timestamp}</span></p>
            <p className="mt-1 text-slate-300">Recorded Analyst Note: <span className="text-white">{loggedDecision.note || "None"}</span></p>
          </div>
        )}
      </section>

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
