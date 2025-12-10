import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from handlers import start_router, status_router, getlogs_router, gettickets_router
from utils.logger import get_logger
from utils.health import start_health_server, stop_bot_metric

logger = get_logger(__name__)

async def main():
    """Запуск бота"""
    logger.info("Запуск Telegram бота")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Подключение роутеров
    dp.include_router(start_router)
    dp.include_router(status_router)
    dp.include_router(getlogs_router)
    dp.include_router(gettickets_router)
    
    health_runner = None

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
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())

