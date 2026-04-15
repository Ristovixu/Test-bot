# bot_simple.py
"""
Упрощенная версия бота с увеличенными таймаутами
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import ClientTimeout
from config import BOT_TOKEN
from database.db import Database
from handlers import user, admin, subscription
from utils.scheduler import ReminderScheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    try:
        # Создаем сессию с увеличенными таймаутами
        timeout = ClientTimeout(
            total=120,  # Общий таймаут 120 секунд
            connect=60,  # Таймаут подключения 60 секунд
            sock_connect=60,  # Таймаут сокета 60 секунд
            sock_read=60  # Таймаут чтения 60 секунд
        )
        
        session = AiohttpSession(timeout=timeout)
        
        # Инициализация бота
        bot = Bot(token=BOT_TOKEN, session=session)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
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
        
        # Запуск polling с обработкой ошибок
        try:
            await dp.start_polling(
                bot,
                allowed_updates=dp.resolve_used_update_types(),
                polling_timeout=30,  # Таймаут между запросами
                handle_as_tasks=True
            )
        except Exception as e:
            logger.error(f"Ошибка при polling: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        # Корректное завершение
        try:
            scheduler.shutdown()
            await bot.session.close()
            logger.info("Бот остановлен")
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
