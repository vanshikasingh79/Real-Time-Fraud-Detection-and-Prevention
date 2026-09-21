"""Application configuration settings.

This module centralizes runtime configuration for the fraud detection API and
loads values from environment variables and an optional .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables.

    Values are resolved in the following order: environment variables, values from
    the local .env file, and finally the defaults defined below.
    """

    APP_NAME: str = "Fraud Guard API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    FRAUD_THRESHOLD_HIGH: float = 0.80
    FRAUD_THRESHOLD_MEDIUM: float = 0.30
    MODEL_PATH: str = "app/ml/artifacts/saved_model.pkl"
    API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./fraud_audit.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    PASTE_COUNT_THRESHOLD: int = 3
    TYPING_WPM_HIGH: float = 150.0
    TYPING_WPM_LOW: float = 10.0
    MOUSE_JITTER_LOW: float = 0.05
    LOAN_TO_INCOME_RATIO_HIGH: float = 0.50
    EXTREME_FINANCIAL_DTI_RATIO: float = 10.0
    EXTREME_FINANCIAL_LOAN_AMOUNT: float = 20_000.0
    EXTREME_FINANCIAL_INCOME_LIMIT: float = 1_000.0
    EXTREME_FINANCIAL_ANOMALY_WEIGHT: float = 0.85
    REPEAT_OFFENDER_RISK_WEIGHT: float = 0.85
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AWS_REGION: str = "us-east-1"
    AWS_BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    ENABLE_PII_MASKING: bool = True
    MAX_EXPLANATION_TOKENS: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        """Return a SQLAlchemy URL suitable for asynchronous PostgreSQL access."""
        from urllib.parse import SplitResult, urlsplit, urlunsplit

        url = self.DATABASE_URL.strip()
        if not url.startswith("postgresql"):
            return url

        if "+asyncpg" not in url.split(":", 1)[0]:
            parts = urlsplit(url)
            url = urlunsplit(
                SplitResult(
                    "postgresql+asyncpg",
                    parts.netloc,
                    parts.path,
                    parts.query,
                    parts.fragment,
                )
            )

        if self.ENVIRONMENT.lower() != "production":
            parts = urlsplit(url)
            if parts.hostname == "localhost":
                credentials = ""
                if parts.username is not None:
                    credentials = parts.username
                    if parts.password is not None:
                        credentials += f":{parts.password}"
                    credentials += "@"
                host = f"{credentials}127.0.0.1"
                if parts.port is not None:
                    host += f":{parts.port}"
                url = urlunsplit(
                    SplitResult(
                        parts.scheme, host, parts.path, parts.query, parts.fragment
                    )
                )

        return url


settings = Settings()
"""Global application settings instance."""
