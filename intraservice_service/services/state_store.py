import logging
from typing import Optional

import redis

from config import settings

try:  # pragma: no cover - optional dependency during runtime
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


logger = logging.getLogger(__name__)


class EventlogStateStore:
    redis_key = "eventlog:last_id"

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or redis.from_url(settings.REDIS_URL)
        self._pg_conn: Optional["psycopg.Connection"] = None

    def get_last_event_id(self) -> int:
        if self.redis:
            try:
                value = self.redis.get(self.redis_key)
                if value:
                    return int(value)
            except redis.RedisError:
                logger.warning("Не удалось получить last_id из Redis")

        pg_conn = self._get_pg_conn()
        if pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute("SELECT last_event_id FROM eventlog_state WHERE id = 1")
                row = cur.fetchone()
                return int(row[0]) if row else 0
        return 0

    def set_last_event_id(self, event_id: int) -> None:
        if self.redis:
            try:
                self.redis.set(self.redis_key, event_id)
                return
            except redis.RedisError:
                logger.warning("Не удалось сохранить last_id в Redis")

        pg_conn = self._get_pg_conn()
        if pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO eventlog_state (id, last_event_id) VALUES (1, %s) "
                    "ON CONFLICT (id) DO UPDATE SET last_event_id = EXCLUDED.last_event_id",
                    (event_id,),
                )
                pg_conn.commit()

    def _get_pg_conn(self):
        if not psycopg:
            return None
        if self._pg_conn is None:
            self._pg_conn = psycopg.connect(settings.postgres_dsn)
            self._ensure_pg_table()
        return self._pg_conn

    def _ensure_pg_table(self) -> None:
        if not self._pg_conn:
            return
        with self._pg_conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS eventlog_state (
                    id INTEGER PRIMARY KEY,
                    last_event_id BIGINT NOT NULL
                )
                """
            )
            self._pg_conn.commit()
