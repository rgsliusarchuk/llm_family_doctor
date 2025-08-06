from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # OpenAI configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    
    # LangSmith configuration
    langsmith_api_key: str = Field("", env="LANGSMITH_API_KEY")
    langsmith_project: str = Field("llm-family-doctor", env="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field("https://api.smith.langchain.com", env="LANGSMITH_ENDPOINT")
    
    # model & vector-store paths
    model_id: str = Field("intfloat/multilingual-e5-base", env="MODEL_ID")
    index_path: str = Field("data/faiss_index",              env="INDEX_PATH")
    map_path:   str = Field("data/doc_map.pkl",              env="MAP_PATH")
    
    # Telegram Bot configuration
    telegram_bot_token: str = Field("", env="TELEGRAM_BOT_TOKEN")

    class Config:
        env_file = ".env"        # loads KEY=value pairs from repo root

settings = Settings()            # singleton you'll import elsewhere 