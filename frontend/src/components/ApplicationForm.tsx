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
import {
  useTelemetry,
  type BrowserTelemetry,
} from "@/hooks/useTelemetry";

type Preset = {
  label: string;
  description: string;
  values: FormValues;
  telemetry: BrowserTelemetry;
};

type FormValues = {
  applicantId: string;
  loanAmount: number;
  annualIncome: number;
  isVpn: boolean;
};

const initialValues: FormValues = {
  applicantId: "APP-10294",
  loanAmount: 25000,
  annualIncome: 100000,
  isVpn: false,
};

const initialSimulationTelemetry: BrowserTelemetry = {
  typing_speed_wpm: 65,
  paste_event_count: 0,
  mouse_jitter_score: 0.8,
  session_duration_seconds: 45,
};

const presets: Preset[] = [
  {
    label: "Legitimate Applicant",
    description: "Natural session, no paste activity",
    values: initialValues,
    telemetry: initialSimulationTelemetry,
  },
  {
    label: "Bot / Automation Attack",
    description: "Extreme cadence, paste burst, VPN",
    values: {
      ...initialValues,
      isVpn: true,
    },
    telemetry: {
      typing_speed_wpm: 200,
      paste_event_count: 8,
      mouse_jitter_score: 0,
      session_duration_seconds: 10,
    },
  },
  {
    label: "Suspicious Behavioral Shift",
    description: "Slow typing with repeated pastes",
    values: {
      ...initialValues,
    },
    telemetry: {
      typing_speed_wpm: 10,
      paste_event_count: 4,
      mouse_jitter_score: 0.45,
      session_duration_seconds: 45,
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
  const { formRef, telemetry, getTelemetry } = useTelemetry<HTMLFormElement>();
  const [values, setValues] = useState<FormValues>(initialValues);
  const [telemetryMode, setTelemetryMode] = useState<"real" | "simulation">("real");
  const [simulationTelemetry, setSimulationTelemetry] = useState<BrowserTelemetry>(
    initialSimulationTelemetry,
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateValue<Key extends keyof FormValues>(key: Key, value: FormValues[Key]) {
    setValues((currentValues) => ({ ...currentValues, [key]: value }));
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const finalTelemetry = telemetryMode === "simulation"
      ? simulationTelemetry
      : getTelemetry();

    const payload: LoanApplicationRequest = {
      applicant_id: values.applicantId,
      loan_amount: values.loanAmount,
      annual_income: values.annualIncome,
      requested_term_months: 24,
      telemetry: {
        ...finalTelemetry,
        ip_address: "192.168.1.1",
        device_id: "DEV-DEMO-10294",
        session_id: crypto.randomUUID(),
        is_vpn: telemetryMode === "simulation" ? values.isVpn : false,
      },
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
        ref={formRef}
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
                <h2 className="text-lg font-semibold text-slate-900">Browser-collected signals</h2>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${telemetryMode === "simulation" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>
                {telemetryMode === "simulation" ? "Demo / simulation mode" : "Real telemetry mode"}
              </span>
            </div>
            <div className="grid gap-x-8 gap-y-6 sm:grid-cols-2">
              <TelemetryValue label="Typing speed" value={`${(telemetryMode === "simulation" ? simulationTelemetry.typing_speed_wpm : telemetry.typing_speed_wpm).toFixed(1)} WPM`} />
              <TelemetryValue label="Paste events" value={`${telemetryMode === "simulation" ? simulationTelemetry.paste_event_count : telemetry.paste_event_count} events`} />
              <TelemetryValue label="Mouse jitter score" value={(telemetryMode === "simulation" ? simulationTelemetry.mouse_jitter_score : telemetry.mouse_jitter_score).toFixed(2)} />
              <TelemetryValue label="Session duration" value={`${(telemetryMode === "simulation" ? simulationTelemetry.session_duration_seconds : telemetry.session_duration_seconds).toFixed(1)} sec`} />
            </div>
            {telemetryMode === "simulation" && <button type="button" onClick={() => setTelemetryMode("real")} className="mt-5 rounded-lg border border-amber-300 px-3 py-2 text-xs font-semibold text-amber-800 transition hover:bg-amber-50">Use live browser telemetry</button>}
          </div>

          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <div className="flex items-center gap-3">
              <span className={`flex size-9 items-center justify-center rounded-lg ${values.isVpn ? "bg-amber-100 text-amber-700" : "bg-white text-slate-500"}`}><Wifi className="size-4" /></span>
              <div><p className="text-sm font-semibold text-slate-800">VPN status (demo only)</p><p className="text-xs text-slate-500">Browser telemetry cannot reliably detect VPN usage</p></div>
            </div>
            <button type="button" role="switch" aria-checked={values.isVpn} aria-label="Toggle demo VPN status" disabled={telemetryMode !== "simulation"} onClick={() => updateValue("isVpn", !values.isVpn)} className={`relative h-7 w-12 rounded-full transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${values.isVpn ? "bg-amber-500" : "bg-slate-300"}`}><span className={`absolute top-1 size-5 rounded-full bg-white shadow-sm transition-transform ${values.isVpn ? "translate-x-6" : "translate-x-1"}`} /></button>
          </div>

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
            {presets.map((preset) => <button key={preset.label} type="button" onClick={() => { setValues(preset.values); setSimulationTelemetry(preset.telemetry); setTelemetryMode("simulation"); setError(null); }} className="group flex w-full items-center justify-between rounded-xl border border-slate-200 px-3 py-3 text-left transition hover:border-blue-300 hover:bg-blue-50"><span><span className="block text-sm font-semibold text-slate-800">{preset.label}</span><span className="mt-0.5 block text-xs text-slate-500">{preset.description}</span></span><ChevronRight className="size-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-blue-600" /></button>)}
          </div>
        </div>

        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm leading-6 text-slate-500"><CircleDot className="mb-3 size-5 text-blue-600" /><p className="font-semibold text-slate-700">Awaiting assessment</p><p className="mt-1">Submit the application to open its decision and grounded explanation.</p></div>
      </aside>
    </section>
  );
}

function TelemetryValue({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-3"><p className="text-xs font-bold uppercase tracking-widest text-slate-500">{label}</p><p className="mt-1 text-lg font-semibold text-slate-900">{value}</p></div>;
}
