from celery import Celery
from config import settings
from services.intraservice_api import IntraServiceAPI
from services.html_parser import HTMLParser
import logging

logger = logging.getLogger(__name__)

app = Celery(
    'intraservice_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@app.task
def poll_intraservice_api():
    """Периодический опрос IntraService API"""
    logger.info('Начало опроса IntraService')
    
    api = IntraServiceAPI()
    
    if not api.login():
        logger.error('Не удалось залогиниться')
        return {'status': 'error', 'message': 'Login failed'}
    
    tickets = api.get_tickets(limit=50)
    
    if not tickets:
        logger.warning('Заявок не получено')
        return {'status': 'ok', 'tickets_count': 0}
    
    processed = 0
    for ticket in tickets:
        try:
            ticket_id = ticket.get('id')
            logs = api.get_ticket_logs(ticket_id)
            
            if not logs:
                continue
            
            parser = HTMLParser()
            lines = parser.parse_logs(logs)
            errors = parser.extract_errors(lines)
            
            logger.info(f'Заявка {ticket_id}: {len(errors)} ошибок')
            processed += 1
        
        except Exception as e:
            logger.error(f'Ошибка при обработке заявки: {str(e)}')
    
    logger.info(f'Обработано заявок: {processed}')
    
    return {
        'status': 'ok',
        'tickets_received': len(tickets),
        'tickets_processed': processed
    }

# Расписание для Celery Beat
from celery.schedules import crontab

app.conf.beat_schedule = {
    'poll-intraservice-every-5-minutes': {
        'task': 'tasks.poll_intraservice_api',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'default'}
    },
}

if __name__ == '__main__':
    app.start()

