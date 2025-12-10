import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from utils.logger import get_logger


logger = get_logger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        # storage: {(user_id, tag): deque[timestamps]}
        self.storage: Dict[Tuple[int, str], Deque[float]] = defaultdict(deque)

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not isinstance(event, Message):
            return await handler(event, data)

        handler_obj = data.get("handler")
        flags = getattr(handler_obj, "flags", {}) if handler_obj else {}
        rate_limit_cfg = flags.get("rate_limit") if isinstance(flags, dict) else None
        dangerous = bool(flags.get("dangerous")) if isinstance(flags, dict) else False

        if rate_limit_cfg and dangerous:
            interval = float(rate_limit_cfg.get("interval", 60))
            limit = int(rate_limit_cfg.get("limit", 3))
            default_tag = handler_obj.callback.__name__ if handler_obj else "handler"
            tag = rate_limit_cfg.get("tag") or default_tag
            if not self._is_allowed(event.from_user.id, tag, interval, limit):
                await event.reply(
                    "⚠️ Превышен лимит попыток для опасной операции. Попробуйте позже."
                )
                logger.warning(
                    "Rate limit exceeded for user %s and tag %s", event.from_user.id, tag
                )
                return
        return await handler(event, data)

    def _is_allowed(self, user_id: int, tag: str, interval: float, limit: int) -> bool:
        key = (user_id, tag)
        now = time.monotonic()
        queue = self.storage[key]
        while queue and now - queue[0] > interval:
            queue.popleft()
        if len(queue) >= limit:
            return False
        queue.append(now)
        return True
