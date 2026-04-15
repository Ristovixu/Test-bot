# bot.py
"""
Главный файл бота для мастера по маникюру
"""

import asyncio
import logging
import sys
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.db import Database
from handlers import user, admin, subscription
from utils.scheduler import ReminderScheduler

# Исправление для Windows asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    # Инициализация бота и диспетчера
    from aiogram.client.session.aiohttp import AiohttpSession
    
    # Создаем сессию (aiogram 3.x сам управляет таймаутами)
    session = AiohttpSession()
    bot = Bot(token=BOT_TOKEN, session=session)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Попытка подключения к Telegram API
    logger.info("Проверяю подключение к Telegram API...")
    try:
        me = await bot.get_me()
        logger.info(f"Бот @{me.username} успешно подключен")
    except Exception as e:
        logger.error(f"Не удалось подключиться к Telegram API: {e}")
        logger.info("Проверьте токен бота и интернет-соединение")
        return
    
    # Инициализация базы данных
    db = Database()
    await db.init_db()
    logger.info("База данных инициализирована")
    
    # Инициализация планировщика напоминаний
    scheduler = ReminderScheduler(bot, db)
    scheduler.start()
    logger.info("Планировщик запущен")
    
    # Восстановление напоминаний после перезапуска
    await scheduler.restore_reminders()
    
    # Регистрация роутеров
    dp.include_router(subscription.router)
    dp.include_router(user.router)
    dp.include_router(admin.router)
    
    # Передача зависимостей в middleware
    dp['db'] = db
    dp['scheduler'] = scheduler
    
    # Middleware для передачи db и scheduler в хендлеры
    @dp.update.outer_middleware()
    async def db_middleware(handler, event, data):
        data['db'] = db
        data['scheduler'] = scheduler
        return await handler(event, data)
    
    logger.info("Бот запущен")
    
    try:
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Корректное завершение
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
