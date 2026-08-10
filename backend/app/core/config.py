from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

PLACEHOLDER_JWT_SECRET = "change-me-jwt-secret"
PLACEHOLDER_AES_KEY = "change-me-32-byte-aes-key!!!!!!"
# RFC 7518 §3.2: chave HMAC de HS256 deve ter pelo menos o tamanho do digest.
JWT_SECRET_MIN_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/automacao_juridica"
    jwt_secret: str = PLACEHOLDER_JWT_SECRET
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    password_reset_token_expire_minutes: int = 60
    aes_key: str = PLACEHOLDER_AES_KEY
    cors_origins: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _rejeita_segredos_placeholder(self) -> "Settings":
        """Impede subir fora de development com os segredos de exemplo."""
        if self.app_env == "development":
            return self

        placeholders = {
            "JWT_SECRET": self.jwt_secret == PLACEHOLDER_JWT_SECRET,
            "AES_KEY": self.aes_key == PLACEHOLDER_AES_KEY,
        }
        pendentes = [nome for nome, is_placeholder in placeholders.items() if is_placeholder]
        if pendentes:
            raise ValueError(
                f"Segredos com valor de exemplo em APP_ENV={self.app_env}: {', '.join(pendentes)}. "
                "Defina valores reais nas variáveis de ambiente."
            )

        if len(self.jwt_secret) < JWT_SECRET_MIN_LENGTH:
            raise ValueError(
                f"JWT_SECRET precisa ter ao menos {JWT_SECRET_MIN_LENGTH} caracteres"
            )
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def frontend_url(self) -> str:
        """Base do frontend, usada para montar links enviados ao usuário."""
        origens = self.cors_origins_list
        return origens[0] if origens else "http://localhost:3000"

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
