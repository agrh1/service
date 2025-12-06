from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.logger import get_logger

logger = get_logger(__name__)

start_router = Router()

@start_router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info(f"User {message.from_user.id} started bot")
    
    text = """
👋 Добро пожаловать в микросервисную систему!

📋 Доступные команды:
- /help - показать справку
- /status - проверить статус системы
- /getlogs <номер_заявки> - получить логи заявки
"""
    await message.reply(text)

@start_router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    logger.info(f"User {message.from_user.id} asked for help")
    
    text = """
📖 Справка по командам:

**/start** - начальное приветствие

**/status** - проверить статус всех сервисов
Покажет доступность:
- Django портала
- IntraService API
- Seafile Service

**/getlogs <номер>** - получить логи заявки
Пример: /getlogs 12345
Вернёт:
- Логи из IntraService
- Ссылки для скачивания
- Защищённый доступ

**/help** - эта справка
"""
    await message.reply(text)

