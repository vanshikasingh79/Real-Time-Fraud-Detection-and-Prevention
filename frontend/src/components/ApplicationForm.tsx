"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import {
  ChevronRight,
  CircleDot,
  LoaderCircle,
  ShieldCheck,
  SlidersHorizontal,
  Wifi,
  Zap,
} from "lucide-react";

import {
  evaluateLoanApplication,
  type LoanApplicationRequest,
} from "@/lib/api";

type Preset = {
  label: string;
  description: string;
  values: FormValues;
};

type FormValues = {
  applicantId: string;
  loanAmount: number;
  annualIncome: number;
  typingSpeed: number;
  pasteCount: number;
  mouseJitter: number;
  sessionDuration: number;
  isVpn: boolean;
};

const initialValues: FormValues = {
  applicantId: "APP-10294",
  loanAmount: 25000,
  annualIncome: 100000,
  typingSpeed: 65,
  pasteCount: 0,
  mouseJitter: 0.8,
  sessionDuration: 45,
  isVpn: false,
};

const presets: Preset[] = [
  {
    label: "Legitimate Applicant",
    description: "Natural session, no paste activity",
    values: initialValues,
  },
  {
    label: "Bot / Automation Attack",
    description: "Extreme cadence, paste burst, VPN",
    values: {
      ...initialValues,
      typingSpeed: 200,
      pasteCount: 8,
      mouseJitter: 0,
      isVpn: true,
    },
  },
  {
    label: "Suspicious Behavioral Shift",
    description: "Slow typing with repeated pastes",
    values: {
      ...initialValues,
      typingSpeed: 10,
      pasteCount: 4,
      mouseJitter: 0.45,
    },
  },
];

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ApplicationForm() {
  const router = useRouter();
  const [values, setValues] = useState<FormValues>(initialValues);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [developerMode, setDeveloperMode] = useState(false);

  function updateValue<Key extends keyof FormValues>(key: Key, value: FormValues[Key]) {
    setValues((currentValues) => ({ ...currentValues, [key]: value }));
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const payload: LoanApplicationRequest = {
      applicant_id: values.applicantId,
      loan_amount: values.loanAmount,
      annual_income: values.annualIncome,
      requested_term_months: 24,
      telemetry: {
        typing_speed_wpm: values.typingSpeed,
        paste_event_count: values.pasteCount,
        mouse_jitter_score: values.mouseJitter,
        session_duration_seconds: values.sessionDuration,
        ip_address: "192.168.1.1",
        device_fingerprint_id: "DEV-DEMO-10294",
        is_vpn: values.isVpn,
      },
      is_developer_mode: developerMode,
    };

    try {
      const assessment = await evaluateLoanApplication(payload);
      sessionStorage.setItem("latestAssessment", JSON.stringify(assessment));
      router.push("/assessment");
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "The application could not be evaluated.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="grid w-full max-w-6xl gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <form
        onSubmit={handleSubmit}
        className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_24px_70px_-34px_rgba(15,23,42,0.35)]"
      >
        <div className="border-b border-slate-200 bg-[linear-gradient(120deg,#f8fafc,#eff6ff)] px-6 py-6 sm:px-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-blue-700">
                <ShieldCheck className="size-4" /> Intake console
              </p>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
                Loan application review
              </h1>
              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">
                Tune the behavioral signals, then run a live fraud assessment against the detection service.
              </p>
            </div>
            <div className="hidden rounded-xl border border-blue-100 bg-white/75 p-3 text-blue-700 sm:block">
              <SlidersHorizontal className="size-5" />
            </div>
          </div>
        </div>

        <div className="space-y-8 px-6 py-7 sm:px-8">
          <div className="grid gap-5 sm:grid-cols-3">
            <label className="sm:col-span-1">
              <span className="mb-2 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Applicant ID</span>
              <input
                className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                value={values.applicantId}
                onChange={(event) => updateValue("applicantId", event.target.value)}
                required
              />
            </label>
            <label>
              <span className="mb-2 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Loan amount</span>
              <div className="relative"><span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">$</span><input className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 pl-7 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100" type="number" min="1" step="any" value={values.loanAmount} onChange={(event) => updateValue("loanAmount", Number(event.target.value))} required /></div>
            </label>
            <label>
              <span className="mb-2 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Annual income</span>
              <div className="relative"><span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">$</span><input className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 pl-7 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100" type="number" min="1" step="any" value={values.annualIncome} onChange={(event) => updateValue("annualIncome", Number(event.target.value))} required /></div>
            </label>
          </div>

          <div>
            <div className="mb-4 flex items-end justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Behavioral telemetry</p>
                <h2 className="text-lg font-semibold text-slate-900">Simulate session signals</h2>
              </div>
              <span className="hidden text-xs text-slate-400 sm:block">Drag to adjust</span>
            </div>
            <div className="grid gap-x-8 gap-y-6 sm:grid-cols-2">
              <SliderField label="Typing speed" value={values.typingSpeed} min={5} max={200} step={1} display={`${values.typingSpeed} WPM`} onChange={(value) => updateValue("typingSpeed", value)} />
              <SliderField label="Paste events" value={values.pasteCount} min={0} max={10} step={1} display={`${values.pasteCount} events`} onChange={(value) => updateValue("pasteCount", value)} />
              <SliderField label="Mouse jitter score" value={values.mouseJitter} min={0} max={1} step={0.01} display={values.mouseJitter.toFixed(2)} onChange={(value) => updateValue("mouseJitter", value)} />
              <SliderField label="Session duration" value={values.sessionDuration} min={5} max={120} step={1} display={`${values.sessionDuration} sec`} onChange={(value) => updateValue("sessionDuration", value)} />
            </div>
          </div>

          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-3">
              <span className={`flex size-9 items-center justify-center rounded-lg ${values.isVpn ? "bg-amber-100 text-amber-700" : "bg-white text-slate-500"}`}><Wifi className="size-4" /></span>
              <div><p className="text-sm font-semibold text-slate-800">VPN connection</p><p className="text-xs text-slate-500">Anonymized network detected</p></div>
            </div>
            <button type="button" role="switch" aria-checked={values.isVpn} aria-label="Toggle VPN connection" onClick={() => updateValue("isVpn", !values.isVpn)} className={`relative h-7 w-12 rounded-full transition-colors ${values.isVpn ? "bg-amber-500" : "bg-slate-300"}`}><span className={`absolute top-1 size-5 rounded-full bg-white shadow-sm transition-transform ${values.isVpn ? "translate-x-6" : "translate-x-1"}`} /></button>
          </div>

          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-dashed border-amber-300 bg-amber-50 px-4 py-3">
            <input
              type="checkbox"
              checked={developerMode}
              onChange={(event) => setDeveloperMode(event.target.checked)}
              className="mt-1 size-4 accent-amber-600"
            />
            <span>
              <span className="block text-sm font-semibold text-amber-900">Developer test mode</span>
              <span className="mt-1 block text-xs leading-5 text-amber-800">Disables repeat-offender escalation for local testing. Behavioral signals are still scored.</span>
            </span>
          </label>

          <div className="flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <div><p className="text-xs text-slate-500">Current request</p><p className="font-semibold text-slate-800">{formatCurrency(values.loanAmount)} requested</p></div>
            <button type="submit" disabled={isSubmitting} className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : <Zap className="size-4" />}{isSubmitting ? "Evaluating..." : "Evaluate application"}<ChevronRight className="size-4" /></button>
          </div>
          {error && <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
        </div>
      </form>

      <aside className="space-y-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_24px_70px_-34px_rgba(15,23,42,0.25)]">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Demo scenarios</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Load a signal profile</h2>
          <div className="mt-4 space-y-2">
            {presets.map((preset) => <button key={preset.label} type="button" onClick={() => { setValues(preset.values); setError(null); }} className="group flex w-full items-center justify-between rounded-xl border border-slate-200 px-3 py-3 text-left transition hover:border-blue-300 hover:bg-blue-50"><span><span className="block text-sm font-semibold text-slate-800">{preset.label}</span><span className="mt-0.5 block text-xs text-slate-500">{preset.description}</span></span><ChevronRight className="size-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-blue-600" /></button>)}
          </div>
        </div>

        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm leading-6 text-slate-500"><CircleDot className="mb-3 size-5 text-blue-600" /><p className="font-semibold text-slate-700">Awaiting assessment</p><p className="mt-1">Submit the application to open its decision and grounded explanation.</p></div>
      </aside>
    </section>
  );
}

function SliderField({ label, value, min, max, step, display, onChange }: { label: string; value: number; min: number; max: number; step: number; display: string; onChange: (value: number) => void }) {
  return <label className="block"><span className="mb-2 flex items-center justify-between text-sm font-medium text-slate-700"><span>{label}</span><strong className="rounded-md bg-blue-50 px-2 py-1 text-xs text-blue-700">{display}</strong></span><input className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-blue-600" type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} /></label>;
}
