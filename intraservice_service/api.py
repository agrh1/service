import json
import logging
import uuid
from contextvars import ContextVar

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import logging

from config import settings

correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - integration glue
        record.correlation_id = correlation_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # pragma: no cover - formatting
        base = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.__dict__.get("correlation_id"):
            base["correlation_id"] = record.__dict__["correlation_id"]
        return json.dumps(base)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
handler.addFilter(CorrelationIdFilter())
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO), handlers=[handler])

app = FastAPI(title="IntraService API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

Instrumentator().instrument(app).expose(app, include_in_schema=False)

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id_ctx.set(correlation_id)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "intraservice"}


Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/tasks")
def get_tasks():
    return {"status": "ok", "service": "open tickets"}


@app.get("/api/task/{ticket_id}/logs")
def get_logs_by_ticket(ticket_id: int):
    """Получить логи заявки (GET запрос)"""
    logger.info("Получение логов для заявки %s", ticket_id)
    return {
        "ticket_id": ticket_id,
        "logs": [
            {"timestamp": "2025-12-06T20:00:00Z", "message": "Ticket opened"},
            {"timestamp": "2025-12-06T20:15:00Z", "message": "Status changed"}
        ]
    }


@app.post("/logs")
def get_logs(data: dict):
    """Альтернативный POST endpoint"""
    ticket_id = data.get("ticket_id")
    logger.info("Получение логов через POST для заявки %s", ticket_id)
    return {
        "ticket_id": ticket_id,
        "logs": [
            {"timestamp": "2025-12-06T20:00:00Z", "message": "Ticket opened"},
            {"timestamp": "2025-12-06T20:15:00Z", "message": "Status changed"}
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

