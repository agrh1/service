from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.utils import require_admin
from repositories import UserRepository
from utils.logger import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(Command("register_user"))
async def register_user(message: Message):
    repo: UserRepository = message.bot.get("user_repo")
    admin = await require_admin(message, repo)
    if not admin:
        return

    args = message.text.split()
    if len(args) < 3:
        await message.reply(
            "❌ Использование: /register_user <telegram_id> <role>\nПример: /register_user 123456789 user"
        )
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ ID пользователя должен быть числом")
        return

    role = args[2]
    user = await repo.register_user(target_id, None, role=role)
    await message.reply(
        f"✅ Пользователь {target_id} зарегистрирован с ролью {user.role}"
    )
    logger.info("Admin %s registered user %s with role %s", admin.telegram_id, target_id, role)
