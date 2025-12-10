from typing import Optional

from aiogram.types import Message

from repositories import UserRepository, User


async def require_registered_user(message: Message, repo: UserRepository) -> Optional[User]:
    if not repo:
        await message.reply("❌ Репозиторий пользователей не инициализирован")
        return None
    if not message.from_user:
        await message.reply("❌ Не удалось определить пользователя.")
        return None

    user = await repo.get_user(message.from_user.id)
    if not user:
        await message.reply(
            "❌ Вы не зарегистрированы в системе. Обратитесь к администратору."
        )
        return None
    if user.is_blocked:
        await message.reply("⛔️ Ваш доступ заблокирован. Свяжитесь с администратором.")
        return None
    return user


async def require_admin(message: Message, repo: UserRepository) -> Optional[User]:
    user = await require_registered_user(message, repo)
    if not user:
        return None
    if user.role != "admin":
        await message.reply("❌ Недостаточно прав для выполнения команды.")
        return None
    return user
