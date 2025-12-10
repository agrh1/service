from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from services.link_generator import LinkGenerator
from config import settings
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from flask import Flask, jsonify, request, g, has_request_context
from pydantic import BaseModel, Field, ValidationError

from config import settings
from models import init_db, seed_from_settings
from services.link_generator import LinkGenerator
from tasks import start_scheduler


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.correlation_id = getattr(g, "correlation_id", None)
        else:
            record.correlation_id = None
        return True


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(CorrelationIdFilter())
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), handlers=[handler])


class CreateUploadRequest(BaseModel):
    ticket_id: str
    category: str
    folder_path: Optional[str] = None
    ttl_seconds: Optional[int] = Field(default=None, gt=0)
    repository_name: Optional[str] = None
    instance_name: Optional[str] = None


class CreateDownloadRequest(BaseModel):
    ticket_id: str
    category: str
    file_path: str
    ttl_seconds: Optional[int] = Field(default=None, gt=0)
    repository_name: Optional[str] = None
    instance_name: Optional[str] = None


class StatusRequest(BaseModel):
    ticket_id: str
    category: Optional[str] = None
    close_ticket: bool = False


def create_app():
    configure_logging()
    app = Flask(__name__)
    generator = LinkGenerator()

    init_db()
    seed_from_settings()
    start_scheduler()

    @app.before_request
    def inject_correlation_id():
        g.correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())

    @app.after_request
    def add_correlation_header(response):
        response.headers["X-Correlation-Id"] = g.correlation_id
        return response

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'}), 200

    @app.route('/api/create-upload', methods=['POST'])
    def create_upload():
        try:
            payload = CreateUploadRequest.model_validate(request.get_json(force=True))
            result = generator.generate_upload_link(**payload.model_dump())
            result["correlation_id"] = g.correlation_id
            return jsonify(result), 200
        except ValidationError as exc:
            logging.getLogger(__name__).warning("Validation error", extra={"details": exc.errors()})
            return jsonify({"error": "Invalid payload", "details": exc.errors(), "correlation_id": g.correlation_id}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(str(exc))
            return jsonify({"error": str(exc), "correlation_id": g.correlation_id}), 500

    @app.route('/api/create-download', methods=['POST'])
    def create_download():
        try:
            payload = CreateDownloadRequest.model_validate(request.get_json(force=True))
            result = generator.generate_download_link(**payload.model_dump())
            result["correlation_id"] = g.correlation_id
            return jsonify(result), 200
        except ValidationError as exc:
            logging.getLogger(__name__).warning("Validation error", extra={"details": exc.errors()})
            return jsonify({"error": "Invalid payload", "details": exc.errors(), "correlation_id": g.correlation_id}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(str(exc))
            return jsonify({"error": str(exc), "correlation_id": g.correlation_id}), 500

    @app.route('/api/status', methods=['POST'])
    def status():
        try:
            payload = StatusRequest.model_validate(request.get_json(force=True))
            if payload.close_ticket:
                generator.close_ticket(ticket_id=payload.ticket_id)
            result = generator.get_status(ticket_id=payload.ticket_id, category=payload.category)
            result["correlation_id"] = g.correlation_id
            return jsonify(result), 200
        except ValidationError as exc:
            logging.getLogger(__name__).warning("Validation error", extra={"details": exc.errors()})
            return jsonify({"error": "Invalid payload", "details": exc.errors(), "correlation_id": g.correlation_id}), 400
        except Exception as exc:  # pylint: disable=broad-except
            logging.getLogger(__name__).error(str(exc))
            return jsonify({"error": str(exc), "correlation_id": g.correlation_id}), 500

    return app


app = create_app()

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)
metrics = PrometheusMetrics(app, defaults_prefix="seafile")
metrics.info("app_info", "Seafile service", version="1.0.0")
generator = LinkGenerator()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/generate-links', methods=['POST'])
def generate_links():
    """Генерирует ссылки для заявки"""
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        link_types = data.get('link_types', 'both')
        
        if not ticket_id:
            return jsonify({'error': 'ticket_id is required'}), 400
        
        result = generator.generate_links_for_ticket(ticket_id, link_types)
        
        status_code = 200 if result['status'] == 'ok' else 400
        return jsonify(result), status_code
    
    except Exception as e:
        logger.error(f'Ошибка: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=settings.PORT,
        debug=settings.DEBUG
    )
