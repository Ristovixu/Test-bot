# keyboards/inline.py
"""
Inline-клавиатуры для бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from config import PORTFOLIO_LINK


def main_menu():
    """Главное меню"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📅 Записаться", callback_data="book"))
    keyboard.row(InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking"))
    keyboard.row(InlineKeyboardButton(text="💰 Прайсы", callback_data="prices"))
    keyboard.row(InlineKeyboardButton(text="📸 Портфолио", callback_data="portfolio"))
    return keyboard.as_markup()


def subscription_check_keyboard(channel_link: str):
    """Клавиатура для проверки подписки"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📢 Подписаться", url=channel_link))
    keyboard.row(InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription"))
    return keyboard.as_markup()


def portfolio_keyboard():
    """Клавиатура с портфолио"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="👀 Смотреть портфолио", url=PORTFOLIO_LINK))
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return keyboard.as_markup()


def calendar_keyboard(available_dates: list):
    """Календарь с доступными датами"""
    keyboard = InlineKeyboardBuilder()
    
    for date in available_dates:
        # Форматируем дату для отображения
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        display_date = date_obj.strftime("%d.%m.%Y (%a)")
        keyboard.row(InlineKeyboardButton(
            text=display_date,
            callback_data=f"date_{date}"
        ))
    
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return keyboard.as_markup()


def time_slots_keyboard(slots: list, selected_date: str):
    """Клавиатура с временными слотами"""
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем слоты по 3 в ряд
    for i in range(0, len(slots), 3):
        row_slots = slots[i:i+3]
        for slot in row_slots:
            keyboard.add(InlineKeyboardButton(
                text=slot,
                callback_data=f"time_{selected_date}_{slot}"
            ))
        keyboard.adjust(len(row_slots))
    
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="book"))
    return keyboard.as_markup()


def confirm_booking_keyboard(date: str, time: str):
    """Клавиатура подтверждения записи"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text="✅ Подтвердить",
        callback_data=f"confirm_{date}_{time}"
    ))
    keyboard.row(InlineKeyboardButton(
        text="❌ Отменить",
        callback_data="book"
    ))
    return keyboard.as_markup()


def cancel_booking_confirm_keyboard(booking_id: int):
    """Клавиатура подтверждения отмены записи"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text="✅ Да, отменить",
        callback_data=f"confirm_cancel_{booking_id}"
    ))
    keyboard.row(InlineKeyboardButton(
        text="❌ Нет",
        callback_data="back_to_menu"
    ))
    return keyboard.as_markup()


def back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu"))
    return keyboard.as_markup()


# === АДМИН-КЛАВИАТУРЫ ===

def admin_menu():
    """Админ-панель"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📅 Управление днями", callback_data="admin_manage_days"))
    keyboard.row(InlineKeyboardButton(text="➕ Добавить слоты", callback_data="admin_add_slots"))
    keyboard.row(InlineKeyboardButton(text="➖ Удалить слоты", callback_data="admin_delete_slots"))
    keyboard.row(InlineKeyboardButton(text="🔒 Закрыть день", callback_data="admin_close_day"))
    keyboard.row(InlineKeyboardButton(text="📋 Просмотр расписания", callback_data="admin_view_schedule"))
    keyboard.row(InlineKeyboardButton(text="❌ Отменить запись клиента", callback_data="admin_cancel_booking"))
    keyboard.row(InlineKeyboardButton(text="🔙 Выход", callback_data="back_to_menu"))
    return keyboard.as_markup()


def admin_calendar_keyboard(available_dates: list, action: str):
    """Календарь для админа"""
    keyboard = InlineKeyboardBuilder()
    
    for date in available_dates:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        display_date = date_obj.strftime("%d.%m.%Y")
        keyboard.row(InlineKeyboardButton(
            text=display_date,
            callback_data=f"admin_{action}_{date}"
        ))
    
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin"))
    return keyboard.as_markup()


def admin_slots_keyboard(slots: list, date: str, action: str):
    """Клавиатура слотов для админа"""
    keyboard = InlineKeyboardBuilder()
    
    for slot_time, is_booked in slots:
        status = "🔴" if is_booked else "🟢"
        keyboard.row(InlineKeyboardButton(
            text=f"{status} {slot_time}",
            callback_data=f"admin_{action}_{date}_{slot_time}"
        ))
    
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin"))
    return keyboard.as_markup()


def admin_bookings_keyboard(bookings: list):
    """Клавиатура записей для отмены"""
    keyboard = InlineKeyboardBuilder()
    
    for booking_id, user_id, username, name, phone, time in bookings:
        display_text = f"{time} - {name} (@{username or 'нет'})"
        keyboard.row(InlineKeyboardButton(
            text=display_text,
            callback_data=f"admin_cancel_confirm_{booking_id}"
        ))
    
    keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin"))
    return keyboard.as_markup()
