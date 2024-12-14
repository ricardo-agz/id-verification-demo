from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Union, List
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseSettings):
    # API
    cors_headers: str = "Content-Type"
    api_port: int = 5000

    # DB
    db_url: str | None = None
    db_name: str = "ForgeDB"

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_url: str | None = None

    # s3
    document_images_s3_bucket_name: str = "fireworks-take-home-document-images"
    s3_region: str = "us-east-1"

    # Application
    debug: bool = False
    env: str = "dev"
    dashboard_url: str = "http://localhost:3000"
    cors_origin_whitelist: Union[str, List[str]] = "*"

    model_config = SettingsConfigDict(
        env_file=".env"
    )


class ProductionSettings(Settings):
    debug: bool = False
    env: str = "prod"
    cors_origin_whitelist: List[str] = [
        "https://platform.neutrinoapp.com",
        "https://www.neutrinoapp.com",
    ]

    model_config = SettingsConfigDict(env_file=".env.prod")


class DevelopmentSettings(Settings):
    debug: bool = True
    env: str = "dev"
    cors_origin_whitelist: str = "*"
    redis_password: None = None
    redis_url: None = None

    model_config = SettingsConfigDict(env_file=".env.dev")


@lru_cache()
def get_settings() -> Union[Settings, ProductionSettings, DevelopmentSettings]:
    env = os.getenv("ENV", "dev").lower()

    if env == "prod":
        return ProductionSettings()
    elif env == "dev":
        return DevelopmentSettings()
    return Settings()


settings = get_settings()
