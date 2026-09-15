from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AgriSmart Bonus Module API"
    # Placeholder environment variables for future modules
    # WEATHER_API_KEY: str = ""
    # LLM_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b:free"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
