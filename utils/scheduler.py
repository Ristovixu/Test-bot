# utils/scheduler.py
"""
Планировщик напоминаний
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, bot: Bot, db):
        self.scheduler = AsyncIOScheduler()
        self.bot = bot
        self.db = db

    def start(self):
        """Запустить планировщик"""
        self.scheduler.start()
        logger.info("Планировщик напоминаний запущен")

    async def restore_reminders(self):
        """Восстановить напоминания после перезапуска бота"""
        bookings = await self.db.get_all_future_bookings()
        restored_count = 0
        
        for booking_id, user_id, date, time, old_job_id in bookings:
            # Удаляем старую задачу, если она есть
            if old_job_id:
                try:
                    self.scheduler.remove_job(old_job_id)
                except:
                    pass
            
            # Создаем новую задачу
            job_id = await self.schedule_reminder(booking_id, user_id, date, time)
            if job_id:
                restored_count += 1
        
        logger.info(f"Восстановлено {restored_count} напоминаний")

    async def schedule_reminder(self, booking_id: int, user_id: int, date: str, time: str):
        """
        Запланировать напоминание за 24 часа до записи
        Возвращает job_id или None, если напоминание не нужно
        """
        try:
            # Парсим дату и время записи
            booking_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            
            # Вычисляем время напоминания (за 24 часа)
            reminder_datetime = booking_datetime - timedelta(hours=24)
            
            # Если время напоминания уже прошло, не создаем задачу
            if reminder_datetime <= datetime.now():
                logger.info(f"Напоминание для записи {booking_id} не создано (менее 24 часов)")
                return None
            
            # Создаем уникальный ID для задачи
            job_id = f"reminder_{booking_id}_{user_id}"
            
            # Планируем задачу
            self.scheduler.add_job(
                self._send_reminder,
                trigger=DateTrigger(run_date=reminder_datetime),
                args=[user_id, time],
                id=job_id,
                replace_existing=True
            )
            
            # Обновляем job_id в базе данных
            await self.db.update_reminder_job_id(booking_id, job_id)
            
            logger.info(f"Запланировано напоминание {job_id} на {reminder_datetime}")
            return job_id
            
        except Exception as e:
            logger.error(f"Ошибка при планировании напоминания: {e}")
            return None

    async def _send_reminder(self, user_id: int, time: str):
        """Отправить напоминание пользователю"""
        try:
            message = (
                f"🔔 <b>Напоминание!</b>\n\n"
                f"Напоминаем, что вы записаны на маникюр завтра в <b>{time}</b>.\n"
                f"Ждём вас! 💅✨"
            )
            await self.bot.send_message(user_id, message, parse_mode="HTML")
            logger.info(f"Напоминание отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")

    def cancel_reminder(self, job_id: str):
        """Отменить напоминание"""
        try:
            if job_id:
                self.scheduler.remove_job(job_id)
                logger.info(f"Напоминание {job_id} отменено")
        except Exception as e:
            logger.error(f"Ошибка при отмене напоминания {job_id}: {e}")

    def shutdown(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        logger.info("Планировщик напоминаний остановлен")
