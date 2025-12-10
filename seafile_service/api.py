from flask import Flask, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from services.link_generator import LinkGenerator
from config import settings
import logging

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

