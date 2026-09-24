from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    backend_host: str = "127.0.0.1"
    backend_port: int = 8001
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000"

    foundry_project_endpoint: str
    foundry_api_key: str
    foundry_api_version: str = "2024-10-21"
    foundry_chat_deployment: str = "gpt-4.1-mini"
    foundry_embedding_deployment: str = "text-embedding-3-small"

    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index: str = "university-docs"
    azure_search_top_k: int = 5
    azure_search_min_score: float = 0.72

    azure_speech_key: str
    azure_speech_region: str
    azure_speech_token_ttl_seconds: int = 600

    supported_languages: str = "en-US,hi-IN,pa-IN,es-ES,fr-FR,de-DE,ar-SA,zh-CN,ja-JP,ko-KR,ru-RU,it-IT,pt-BR,gu-IN,mr-IN,ta-IN,te-IN,kn-IN,bn-IN,ur-IN"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def supported_language_list(self) -> list[str]:
        return [l.strip() for l in self.supported_languages.split(",") if l.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
