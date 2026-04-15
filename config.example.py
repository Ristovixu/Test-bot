# config.example.py
"""
Пример конфигурационного файла
Скопируйте этот файл в config.py и заполните своими данными
"""

import os

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ID администратора (ваш Telegram ID, узнать у @userinfobot)
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# ID канала для уведомлений (формат: -100xxxxxxxxxx, узнать у @getmyid_bot)
NOTIFICATION_CHANNEL_ID = int(os.getenv("NOTIFICATION_CHANNEL_ID", "-1001234567890"))

# ID канала для обязательной подписки (@username или числовой ID)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")

# Ссылка на портфолио
PORTFOLIO_LINK = os.getenv("PORTFOLIO_LINK", "https://ru.pinterest.com/crystalwithluv/_created/")

# Настройки расписания
WORKING_HOURS_START = 9  # Начало рабочего дня
WORKING_HOURS_END = 18   # Конец рабочего дня
SLOT_DURATION = 60       # Длительность слота в минутах
SCHEDULE_DAYS_AHEAD = 30 # На сколько дней вперед формировать расписание

# База данных
DATABASE_PATH = "manicure_bot.db"
