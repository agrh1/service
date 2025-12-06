import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import settings
from handlers import start_router, status_router, getlogs_router, gettickets_router
from utils.logger import get_logger

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
    
    try:
        logger.info("Бот готов к работе")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())

