from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from utils.logger import get_logger


logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message):
            user = event.from_user
            logger.info(
                "Incoming message from %s (%s): %s",
                user.id if user else "unknown",
                user.username if user else "-",
                event.text,
            )
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Error while handling update")
            raise
