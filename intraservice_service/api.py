intraservice_service/api.pyfrom fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

app = FastAPI(title="IntraService API")

# CORS для gateway
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

@app.post("/logs")
def get_logs(ticket_id: int):
    """Получить логи заявки из IntraService"""
    # заглушка, потом интегрируешь с реальной логикой
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
