from __future__ import annotations

import json
import logging
from typing import Dict, Iterable, Set

import requests
from celery import Celery
from celery.schedules import crontab
from redis import Redis, RedisError

from config import settings
from services.eventlog_parser import EventLogParser
from services.html_parser import HTMLParser
from services.intraservice_api import IntraServiceAPI
from services.state_store import EventlogStateStore

logger = logging.getLogger(__name__)

app = Celery(
    'intraservice_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

redis_client = Redis.from_url(settings.REDIS_URL)
state_store = EventlogStateStore(redis_client)


def _publish_event(event_name: str, payload: Dict) -> None:
    message = json.dumps({"event": event_name, "payload": payload})
    try:
        redis_client.publish("intraservice.events", message)
    except RedisError:
        logger.warning("Не удалось отправить событие в Redis")

    if settings.BOT_WEBHOOK_URL:
        try:
            requests.post(settings.BOT_WEBHOOK_URL, json=json.loads(message), timeout=5)
        except requests.RequestException:
            logger.warning("Не удалось отправить webhook для %s", event_name)


def _sync_reference(redis_key: str, items: Iterable[Dict], client: Redis | None = None) -> Dict[str, Set[int]]:
    client = client or redis_client
    new_ids = {int(item["id"]) for item in items if item.get("id") is not None}
    existing_ids = {int(v) for v in client.smembers(redis_key)}

    added = new_ids - existing_ids
    removed = existing_ids - new_ids

    if new_ids:
        client.sadd(redis_key, *new_ids)
    if removed:
        client.srem(redis_key, *removed)

    return {"added": added, "removed": removed}


@app.task
def poll_intraservice_api():
    """Периодический опрос IntraService API"""
    logger.info('Начало опроса IntraService')

    api = IntraServiceAPI()
    tickets = api.get_open_tickets(limit=50)

    if not tickets:
        logger.warning('Заявок не получено')
        return {'status': 'ok', 'tickets_count': 0}

    processed = 0
    for ticket in tickets:
        ticket_id = ticket.get('id')
        logs = api.get_ticket_logs(ticket_id)
        if not logs:
            continue

        lines = HTMLParser.parse_logs(logs)
        errors = HTMLParser.extract_errors(lines)

        _publish_event('ticket_logs', {'ticket_id': ticket_id, 'errors': errors})
        processed += 1

    logger.info('Обработано заявок: %s', processed)

    return {
        'status': 'ok',
        'tickets_received': len(tickets),
        'tickets_processed': processed
    }


@app.task
def sync_catalogs():
    """Сценарий 5.3.1: обновление справочников категорий и исполнителей."""
    api = IntraServiceAPI()
    categories = api.get_categories()
    executors = api.get_executors()

    cat_result = _sync_reference('intraservice:categories', categories)
    exec_result = _sync_reference('intraservice:executors', executors)

    if cat_result["removed"]:
        _publish_event('category_removed', {'ids': list(cat_result['removed'])})
    if exec_result["removed"]:
        _publish_event('executor_removed', {'ids': list(exec_result['removed'])})

    return {
        'categories': {k: list(v) for k, v in cat_result.items()},
        'executors': {k: list(v) for k, v in exec_result.items()},
    }


@app.task
def poll_eventlog():
    """Читает системный лог eventlog.ivp и публикует новые события."""
    api = IntraServiceAPI()
    parser = EventLogParser(settings.EVENTLOG_FILTER_PATTERNS)

    last_id = state_store.get_last_event_id()
    processed_entries = []

    for event_id in range(last_id + 1, last_id + settings.EVENTLOG_BATCH_SIZE + 1):
        html = api.fetch_eventlog_entry(event_id)
        if not html:
            break
        entries = parser.parse_entry(html, event_id)
        if entries:
            _publish_event('eventlog_entry', {'entries': entries})
            processed_entries.extend(entries)
        state_store.set_last_event_id(event_id)

    return {
        'processed': len(processed_entries),
        'last_event_id': state_store.get_last_event_id(),
    }


app.conf.beat_schedule = {
    'poll-intraservice-every-5-minutes': {
        'task': 'tasks.poll_intraservice_api',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'default'}
    },
    'sync-catalogs-every-30-minutes': {
        'task': 'tasks.sync_catalogs',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'default'}
    },
    'poll-eventlog-every-2-minutes': {
        'task': 'tasks.poll_eventlog',
        'schedule': crontab(minute='*/2'),
        'options': {'queue': 'default'}
    },
}


if __name__ == '__main__':
    app.start()

