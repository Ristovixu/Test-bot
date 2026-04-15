# database/db.py
"""
Модуль для работы с базой данных SQLite
"""

import aiosqlite
from datetime import datetime, timedelta
from config import DATABASE_PATH


class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица рабочих дней
            await db.execute("""
                CREATE TABLE IF NOT EXISTS working_days (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    is_closed INTEGER DEFAULT 0
                )
            """)

            # Таблица временных слотов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS time_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    is_booked INTEGER DEFAULT 0,
                    UNIQUE(date, time)
                )
            """)

            # Таблица записей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    reminder_job_id TEXT
                )
            """)

            await db.commit()

    # === РАБОТА С РАБОЧИМИ ДНЯМИ ===
    
    async def add_working_day(self, date: str):
        """Добавить рабочий день"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO working_days (date, is_closed) VALUES (?, 0)",
                    (date,)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def close_day(self, date: str):
        """Закрыть день (сделать нерабочим)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE working_days SET is_closed = 1 WHERE date = ?",
                (date,)
            )
            await db.commit()

    async def open_day(self, date: str):
        """Открыть день"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE working_days SET is_closed = 0 WHERE date = ?",
                (date,)
            )
            await db.commit()

    async def get_working_days(self, start_date: str, end_date: str):
        """Получить рабочие дни в диапазоне"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT date FROM working_days WHERE date BETWEEN ? AND ? AND is_closed = 0 ORDER BY date",
                (start_date, end_date)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def is_day_closed(self, date: str):
        """Проверить, закрыт ли день"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_closed FROM working_days WHERE date = ?",
                (date,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] == 1 if row else True

    # === РАБОТА СО СЛОТАМИ ===
    
    async def add_time_slot(self, date: str, time: str):
        """Добавить временной слот"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO time_slots (date, time, is_booked) VALUES (?, ?, 0)",
                    (date, time)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def delete_time_slot(self, date: str, time: str):
        """Удалить временной слот"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM time_slots WHERE date = ? AND time = ?",
                (date, time)
            )
            await db.commit()

    async def get_available_slots(self, date: str):
        """Получить доступные слоты на дату"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT time FROM time_slots WHERE date = ? AND is_booked = 0 ORDER BY time",
                (date,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_all_slots(self, date: str):
        """Получить все слоты на дату (для админа)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT time, is_booked FROM time_slots WHERE date = ? ORDER BY time",
                (date,)
            ) as cursor:
                return await cursor.fetchall()

    async def book_slot(self, date: str, time: str):
        """Забронировать слот"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE time_slots SET is_booked = 1 WHERE date = ? AND time = ?",
                (date, time)
            )
            await db.commit()

    async def unbook_slot(self, date: str, time: str):
        """Освободить слот"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE time_slots SET is_booked = 0 WHERE date = ? AND time = ?",
                (date, time)
            )
            await db.commit()

    # === РАБОТА С ЗАПИСЯМИ ===
    
    async def create_booking(self, user_id: int, username: str, name: str, 
                           phone: str, date: str, time: str, reminder_job_id: str = None):
        """Создать запись"""
        async with aiosqlite.connect(self.db_path) as db:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                """INSERT INTO bookings 
                   (user_id, username, name, phone, date, time, created_at, reminder_job_id) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, username, name, phone, date, time, created_at, reminder_job_id)
            )
            await db.commit()
            await self.book_slot(date, time)

    async def get_user_booking(self, user_id: int):
        """Получить активную запись пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, name, phone, date, time, reminder_job_id FROM bookings WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                return await cursor.fetchone()

    async def cancel_booking(self, booking_id: int):
        """Отменить запись"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем данные записи
            async with db.execute(
                "SELECT date, time FROM bookings WHERE id = ?",
                (booking_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    date, time = row
                    # Удаляем запись
                    await db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
                    await db.commit()
                    # Освобождаем слот
                    await self.unbook_slot(date, time)
                    return True
        return False

    async def get_bookings_by_date(self, date: str):
        """Получить все записи на дату"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """SELECT id, user_id, username, name, phone, time 
                   FROM bookings WHERE date = ? ORDER BY time""",
                (date,)
            ) as cursor:
                return await cursor.fetchall()

    async def get_all_future_bookings(self):
        """Получить все будущие записи (для восстановления напоминаний)"""
        async with aiosqlite.connect(self.db_path) as db:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
            async with db.execute(
                """SELECT id, user_id, date, time, reminder_job_id 
                   FROM bookings 
                   WHERE date || ' ' || time > ?""",
                (current_datetime,)
            ) as cursor:
                return await cursor.fetchall()

    async def update_reminder_job_id(self, booking_id: int, job_id: str):
        """Обновить ID задачи напоминания"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE bookings SET reminder_job_id = ? WHERE id = ?",
                (job_id, booking_id)
            )
            await db.commit()
