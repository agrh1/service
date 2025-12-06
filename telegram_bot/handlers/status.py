from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.logger import get_logger
import aiohttp
import redis

logger = get_logger(__name__)
status_router = Router()

@status_router.message(Command("status"))
async def cmd_status(message: Message):
    """Проверка статуса системы"""
    logger.info(f"User {message.from_user.id} checking status")
    
    await message.reply("⏳ Проверяю статус системы...")

    statuses = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://django:8000/health/", timeout=5) as resp:
                statuses["Django"] = "✅" if resp.status == 200 else "❌"
    except Exception as e:
        logger.error(f"Error checking Django: {e}")
        statuses["Django"] = "❌"

    # 2. Redis по PING
    try:
        r = redis.Redis(host="redis", port=6379, db=0)
        r.ping()
        statuses["Redis"] = "✅"
    except Exception as e:
        logger.error(f"Error checking Redis: {e}")
        statuses["Redis"] = "❌"

    text = "📊 Статус сервисов:\n\n"
    for name, status in statuses.items():
        text += f"{status} {name}\n"

    await message.reply(text)
