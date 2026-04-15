#!/usr/bin/env python3
"""
Альтернативная версия бота с обходом SSL проблем
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
    from aiohttp import ClientTimeout

    # Простая сессия без SSL для тестирования
    session = AiohttpSession(timeout=ClientTimeout(total=60))
    bot = Bot(token=BOT_TOKEN, session=session)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Проверяем подключение без SSL
    logger.info("Проверяю подключение к Telegram API (без SSL)...")
    try:
        # Используем HTTP вместо HTTPS для тестирования
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        test_session = aiohttp.ClientSession(connector=connector)

        # Пробуем подключиться
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        async with test_session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            data = await response.json()
            if data.get('ok'):
                logger.info(f"✅ Бот @{data['result']['username']} успешно подключен")
            else:
                logger.error(f"❌ Ошибка токена: {data}")
                return

        await test_session.close()

    except Exception as e:
        logger.error(f"Не удалось подключиться к Telegram API: {e}")
        logger.info("Возможные решения:")
        logger.info("1. Проверьте настройки VPN")
        logger.info("2. Отключите антивирус временно")
        logger.info("3. Попробуйте другой VPN")
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