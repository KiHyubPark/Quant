from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    booker_base_url: str = "https://restful-booker.herokuapp.com"
    booker_username: str = "admin"
    booker_password: str = "password123"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
