"""Черновик новой версии `seafile_service/api.py`.

Ключевые моменты:
- Единое Flask-приложение без дублирующих инстансов.
- Pydantic-схемы запросов/ответов через `pydantic` v1 (совместимо с Flask).
- Структурированные логи с correlation_id и временной меткой.
- Задел под несколько инстансов/репозиториев и TTL download-ссылок.
"""

from __future__ import annotations

import json
import logging
import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from flask import Flask, jsonify, request, g, has_request_context
from flask.typing import ResponseReturnValue
from pydantic import BaseModel, Field, ValidationError
from prometheus_flask_exporter import PrometheusMetrics


# ===== Логирование =====
class JsonFormatter(logging.Formatter):
    """JSON-формат логов для централизованной сборки."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - форматирование
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if hasattr(record, "correlation_id"):
            payload["correlation_id"] = record.correlation_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class CorrelationIdFilter(logging.Filter):
    """Вытаскивает correlation_id из контекста Flask."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - интеграционное клеяние
        record.correlation_id = getattr(g, "correlation_id", None) if has_request_context() else None
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(CorrelationIdFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])


configure_logging()
logger = logging.getLogger(__name__)


# ===== Конфиг и доменные структуры =====
class Settings(BaseModel):
    seafile_instances: Dict[str, str] = Field(
        default_factory=lambda: {"default": "https://drv.pixel.org.ru"},
        description="Список инстансов Seafile (имя->URL API)",
    )
    default_repo: str = Field("logs", description="Имя репозитория по умолчанию")
    download_ttl_days: int = Field(7, description="Срок действия download-ссылки в днях")
    password_length: int = Field(12, description="Длина пароля для download-ссылок")


@dataclass
class GeneratedLink:
    url: str
    password: Optional[str]
    expires_at: Optional[datetime]
    instance: str
    repository: str


class CreateUploadRequest(BaseModel):
    ticket_id: str
    category: str
    folder_path: Optional[str] = None
    repository_name: Optional[str] = None
    instance_name: Optional[str] = None


class CreateDownloadRequest(BaseModel):
    ticket_id: str
    category: str
    file_path: str
    repository_name: Optional[str] = None
    instance_name: Optional[str] = None


class StatusRequest(BaseModel):
    ticket_id: str
    category: Optional[str] = None
    close_ticket: bool = False


class StatusResponse(BaseModel):
    correlation_id: str
    upload_url: Optional[str] = None
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    instance: Optional[str] = None
    repository: Optional[str] = None


# ===== Вспомогательные функции =====
def generate_password(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class SeafileRouter:
    """Простейший роутер инстансов/репозиториев.

    Здесь должны быть реальные вызовы Seafile API: создание папок, выдача upload/download-ссылок
    и удаление просроченных. Пока методы возвращают заглушки, чтобы не блокировать выкладки.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage: Dict[str, GeneratedLink] = {}

    def _resolve(self, instance_name: Optional[str], repository_name: Optional[str]) -> tuple[str, str]:
        instance = instance_name or "default"
        if instance not in self.settings.seafile_instances:
            raise ValueError(f"Неизвестный инстанс: {instance}")
        repository = repository_name or self.settings.default_repo
        return instance, repository

    def create_upload_link(self, payload: CreateUploadRequest) -> GeneratedLink:
        instance, repository = self._resolve(payload.instance_name, payload.repository_name)
        url = f"{self.settings.seafile_instances[instance]}/upload/{payload.ticket_id}/"
        link = GeneratedLink(url=url, password=None, expires_at=None, instance=instance, repository=repository)
        self.storage[f"upload:{payload.ticket_id}"] = link
        return link

    def create_download_link(self, payload: CreateDownloadRequest) -> GeneratedLink:
        instance, repository = self._resolve(payload.instance_name, payload.repository_name)
        password = generate_password(self.settings.password_length)
        expires_at = datetime.utcnow() + timedelta(days=self.settings.download_ttl_days)
        url = f"{self.settings.seafile_instances[instance]}/download/{payload.ticket_id}/{payload.file_path}"
        link = GeneratedLink(url=url, password=password, expires_at=expires_at, instance=instance, repository=repository)
        self.storage[f"download:{payload.ticket_id}"] = link
        return link

    def get_status(self, ticket_id: str) -> StatusResponse:
        upload = self.storage.get(f"upload:{ticket_id}")
        download = self.storage.get(f"download:{ticket_id}")
        return StatusResponse(
            correlation_id=g.correlation_id,
            upload_url=upload.url if upload else None,
            download_url=download.url if download else None,
            download_expires_at=download.expires_at if download else None,
            instance=upload.instance if upload else (download.instance if download else None),
            repository=upload.repository if upload else (download.repository if download else None),
        )

    def cleanup_expired(self) -> None:
        """Удаляет просроченные download-ссылки (TTL берём из настроек)."""

        now = datetime.utcnow()
        for key, link in list(self.storage.items()):
            if key.startswith("download:") and link.expires_at and link.expires_at < now:
                logger.info("Удаляем просроченную ссылку", extra={"ticket": key, "expires_at": link.expires_at.isoformat()})
                self.storage.pop(key, None)


# ===== Flask-приложение =====
def create_app() -> Flask:
    settings = Settings()
    router = SeafileRouter(settings=settings)

    app = Flask(__name__)
    metrics = PrometheusMetrics(app, defaults_prefix="seafile")
    metrics.info("app_info", "Seafile service", version="1.0.0")

    @app.before_request
    def inject_correlation_id() -> None:  # pragma: no cover - интеграционная обвязка
        g.correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())

    @app.after_request
    def add_correlation_header(response):  # pragma: no cover - интеграционная обвязка
        response.headers["X-Correlation-Id"] = g.correlation_id
        return response

    @app.route("/health", methods=["GET"])
    def health() -> ResponseReturnValue:
        return jsonify({"status": "ok"}), 200

    @app.route("/api/create-upload", methods=["POST"])
    def create_upload() -> ResponseReturnValue:
        try:
            payload = CreateUploadRequest.model_validate(request.get_json(force=True))
            link = router.create_upload_link(payload)
            return (
                jsonify(
                    {
                        "upload_url": link.url,
                        "instance": link.instance,
                        "repository": link.repository,
                        "correlation_id": g.correlation_id,
                    }
                ),
                200,
            )
        except ValidationError as exc:
            logger.warning("Validation error", extra={"details": exc.errors()})
            return jsonify({"error": "Invalid payload", "details": exc.errors(), "correlation_id": g.correlation_id}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Upload error", exc_info=exc)
            return jsonify({"error": str(exc), "correlation_id": g.correlation_id}), 500

    @app.route("/api/create-download", methods=["POST"])
    def create_download() -> ResponseReturnValue:
        try:
            payload = CreateDownloadRequest.model_validate(request.get_json(force=True))
            link = router.create_download_link(payload)
            return (
                jsonify(
                    {
                        "download_url": link.url,
                        "password": link.password,
                        "expires_at": link.expires_at.isoformat(),
                        "instance": link.instance,
                        "repository": link.repository,
                        "correlation_id": g.correlation_id,
                    }
                ),
                200,
            )
        except ValidationError as exc:
            logger.warning("Validation error", extra={"details": exc.errors()})
            return jsonify({"error": "Invalid payload", "details": exc.errors(), "correlation_id": g.correlation_id}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Download error", exc_info=exc)
            return jsonify({"error": str(exc), "correlation_id": g.correlation_id}), 500

    @app.route("/api/status", methods=["POST"])
    def status() -> ResponseReturnValue:
        try:
            payload = StatusRequest.model_validate(request.get_json(force=True))
            result = router.get_status(ticket_id=payload.ticket_id)
            return jsonify(result.model_dump()), 200
        except ValidationError as exc:
            logger.warning("Validation error", extra={"details": exc.errors()})
            return jsonify({"error": "Invalid payload", "details": exc.errors(), "correlation_id": g.correlation_id}), 400

    @app.route("/api/cleanup", methods=["POST"])
    def cleanup() -> ResponseReturnValue:
        router.cleanup_expired()
        return jsonify({"status": "ok", "correlation_id": g.correlation_id}), 200

    return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover - ручной запуск
    app.run(host="0.0.0.0", port=8002)

