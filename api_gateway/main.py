from flask import Flask, request, jsonify
from workflows.get_logs_workflow import (
    GetLogsWorkflow,
    GetLogsWorkflowRequest
)
from config import settings
import asyncio
import logging

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = Flask(__name__)

workflow = GetLogsWorkflow(
    intraservice_url=settings.INTRASERVICE_URL,
    seafile_service_url=settings.SEAFILE_SERVICE_URL
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/get-logs', methods=['POST'])
def get_logs():
    """API endpoint для получения логов"""
    
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        link_types = data.get('link_types', 'both')
        
        if not ticket_id:
            return jsonify({'error': 'ticket_id is required'}), 400
        
        workflow_request = GetLogsWorkflowRequest(
            ticket_id=ticket_id,
            link_types=link_types
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(workflow.execute(workflow_request))
        loop.close()
        
        response_data = {
            'status': result.status,
            'ticket_id': result.ticket_id,
            'logs': result.logs,
            'links': result.links
        }
        
        if result.errors:
            response_data['errors'] = result.errors
        
        status_code = 200 if result.status == 'ok' else 206
        return jsonify(response_data), status_code
    
    except Exception as e:
        logger.error(f'Ошибка: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=settings.PORT,
        debug=settings.DEBUG
    )

