from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from utils.logger import get_logger

logger = get_logger(__name__)
getlogs_router = Router()

@getlogs_router.message(Command("getlogs"))
async def cmd_getlogs(message: Message):
    """Обработчик команды /getlogs"""
    logger.info(f"User {message.from_user.id} requested logs")
    
    try:
        args = message.text.split()
        
        if len(args) < 2:
            await message.reply("❌ Использование: /getlogs <номер_заявки>\nПример: /getlogs 12345")
            return
        
        ticket_id = int(args[1])
        
        await message.reply(f"⏳ Получаю логи для заявки {ticket_id}...")
        
        # Здесь будет интеграция с API Gateway (в Sprint 5)
        # На данный момент просто возвращаем сообщение
        
        text = f"""
✅ Заявка {ticket_id}:

📋 Логи получены
📤 Upload ссылка: (будет доступна в Sprint 4)
📥 Download ссылка: (будет доступна в Sprint 4)
🔐 Пароль: (будет доступен в Sprint 4)

ℹ️ Полный функционал будет доступен после Sprint 4 (Seafile интеграция)
"""
        await message.reply(text)
    
    except ValueError:
        await message.reply("❌ Номер заявки должен быть числом\nПример: /getlogs 12345")
    except Exception as e:
        logger.error(f"Error in getlogs: {e}")
        await message.reply(f"❌ Ошибка: {str(e)}")
