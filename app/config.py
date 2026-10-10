"""Central, typed configuration loaded from environment variables / .env."""
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Export .env into os.environ so provider SDKs (OpenAI, Anthropic, ...) can read their keys.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic Research Assistant"
    log_level: str = "INFO"
    api_key: str | None = None  # when set, clients must send X-API-Key
    cors_origins: list[str] = ["*"]

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2

    # Embeddings / retrieval
    embedding_provider: str = "openai"  # openai | fake
    embedding_model: str = "text-embedding-3-small"
    retrieval_k: int = 4
    chunk_size: int = 800
    chunk_overlap: int = 120
    max_upload_mb: int = 10

    # Web search
    tavily_api_key: str | None = None

    # Agent behaviour
    max_plan_steps: int = 4
    max_tool_rounds: int = 3
    max_revisions: int = 2
    min_review_score: int = 7
    history_window: int = 6
    recursion_limit: int = 40

    # Storage
    data_dir: Path = Path("data")

    @property
    def checkpoint_db(self) -> Path:
        return self.data_dir / "checkpoints.db"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def docs_dir(self) -> Path:
        return self.data_dir / "docs"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
