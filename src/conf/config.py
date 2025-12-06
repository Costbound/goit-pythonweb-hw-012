from pydantic import EmailStr, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_SECONDS: int
    REFRESH_TOKEN_EXPIRE_SECONDS: int
    VERIFICATION_TOKEN_EXPIRE_SECONDS: int
    CORS_ORIGINS: list[str] = []

    SMTP_USER: str
    SMTP_PASSWORD: SecretStr
    SMTP_FROM: EmailStr
    SMTP_PORT: int
    SMTP_HOST: str
    SMTP_FROM_NAME: str = "Contact Book"
    SMTP_STARTTLS: bool = False
    SMTP_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_CACHE_EXPIRE_SECONDS: int = 3600

    # Must be setted in .env to use in compose.yml for redis maxmemory setting, here just for validation
    REDIS_MAX_MEMORY: str

    model_config = SettingsConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins_string(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


settings = Settings()  # type: ignore[arg-type]
