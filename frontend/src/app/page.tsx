import { Activity, LockKeyhole, ShieldCheck } from "lucide-react";

import ApplicationForm from "@/components/ApplicationForm";
import MetricsDashboard from "@/components/MetricsDashboard";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#eef3f7] text-slate-900">
      <header className="border-b border-slate-200 bg-[#102332] text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-xl bg-cyan-400 text-[#102332]"><ShieldCheck className="size-5" /></span>
            <div><p className="text-sm font-bold tracking-wide">FRAUD GUARD</p><p className="text-xs text-slate-300">Real-time underwriting intelligence</p></div>
          </div>
          <div className="hidden items-center gap-5 text-xs text-slate-300 sm:flex"><span className="flex items-center gap-2"><Activity className="size-4 text-emerald-400" /> Detection engine online</span><span className="flex items-center gap-2"><LockKeyhole className="size-4 text-cyan-300" /> Guardrails active</span></div>
        </div>
      </header>
      <main className="mx-auto flex max-w-7xl flex-col gap-10 px-5 py-8 sm:px-8 lg:py-12">
        <div className="max-w-3xl"><p className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-700">Analyst workspace</p><h1 className="mt-3 text-4xl font-semibold tracking-tight text-[#102332] sm:text-5xl">Assess every application with signal, context, and control.</h1><p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">Explore behavioral telemetry, run a fraud decision, and review an AI explanation grounded in the model&apos;s observed factors.</p></div>
        <MetricsDashboard />
        <ApplicationForm />
      </main>
    </div>
  );
}
