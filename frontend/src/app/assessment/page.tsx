"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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
      <AssessmentResult assessment={assessment} />
    </main>
  );
}