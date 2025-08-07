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
    index_path: str = Field("data/faiss_index", env="INDEX_PATH")
    map_path: str = Field("data/doc_map.pkl", env="MAP_PATH")
    
    # Database configuration
    database_url: str = Field("sqlite:///data/clinic.db", env="DATABASE_URL")
    
    # Redis configuration
    redis_url: str = Field("redis://cache:6379/0", env="REDIS_URL")
    redis_ttl_days: int = Field(30, env="REDIS_TTL_DAYS")
    
    # API configuration
    api_base_url: str = Field("http://familydoc:8000", env="API_BASE_URL")
    api_base: str = Field("http://familydoc", env="API_BASE")
    
    # Telegram Bot configuration
    telegram_bot_token: str = Field("", env="TELEGRAM_BOT_TOKEN")
    doctor_group_id: str = Field("", env="DOCTOR_GROUP_ID")
    
    # Debug configuration
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    
    # AWS & ECR configuration
    aws_access_key_id: str = Field("", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("", env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field("eu-central-1", env="AWS_REGION")
    ecr_repository: str = Field("familydoc", env="ECR_REPOSITORY")
    ecr_registry: str = Field("735740439208.dkr.ecr.eu-central-1.amazonaws.com", env="ECR_REGISTRY")
    
    # Traefik & Domain configuration
    traefik_domain: str = Field("18.195.119.5", env="TRAEFIK_DOMAIN")
    tag: str = Field("latest", env="TAG")
    
    # EC2 Deployment configuration
    ec2_host: str = Field("18.195.119.5", env="EC2_HOST")
    ec2_user: str = Field("ubuntu", env="EC2_USER")
    ec2_ssh_key: str = Field("", env="EC2_SSH_KEY")

    class Config:
        env_file = ".env"

settings = Settings() 