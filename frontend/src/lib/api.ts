"use client";

export interface TelemetryData {
  typing_speed_wpm: number;
  paste_event_count: number;
  mouse_jitter_score: number;
  session_duration_seconds: number;
  ip_address: string;
  device_id: string;
  session_id?: string;
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
  similar_cases: Array<{
    application_id: string;
    risk_level: "LOW" | "MEDIUM" | "HIGH";
    risk_factors: string[];
    similarity_score: number;
  }> | null;
  pii_sanitized: boolean;
}

export interface FraudMetrics {
  total_evaluations: number;
  fraud_rate_pct: number;
  risk_distribution: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  repeat_offenders_blocked: number;
}

const configuredApiUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const normalizedApiUrl = configuredApiUrl.replace(/\/$/, "");
const API_BASE_URL = normalizedApiUrl.endsWith("/api/v1")
  ? normalizedApiUrl
  : `${normalizedApiUrl}/api/v1`;
const API_KEY =
  process.env.NEXT_PUBLIC_API_KEY || "fg-sk-dev-hackathon-key-2026";
const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

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
      headers,
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
        } else if (
          typeof errorBody === "object" &&
          errorBody !== null &&
          "detail" in errorBody &&
          Array.isArray(errorBody.detail)
        ) {
          const firstError = errorBody.detail[0];
          if (
            typeof firstError === "object" &&
            firstError !== null &&
            "msg" in firstError &&
            typeof firstError.msg === "string"
          ) {
            detail = `Request validation failed: ${firstError.msg}`;
          }
        }
      } catch {
        // Keep the friendly fallback when the server response is not JSON.
      }
      throw new Error(detail);
    }

    return (await response.json()) as FraudAssessmentResponse;
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to reach the fraud detection service. Check that the backend is running and try again.",
        );
      }
      if (error.message === "Invalid or missing API Key") {
        throw new Error(
          "The fraud detection service rejected the API key. Check NEXT_PUBLIC_API_KEY.",
        );
      }
      throw error;
    }
    throw new Error("Unable to evaluate the application. Please try again.");
  }
}

export async function fetchFraudMetrics(): Promise<FraudMetrics> {
  const response = await fetch(`${API_BASE_URL}/metrics`, { headers });
  if (!response.ok) {
    throw new Error("Unable to load fraud metrics.");
  }
  return (await response.json()) as FraudMetrics;
}
