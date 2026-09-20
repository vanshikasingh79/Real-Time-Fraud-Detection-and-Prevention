"use client";

export interface TelemetryData {
  typing_speed_wpm: number;
  paste_event_count: number;
  mouse_jitter_score: number;
  session_duration_seconds: number;
  ip_address: string;
  device_fingerprint_id: string;
  is_vpn: boolean;
}

export interface LoanApplicationRequest {
  applicant_id: string;
  loan_amount: number;
  annual_income: number;
  requested_term_months: number;
  telemetry: TelemetryData;
}

export interface AIExplanation {
  plain_english_summary: string;
  risk_justification_points: string[];
  recommended_next_steps: string[];
  confidence_score: number;
  is_grounded: boolean;
}

export interface FraudAssessmentResponse {
  application_id: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  recommended_action: "APPROVE" | "STEP_UP_AUTHENTICATION" | "BLOCK";
  top_risk_factors: string[];
  evaluated_at: string;
  explanation: AIExplanation | null;
  pii_sanitized: boolean;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Evaluate a loan application through the fraud detection backend.
 *
 * @throws {Error} With a user-friendly message when the backend is unavailable
 * or returns an unsuccessful response.
 */
export async function evaluateLoanApplication(
  payload: LoanApplicationRequest,
  includeExplanation: boolean = true,
): Promise<FraudAssessmentResponse> {
  const endpoint = `${API_BASE_URL}/fraud/evaluate?include_explanation=${includeExplanation}`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let detail = "The application could not be evaluated.";
      try {
        const errorBody: unknown = await response.json();
        if (
          typeof errorBody === "object" &&
          errorBody !== null &&
          "detail" in errorBody &&
          typeof errorBody.detail === "string"
        ) {
          detail = errorBody.detail;
        }
      } catch {
        // Keep the friendly fallback when the server response is not JSON.
      }
      throw new Error(detail);
    }

    return (await response.json()) as FraudAssessmentResponse;
  } catch (error) {
    if (error instanceof Error && error.message !== "Failed to fetch") {
      throw error;
    }
    throw new Error(
      "Unable to connect to the fraud detection service. Please try again.",
    );
  }
}
