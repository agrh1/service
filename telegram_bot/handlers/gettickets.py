from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.logger import get_logger
import aiohttp
import redis

logger = get_logger(__name__)
gettickets_router = Router()

@gettickets_router.message(Command("gettickets"))
async def gettickets(message: Message):
    """Проверка новых тикетов"""
    logger.info(f"User {message.from_user.id} checking tickets")
    
    await message.reply("⏳ Проверяю новые тикеты...")

    status = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://intraservice:8001/tasks/", timeout=5) as resp:
                status["Intraservice"] = "✅" if resp.status == 200 else "❌"
    except Exception as e:
        logger.error(f"Error checking Intraservice: {e}")
        status["Intraservice"] = "❌"



    await message.reply(resp.text)
