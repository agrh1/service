from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.utils import require_admin
from repositories import UserRepository
from utils.logger import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(Command("block_user"))
async def block_user(message: Message):
    repo: UserRepository = message.bot.get("user_repo")
    admin = await require_admin(message, repo)
    if not admin:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Использование: /block_user <telegram_id>")
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ ID пользователя должен быть числом")
        return
    user = await repo.block_user(target_id, True)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    await message.reply(f"⛔️ Пользователь {target_id} заблокирован")
    logger.info("Admin %s blocked user %s", admin.telegram_id, target_id)


@router.message(Command("unblock_user"))
async def unblock_user(message: Message):
    repo: UserRepository = message.bot.get("user_repo")
    admin = await require_admin(message, repo)
    if not admin:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("❌ Использование: /unblock_user <telegram_id>")
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.reply("❌ ID пользователя должен быть числом")
        return
    user = await repo.block_user(target_id, False)
    if not user:
        await message.reply("❌ Пользователь не найден")
        return
    await message.reply(f"✅ Пользователь {target_id} разблокирован")
    logger.info("Admin %s unblocked user %s", admin.telegram_id, target_id)
