from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    model_name: str = os.getenv("MODEL_NAME", "")
    model_provider: str = os.getenv("MODEL_PROVIDER", "openai")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    max_steps: int = int(os.getenv("MAX_STEPS", "6"))
    repo_root: str = os.getenv("REPO_ROOT", "./sandbox/sample_repo")
    use_mock_llm: bool = os.getenv("USE_MOCK_LLM", "true").lower() == "true"


settings = Settings()
