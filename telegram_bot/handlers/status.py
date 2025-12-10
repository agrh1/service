import aiohttp
import redis.asyncio as redis
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from handlers.utils import require_registered_user
from utils.logger import get_logger


logger = get_logger(__name__)
router = Router()


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Проверка статуса системы"""
    repo = message.bot.get("user_repo")
    if not repo:
        await message.reply("❌ Репозиторий пользователей не инициализирован")
        return
    user = await require_registered_user(message, repo)
    if not user:
        return

    logger.info("User %s checking status", message.from_user.id if message.from_user else "-")
    await message.reply("⏳ Проверяю статус системы...")

    statuses = {}
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("http://django:8000/health/") as resp:
                statuses["Django"] = "✅" if resp.status == 200 else "❌"
    except Exception as e:
        logger.error("Error checking Django: %s", e)
        statuses["Django"] = "❌"

    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
        )
        await redis_client.ping()
        statuses["Redis"] = "✅"
    except Exception as e:
        logger.error("Error checking Redis: %s", e)
        statuses["Redis"] = "❌"

    text = "📊 Статус сервисов:\n\n"
    for name, status in statuses.items():
        text += f"{status} {name}\n"

    await message.reply(text)
