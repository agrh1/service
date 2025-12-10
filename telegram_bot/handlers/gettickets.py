from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.logger import get_logger
from config import settings
import aiohttp

logger = get_logger(__name__)
gettickets_router = Router()



##пока заглушка, но работает, надо разобраться как реальные таски выдергивать и обрабатывать
@gettickets_router.message(Command("gettickets"))
async def gettickets(message: Message):
    """Проверка новых тикетов"""
    logger.info(f"User {message.from_user.id} checking tickets")
    
    await message.reply("⏳ Проверяю новые тикеты...")

    status = {"API Gateway": "❌"}
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{settings.API_GATEWAY_URL}/api/tickets"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    tickets = data.get("tickets", [])
                    status["API Gateway"] = "✅"
                    await message.reply(f"✅ Найдено заявок: {len(tickets)}")
                else:
                    text = await resp.text()
                    await message.reply(f"❌ Ошибка {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Error checking tickets via gateway: {e}")
        await message.reply(f"❌ Ошибка обращения к API Gateway: {e}")



    await message.reply(status["API Gateway"])
