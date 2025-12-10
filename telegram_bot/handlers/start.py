from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from repositories import UserRepository
from utils.logger import get_logger


logger = get_logger(__name__)
router = Router()


def _get_repo(message: Message) -> UserRepository:
    repo: UserRepository = message.bot.get("user_repo")
    return repo


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    logger.info("User %s started bot", message.from_user.id if message.from_user else "-")
    repo = _get_repo(message)
    if repo:
        user = await repo.get_user(message.from_user.id) if message.from_user else None
    else:
        user = None

    text = """
👋 Добро пожаловать в микросервисную систему!

📋 Доступные команды:
- /help — показать справку
- /status — проверить статус системы
- /gettickets — получить новые тикеты
- /getlogs <номер_заявки> — получить логи заявки
"""
    if user:
        role_hint = "(администратор)" if user.role == "admin" else ""
        text += f"\nВаш статус: зарегистрирован {role_hint}"
    else:
        text += "\n❗️ Вы пока не зарегистрированы. Обратитесь к администратору для доступа."

    await message.reply(text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    repo = _get_repo(message)
    user = await repo.get_user(message.from_user.id) if repo and message.from_user else None

    logger.info("User %s asked for help", message.from_user.id if message.from_user else "-")
    text = """
📖 Справка по командам:

/start — начальное приветствие
/status — проверить статус всех сервисов
/getlogs <номер> — получить логи заявки
/gettickets — проверить новые заявки
/help — эта справка
"""
    if user and user.role == "admin":
        text += "\nКоманды администратора:\n/register_user <telegram_id> <role>\n/block_user <telegram_id>\n/unblock_user <telegram_id>"
    await message.reply(text)
