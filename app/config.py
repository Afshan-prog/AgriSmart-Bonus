from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AgriSmart Bonus Module API"
    # Placeholder environment variables for future modules
    # WEATHER_API_KEY: str = ""
    # LLM_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
