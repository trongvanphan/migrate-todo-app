from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str = "dev-insecure-change-me"
    database_url: str = "sqlite:///./todo.db"
    cors_origins: str = "http://localhost:3000"
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
