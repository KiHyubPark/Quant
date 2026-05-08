from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    booker_base_url: str = "https://restful-booker.herokuapp.com"
    booker_username: str = "admin"
    booker_password: str = "password123"

    # 자동매매 스케줄러 활성화 여부 (KIS OpenAPI 연동 완료 후 true로 변경)
    scheduler_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
