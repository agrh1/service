from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(title="IntraService API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

@app.get("/health")
def health():
    return {"status": "ok", "service": "intraservice"}

# ✅ Добавь оба маршрута
@app.get("/api/task/{ticket_id}/logs")
def get_logs_by_ticket(ticket_id: int):
    """Получить логи заявки (GET запрос)"""
    logger.info(f"Getting logs for ticket {ticket_id}")
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
    logger.info(f"Getting logs for ticket {ticket_id}")
    return {
        "ticket_id": ticket_id,
        "logs": [
            {"timestamp": "2025-12-06T20:00:00Z", "message": "Ticket opened"},
            {"timestamp": "2025-12-06T20:15:00Z", "message": "Status changed"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

