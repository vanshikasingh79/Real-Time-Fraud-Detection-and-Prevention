"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, RotateCcw } from "lucide-react";

import AssessmentResult from "@/components/AssessmentResult";
import type { FraudAssessmentResponse } from "@/lib/api";

export default function AssessmentPage() {
  const router = useRouter();
  const [assessment, setAssessment] = useState<FraudAssessmentResponse | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("latestAssessment");
    if (!stored) return;

    try {
      const parsedAssessment = JSON.parse(stored) as FraudAssessmentResponse;
      const frame = window.requestAnimationFrame(() => {
        setAssessment(parsedAssessment);
      });
      return () => window.cancelAnimationFrame(frame);
    } catch {
      sessionStorage.removeItem("latestAssessment");
    }
  }, []);

  if (!assessment) {
    return (
      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        <p className="text-slate-500">
          No assessment found. <button type="button" onClick={() => router.push("/")} className="text-blue-600 underline">Go back</button>
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <button type="button" onClick={() => router.push("/")} className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-400 hover:text-blue-700">
          <ArrowLeft className="size-4" /> Back to workspace
        </button>
        <button type="button" onClick={() => { sessionStorage.removeItem("latestAssessment"); router.push("/"); }} className="inline-flex items-center gap-2 rounded-lg bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700">
          <RotateCcw className="size-4" /> New assessment
        </button>
      </div>
      <AssessmentResult assessment={assessment} />
    </main>
  );
}