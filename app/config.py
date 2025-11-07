from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	APP_NAME: str = "Job Automation Agent"
	APP_ENV: str = "development"

	class Config:
		env_file = ".env"


settings = Settings()