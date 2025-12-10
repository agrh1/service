import asyncio
from aiogram import Bot, Dispatcher

from config import settings
from handlers import (
    admin_router,
    getlogs_router,
    gettickets_router,
    start_router,
    status_router,
)
from middlewares import LoggingMiddleware, RateLimitMiddleware
from repositories import UserRepository
from utils.logger import get_logger
from utils.health import start_health_server, stop_bot_metric

logger = get_logger(__name__)


async def main():
    """Запуск бота"""
    logger.info("Запуск Telegram бота")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    repo = UserRepository()
    await repo.connect()

    bot["user_repo"] = repo

    dp = Dispatcher()

    # Подключение роутеров
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    dp.include_router(start_router)
    dp.include_router(status_router)
    dp.include_router(getlogs_router)
    dp.include_router(gettickets_router)
    
    health_runner = None
    dp.include_router(admin_router)

    try:
        logger.info("Бот готов к работе")
        health_runner = await start_health_server(settings.METRICS_PORT)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
    finally:
        stop_bot_metric()
        if health_runner:
            await health_runner.cleanup()
        await repo.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
