from __future__ import annotations

import logging
import os
from typing import List, Optional

from cryptography.fernet import Fernet, InvalidToken
from pydantic import AnyHttpUrl, BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_encryption_key() -> Optional[Fernet]:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        return None
    try:
        return Fernet(key.encode())
    except Exception:
        raise RuntimeError("Invalid ENCRYPTION_KEY provided")


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not value.startswith("enc:"):
        return value
    cipher = _load_encryption_key()
    if cipher is None:
        raise RuntimeError("Encrypted secret provided but ENCRYPTION_KEY is not set")
    token = value.replace("enc:", "", 1).encode()
    try:
        decrypted = cipher.decrypt(token)
        return decrypted.decode()
    except InvalidToken:
        logging.getLogger(__name__).warning("Failed to decrypt secret, returning raw value")
        return value


def encrypt_secret(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cipher = _load_encryption_key()
    if cipher is None:
        return value
    return f"enc:{cipher.encrypt(value.encode()).decode()}"


class RepositorySettings(BaseModel):
    name: str
    repo_id: str
    instance: str
    categories: List[str] = Field(default_factory=list)
    upload_ttl_seconds: int = 3600
    download_ttl_seconds: int = 7 * 24 * 3600


class SeafileInstanceSettings(BaseModel):
    name: str
    base_url: AnyHttpUrl
    api_tokens: List[str] = Field(default_factory=list)
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True

    def decrypted_tokens(self) -> List[str]:
        return [token for token in (decrypt_secret(token) for token in self.api_tokens) if token]

    def decrypted_password(self) -> Optional[str]:
        return decrypt_secret(self.password)


class Settings(BaseSettings):
    SEAFILE_INSTANCES: List[SeafileInstanceSettings] = Field(default_factory=list)
    SEAFILE_REPOSITORIES: List[RepositorySettings] = Field(default_factory=list)

    DATABASE_URL: str = "postgresql://microservices:microservices@postgres:5432/microservices_db"

    DEFAULT_UPLOAD_TTL_SECONDS: int = 3600
    DEFAULT_DOWNLOAD_TTL_SECONDS: int = 7 * 24 * 3600

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8002
    ENABLE_SCHEDULER: bool = True

    model_config = SettingsConfigDict(env_file='.env')


try:
    settings = Settings()
except ValidationError as exc:
    raise RuntimeError(f"Failed to load configuration: {exc}")
