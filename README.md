# Fraud Guard — Real-Time AI Fraud Detection API & Analyst Dashboard

Fraud Guard is a real-time fraud assessment platform for digital loan applications. It combines behavioral telemetry, financial ratios, an Isolation Forest anomaly detector, Responsible AI guardrails, and an analyst-facing Next.js dashboard.

## Core Stack

- FastAPI and Pydantic for the API contract and validation
- Scikit-learn Isolation Forest for unsupervised anomaly detection
- Joblib for model persistence
- Next.js 14, TypeScript, and Tailwind CSS for the analyst portal
- OpenAI and AWS Bedrock for optional AI explanations
- Deterministic mock provider for offline demos and safe local startup
- Docker Compose for one-command submission setup

## System Architecture

```text
+----------------------+
| Frontend Analyst     |
| Portal :3000         |
+----------+-----------+
           |
           v
+----------------------+       +-----------------------------+
| Transport Layer      | ----> | Domain Service              |
| FastAPI / Pydantic   |       | FraudEvaluationService     |
+----------------------+       +--------------+--------------+
                                               |
                                               v
                              +-------------------------------+
                              | Warm ML Model                 |
                              | Isolation Forest             |
                              | FastAPI lifespan caching     |
                              +---------------+---------------+
                                              |
                                              v
                              +-------------------------------+
                              | Guardrails                    |
                              | PII masking + grounding      |
                              | verification                 |
                              +---------------+---------------+
                                              |
                                              v
                              +-------------------------------+
                              | LLM Explainability Engine    |
                              | OpenAI / Bedrock / Mock      |
                              +-------------------------------+
                                              |
                                              v
                              +-------------------------------+
                              | Frontend Analyst Portal      |
                              | Decision, score, rationale,  |
                              | compliance badges            |
                              +-------------------------------+
```

## 30-Second Quickstart

```bash
git clone <repo_url> && cd fraud-detection
cp backend/.env.example backend/.env
docker-compose up --build
```

Open the dashboard at [http://localhost:3000](http://localhost:3000) and Swagger OpenAPI docs at [http://localhost:8000/docs](http://localhost:8000/docs).

The default configuration uses `LLM_PROVIDER=mock`, so the full demo runs without cloud credentials. Stop the stack with `docker-compose down`.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.ml.trainer
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The frontend uses `NEXT_PUBLIC_API_URL` when provided and falls back to `http://localhost:8000/api/v1` for local development.

### Tests and Smoke Test

```bash
cd backend
python -m pytest -q

cd ..
python scripts/smoke_test.py
```

The smoke test expects the API to be running and checks three preset decisions, response time, AI explanation structure, grounding, and PII sanitization. It exits `0` only when every assertion passes.

## Key Technical Features

### Zero-Hardcoding Principles

Decision thresholds and telemetry rules are defined through `pydantic-settings`, loaded from environment variables or `.env` defaults. This includes fraud thresholds, paste count, typing cadence, mouse jitter, and loan-to-income rules.

### High-Throughput Model Serving

The Isolation Forest artifact is loaded once during FastAPI lifespan startup and stored in `app.state.fraud_service`. Requests reuse the warm model instead of reloading the Joblib artifact. The local scoring path is designed for sub-5ms model inference; end-to-end latency also depends on explanation provider behavior.

### Responsible AI Guardrails

- IPv4 and IPv6 addresses are masked before an explanation prompt is built.
- Applicant identifiers are anonymized.
- Device fingerprints are reduced to masked suffixes.
- LLM responses are validated against a strict Pydantic JSON schema.
- `verify_grounding` cross-references explanation points with model-generated risk factors.
- Provider failures fall back to deterministic mock explanations rather than crashing the API.

## API Surface

- `GET /health` — service health check
- `POST /api/v1/fraud/evaluate` — evaluate a loan application
- `POST /api/v1/fraud/evaluate?include_explanation=false` — skip LLM explanation generation
- `GET /docs` — interactive Swagger documentation

## Judge Defense Talking Points

### Q: Why train on synthetic data instead of Kaggle fraud datasets?

**A:** Behavioral biometrics and telemetry data are proprietary and rare. Isolation Forests are unsupervised anomaly detectors designed to flag novel, unseen out-of-distribution patterns without relying on stale historical fraud labels.

### Q: How do you prevent LLM hallucinations in audit summaries?

**A:** All output justifications pass through an automated grounding check, `verify_grounding`, which cross-references LLM points against the raw ML risk factors before returning the explanation to the analyst. Unsupported claims are marked ungrounded, and provider failures use a deterministic fallback.

### Q: What happens without API credentials?

**A:** The default Compose configuration uses the mock provider. It produces deterministic structured explanations and allows judges to run the complete workflow offline.

## Configuration

Copy `backend/.env.example` to `backend/.env` and set provider-specific values as needed. Common options include:

```env
LLM_PROVIDER=mock
# LLM_PROVIDER=openai
# LLM_PROVIDER=bedrock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
AWS_REGION=us-east-1
ENABLE_PII_MASKING=True
```

Never commit real API keys or production credentials.
