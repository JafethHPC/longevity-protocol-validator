from pathlib import Path
from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    project_name: str = "Longevity Validator"
    
    openai_api_key: SecretStr = Field(description="OpenAI API key for LLM calls")
    
    langchain_tracing_v2: str = "true"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: Optional[SecretStr] = Field(default=None, description="LangSmith API key for tracing")
    langchain_project: str = "longevity-validator-dev"
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    report_cache_ttl_hours: int = 24
    
    # API contact email used in User-Agent headers for polite API access
    api_contact_email: str = Field(
        default="researcher@example.com",
        description="Email for API contact/User-Agent (update with your real email)"
    )
    
    @property
    def API_CONTACT_EMAIL(self) -> str:
        return self.api_contact_email
    
    @property
    def OPENAI_API_KEY(self) -> str:
        return self.openai_api_key.get_secret_value()
    
    @property
    def LANGCHAIN_API_KEY(self) -> Optional[str]:
        if self.langchain_api_key:
            return self.langchain_api_key.get_secret_value()
        return None
    
    @property
    def PROJECT_NAME(self) -> str:
        return self.project_name
    
    @property
    def LANGCHAIN_TRACING_V2(self) -> str:
        return self.langchain_tracing_v2
    
    @property
    def LANGCHAIN_ENDPOINT(self) -> str:
        return self.langchain_endpoint
    
    @property
    def LANGCHAIN_PROJECT(self) -> str:
        return self.langchain_project
    
    @property
    def REDIS_HOST(self) -> str:
        return self.redis_host
    
    @property
    def REDIS_PORT(self) -> int:
        return self.redis_port
    
    @property
    def REPORT_CACHE_TTL_HOURS(self) -> int:
        return self.report_cache_ttl_hours


settings = Settings()