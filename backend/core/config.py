from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Pharma Complaint Management System"
    DEBUG: bool = True

    DATABASE_URL: str
    SECRET_KEY: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()