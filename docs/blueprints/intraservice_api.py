"""Черновик новой версии `intraservice_service/api.py`.

Основные принципы:
- FastAPI + Prometheus метрики из коробки.
- Корреляционный ID для всех запросов (X-Correlation-ID).
- Чёткие Pydantic-схемы входа/выхода.
- Заглушки бизнес-логики помечены комментариями, чтобы их дописать без ломки интерфейсов.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Annotated, AsyncIterator, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_fastapi_instrumentator import Instrumentator

# Контекст с корреляционным ID
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class CorrelationIdFilter(logging.Filter):
    """Добавляет correlation_id в каждый лог-запись."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - интеграционное клеяние
        record.correlation_id = correlation_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """Форматирует логи в JSON для дальнейшей отправки в Loki/ELK."""

    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - форматирование
        base = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if record.__dict__.get("correlation_id"):
            base["correlation_id"] = record.__dict__["correlation_id"]
        return json.dumps(base, ensure_ascii=False)


def configure_logging() -> None:
    """Настройка логирования единым образом."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(CorrelationIdFilter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])


class Settings(BaseModel):
    """Минимальный набор настроек; в реальном сервисе брать из env/portal."""

    intraservice_base: str = Field("https://support.pixel.org.ru", description="Базовый URL IntraService")
    open_status_id: int = Field(31, description="ID статуса 'открыто' для выборки заявок")
    eventlog_path: str = Field("/eventlog.ivp/view/", description="Префикс для получения HTML системного лога")
    request_timeout: float = Field(10.0, description="Таймаут запросов к IntraService")


class TicketSummary(BaseModel):
    ticket_id: int
    title: str
    status_id: int
    category: Optional[str] = None
    assignee: Optional[str] = None
    updated_at: datetime


class EventLogRecord(BaseModel):
    record_id: int
    level: str
    source: str
    message: str
    created_at: datetime


class TicketsResponse(BaseModel):
    correlation_id: str
    tickets: list[TicketSummary]


class EventlogResponse(BaseModel):
    correlation_id: str
    records: list[EventLogRecord]


class IntraServiceClient:
    """Тонкий клиент к IntraService.

    В реальной реализации здесь должны быть:
    - Аутентификация (basic + cookie-сессия).
    - Парсинг HTML eventlog через selectolax/BeautifulSoup.
    - Кеширование смещений в Redis/Postgres, чтобы не читать один и тот же лог дважды.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=settings.request_timeout)

    async def fetch_open_tickets(self) -> list[TicketSummary]:
        """Получить открытые заявки.

        Сейчас возвращает заглушку, но интерфейс готов к реальным данным.
        """

        # TODO: заменить на запрос к API IntraService и разбор ответа
        dummy = TicketSummary(
            ticket_id=123,
            title="Заглушка заявки",
            status_id=self._settings.open_status_id,
            category="logsml",
            assignee="seaf_user",
            updated_at=datetime.utcnow(),
        )
        return [dummy]

    async def fetch_eventlog_page(self, last_record_id: Optional[int] = None) -> list[EventLogRecord]:
        """Получить новую порцию системного лога после last_record_id."""

        # TODO: сделать HTTP GET к self._settings.eventlog_path + id
        dummy = EventLogRecord(
            record_id=last_record_id + 1 if last_record_id else 1,
            level="INFO",
            source="dummy",
            message="Новая запись системного лога",
            created_at=datetime.utcnow(),
        )
        return [dummy]

    async def close(self) -> None:
        await self._client.aclose()


async def get_client() -> AsyncIterator[IntraServiceClient]:
    """Dependency FastAPI: выдаёт клиент и закрывает сессию после запроса."""

    settings = Settings()
    client = IntraServiceClient(settings=settings)
    try:
        yield client
    finally:
        await client.close()


configure_logging()
logger = logging.getLogger(__name__)
app = FastAPI(title="IntraService Service", version="1.0.0")

# CORS для интеграций с порталом/ботом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    """Проставляет и прокидывает X-Correlation-ID."""

    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id_ctx.set(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health", summary="Проверка живости")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "intraservice"}


@app.get("/api/tickets", response_model=TicketsResponse, summary="Получить открытые заявки")
async def list_open_tickets(
    client: Annotated[IntraServiceClient, Depends(get_client)],
) -> TicketsResponse:
    tickets = await client.fetch_open_tickets()
    return TicketsResponse(correlation_id=correlation_id_ctx.get() or "", tickets=tickets)


@app.get(
    "/api/eventlog",
    response_model=EventlogResponse,
    summary="Получить новые записи системного лога",
)
async def read_eventlog(
    last_record_id: Optional[int] = None,
    client: Annotated[IntraServiceClient, Depends(get_client)],
) -> EventlogResponse:
    records = await client.fetch_eventlog_page(last_record_id=last_record_id)
    return EventlogResponse(correlation_id=correlation_id_ctx.get() or "", records=records)


@app.post("/api/refresh", summary="Фоновые задачи опроса IntraService")
async def trigger_refresh(
    body: dict | None = None,  # pragma: no cover - подготовка под будущие параметры
    client: Annotated[IntraServiceClient, Depends(get_client)],
) -> dict[str, str]:
    """Endpoint для ручного запуска опроса (используется CI/админкой)."""

    await client.fetch_open_tickets()
    await client.fetch_eventlog_page()
    return {"status": "scheduled", "correlation_id": correlation_id_ctx.get() or ""}


# Обработчик ошибок для единообразного JSON
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):  # pragma: no cover - обёртка
    logger.warning("HTTP error", extra={"status_code": exc.status_code, "detail": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "correlation_id": correlation_id_ctx.get() or "",
        },
    )


@app.on_event("shutdown")
async def shutdown_event():  # pragma: no cover - lifecycle hook
    logger.info("Stopping IntraService service")

