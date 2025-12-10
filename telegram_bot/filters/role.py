from typing import Sequence

from aiogram.filters import BaseFilter
from aiogram.types import Message

from repositories import UserRepository


class RoleFilter(BaseFilter):
    def __init__(self, roles: Sequence[str]):
        self.roles = set(roles)

    async def __call__(self, message: Message) -> bool:
        repo: UserRepository = message.bot.get("user_repo")
        if not repo or not message.from_user:
            return False
        return await repo.ensure_user_has_role(message.from_user.id, list(self.roles))
