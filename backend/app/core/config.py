from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/automacao_juridica"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    aes_key: str = "change-me-32-byte-aes-key!!!!!!"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        """URL pronta para o SQLAlchemy async.

        Aceita a connection string crua do Railway (`postgresql://...`):
        troca o driver para asyncpg e remove `sslmode`, que é parâmetro do
        psycopg2 e faz o asyncpg falhar na conexão.
        """
        url = make_url(self.database_url)
        if url.drivername in ("postgres", "postgresql"):
            url = url.set(drivername="postgresql+asyncpg")
        url = url.difference_update_query(["sslmode"])
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
