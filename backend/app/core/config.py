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
    FRAUD_THRESHOLD_HIGH: float = 0.70
    FRAUD_THRESHOLD_MEDIUM: float = 0.30
    MODEL_PATH: str = "app/ml/artifacts/saved_model.pkl"
    PASTE_COUNT_THRESHOLD: int = 3
    TYPING_WPM_HIGH: float = 150.0
    TYPING_WPM_LOW: float = 10.0
    MOUSE_JITTER_LOW: float = 0.05
    LOAN_TO_INCOME_RATIO_HIGH: float = 0.50
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
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


settings = Settings()
"""Global application settings instance."""
