from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
# Safe defaults; override via environment or .env file
APP_NAME: str = "Job Automation Agent"
APP_ENV: str = "dev"
CORS_ALLOW_ORIGINS: str = "*" # comma-separated


model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')


settings = Settings()