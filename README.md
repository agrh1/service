# Service Monorepo

## Расширение бота

Telegram-бот построен на `aiogram 3` и использует модульную структуру роутеров. Чтобы добавить новый обработчик:

1. Создайте файл с роутером, например `telegram_bot/handlers/custom.py`:

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from handlers.utils import require_registered_user

router = Router()

@router.message(Command("ping"))
async def ping(message: Message):
    repo = message.bot.get("user_repo")
    user = await require_registered_user(message, repo)
    if not user:
        return
    await message.reply("pong")
```

2. Зарегистрируйте роутер в `telegram_bot/handlers/__init__.py` и подключите его в `telegram_bot/main.py` через `Dispatcher.include_router`.

3. Для команд с повышенным риском можно добавить флаги rate limiting:

```python
@router.message(Command("secure"), flags={"dangerous": True, "rate_limit": {"interval": 60, "limit": 2}})
async def secure_action(message: Message):
    ...
```

4. При необходимости администраторских прав используйте фильтр роли или хелпер `require_admin` из `telegram_bot/handlers/utils.py`.

Такой подход сохраняет изоляцию логики и позволяет быстро подключать новые команды, не нарушая существующие обработчики и middleware.
