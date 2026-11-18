from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-6-luna"
    request_timeout_seconds: float = 15.0
    max_page_bytes: int = 1_500_000
    max_content_characters: int = 18_000
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
