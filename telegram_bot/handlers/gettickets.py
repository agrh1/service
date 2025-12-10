import asyncio
import uuid

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from handlers.utils import require_registered_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = Router()


@router.message(Command("gettickets"), flags={"dangerous": True, "rate_limit": {"interval": 30, "limit": 5}})
async def gettickets(message: Message):
    """Проверка новых тикетов"""
    repo = message.bot.get("user_repo")
    if not repo:
        await message.reply("❌ Репозиторий пользователей не инициализирован")
        return
    user = await require_registered_user(message, repo)
    if not user:
        return

    logger.info("User %s checking tickets", message.from_user.id if message.from_user else "-")

    await message.reply("⏳ Проверяю новые тикеты...")

    correlation_id = str(uuid.uuid4())
    timeout = aiohttp.ClientTimeout(total=settings.API_GATEWAY_TIMEOUT)
    url = f"{settings.API_GATEWAY_URL}/api/tickets"
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url, headers={"X-Correlation-ID": correlation_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tickets = data.get("tickets", [])
                    await repo.set_command_state(message.from_user.id, "gettickets")
                    await message.reply(
                        f"✅ Найдено заявок: {len(tickets)}\n🧵 Correlation ID: {correlation_id}"
                    )
                else:
                    text = await resp.text()
                    await message.reply(
                        f"❌ Ошибка {resp.status}: {text}\nCorrelation ID: {correlation_id}"
                    )
    except asyncio.TimeoutError:
        await message.reply("⏱ Таймаут при обращении к API Gateway. Попробуйте позже.")
    except Exception as e:
        logger.error("Error checking tickets via gateway: %s", e)
        await message.reply(f"❌ Ошибка обращения к API Gateway: {e}")
