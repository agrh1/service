import asyncio
import uuid

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from handlers.utils import require_registered_user
from repositories import UserRepository
from utils.logger import get_logger


logger = get_logger(__name__)
router = Router()


def _get_repo(message: Message) -> UserRepository:
    return message.bot.get("user_repo")


@router.message(Command("getlogs"), flags={"dangerous": True, "rate_limit": {"interval": 60, "limit": 3}})
async def cmd_getlogs(message: Message):
    """Обработчик команды /getlogs"""
    repo = _get_repo(message)
    if not repo:
        await message.reply("❌ Репозиторий пользователей не инициализирован")
        return
    user = await require_registered_user(message, repo)
    if not user:
        return

    logger.info("User %s requested logs", message.from_user.id if message.from_user else "-")

    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ Использование: /getlogs <номер_заявки>\nПример: /getlogs 12345")
            return

        ticket_id = int(args[1])
        await repo.set_command_state(message.from_user.id, "getlogs")
        await message.reply(f"⏳ Получаю логи для заявки {ticket_id}...")

        correlation_id = str(uuid.uuid4())
        timeout = aiohttp.ClientTimeout(total=settings.API_GATEWAY_TIMEOUT)
        url = f"{settings.API_GATEWAY_URL}/api/get-logs"
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                url,
                params={"ticket_id": ticket_id},
                headers={"X-Correlation-ID": correlation_id},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data.get("message") or data.get("logs") or "✅ Логи получены"
                    await message.reply(f"{text}\n🧵 Correlation ID: {correlation_id}")
                else:
                    error_text = await resp.text()
                    await message.reply(
                        f"❌ API Gateway вернул ошибку {resp.status}: {error_text}\nCorrelation ID: {correlation_id}"
                    )
    except ValueError:
        await message.reply("❌ Номер заявки должен быть числом\nПример: /getlogs 12345")
    except asyncio.TimeoutError:
        await message.reply("⏱ Таймаут при обращении к API Gateway. Попробуйте позже.")
    except Exception as e:
        logger.error("Error in getlogs: %s", e)
        await message.reply(f"❌ Ошибка: {str(e)}")
