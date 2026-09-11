from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Attendance Management System"
    APP_ENV: str = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "attendance_db"

    JWT_SECRET_KEY: str = "change-this-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    EXPORT_DIRECTORY: str = "exports"

    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_TIMEOUT_SECONDS: float = 45.0

    # Optional OpenAI-compatible endpoint (remote/cloud LLM). When the app is
    # deployed on Render, local Ollama is unreachable — point these at a
    # remotely reachable endpoint (e.g. a hosted Ollama proxy) and set
    # LLM_PROVIDER=openai_compatible.
    OPENAI_COMPATIBLE_BASE_URL: str = ""
    OPENAI_COMPATIBLE_MODEL: str = ""
    OPENAI_COMPATIBLE_API_KEY: str = ""

    DEMO_MODE: bool = False
    DEMO_TEACHER_EMAIL: str = "demo@attendvortex.local"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = []
        for origin in self.CORS_ORIGINS.split(","):
            cleaned = origin.strip().rstrip("/")
            if cleaned and cleaned not in origins:
                origins.append(cleaned)
        return origins if origins else ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
