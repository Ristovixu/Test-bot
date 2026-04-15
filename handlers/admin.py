# handlers/admin.py
"""
Обработчики для администратора
"""

import aiosqlite
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import datetime, timedelta
from database.db import Database
from keyboards.inline import (
    admin_menu, admin_calendar_keyboard, admin_slots_keyboard,
    admin_bookings_keyboard, back_to_menu_keyboard
)
from utils.states import AdminStates
from config import ADMIN_ID, WORKING_HOURS_START, WORKING_HOURS_END, SLOT_DURATION
import logging

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == ADMIN_ID


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    """Админ-панель через callback"""
    await state.clear()
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# === ДОБАВЛЕНИЕ РАБОЧЕГО ДНЯ ===

@router.callback_query(F.data == "admin_add_day")
async def admin_add_day_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления рабочего дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📅 <b>Добавление рабочего дня</b>\n\n"
        "Введите дату в формате <code>ДД.ММ.ГГГГ</code>\n"
        "Например: 25.12.2024",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_date)
    await callback.answer()


@router.message(AdminStates.waiting_for_date)
async def admin_add_day_process(message: Message, state: FSMContext, db: Database):
    """Обработка добавления рабочего дня"""
    if not is_admin(message.from_user.id):
        return
    
    try:
        # Парсим дату
        date_obj = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Добавляем рабочий день
        success = await db.add_working_day(date_str)
        
        if success:
            # Генерируем слоты для этого дня
            slots_added = 0
            current_time = datetime.strptime(f"{WORKING_HOURS_START}:00", "%H:%M")
            end_time = datetime.strptime(f"{WORKING_HOURS_END}:00", "%H:%M")
            
            while current_time < end_time:
                time_str = current_time.strftime("%H:%M")
                await db.add_time_slot(date_str, time_str)
                slots_added += 1
                current_time += timedelta(minutes=SLOT_DURATION)
            
            await message.answer(
                f"✅ <b>Рабочий день добавлен!</b>\n\n"
                f"📅 Дата: <b>{date_obj.strftime('%d.%m.%Y')}</b>\n"
                f"🕐 Создано слотов: <b>{slots_added}</b>",
                reply_markup=admin_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "⚠️ Этот день уже добавлен в расписание.",
                reply_markup=admin_menu(),
                parse_mode="HTML"
            )
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Используйте <code>ДД.ММ.ГГГГ</code>",
            parse_mode="HTML"
        )
        return
    
    await state.clear()


# === ДОБАВЛЕНИЕ СЛОТОВ ===

@router.callback_query(F.data == "admin_add_slots")
async def admin_add_slots_start(callback: CallbackQuery, db: Database):
    """Начало добавления слотов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    # Получаем рабочие дни
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    dates = await db.get_working_days(start_date, end_date)
    
    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных рабочих дней.\n"
            "Сначала добавьте рабочий день.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату для добавления слотов:</b>",
        reply_markup=admin_calendar_keyboard(dates, "addslot"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_addslot_"))
async def admin_add_slots_date(callback: CallbackQuery, state: FSMContext):
    """Выбор даты для добавления слотов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    date = callback.data.split("_")[2]
    await state.update_data(selected_date=date)
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"📅 Дата: <b>{formatted_date}</b>\n\n"
        f"🕐 Введите время в формате <code>ЧЧ:ММ</code>\n"
        f"Например: 14:30",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_time)
    await callback.answer()


@router.message(AdminStates.waiting_for_time)
async def admin_add_slots_process(message: Message, state: FSMContext, db: Database):
    """Обработка добавления слота"""
    if not is_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    date = data['selected_date']
    
    try:
        # Проверяем формат времени
        time_obj = datetime.strptime(message.text.strip(), "%H:%M")
        time_str = time_obj.strftime("%H:%M")
        
        # Добавляем слот
        success = await db.add_time_slot(date, time_str)
        
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y")
        
        if success:
            await message.answer(
                f"✅ <b>Слот добавлен!</b>\n\n"
                f"📅 Дата: <b>{formatted_date}</b>\n"
                f"🕐 Время: <b>{time_str}</b>",
                reply_markup=admin_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"⚠️ Слот на <b>{time_str}</b> уже существует.",
                reply_markup=admin_menu(),
                parse_mode="HTML"
            )
    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Используйте <code>ЧЧ:ММ</code>",
            parse_mode="HTML"
        )
        return
    
    await state.clear()


# === УДАЛЕНИЕ СЛОТОВ ===

@router.callback_query(F.data == "admin_delete_slots")
async def admin_delete_slots_start(callback: CallbackQuery, db: Database):
    """Начало удаления слотов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    dates = await db.get_working_days(start_date, end_date)
    
    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных рабочих дней.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату для удаления слотов:</b>",
        reply_markup=admin_calendar_keyboard(dates, "delslot"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delslot_"))
async def admin_delete_slots_date(callback: CallbackQuery, db: Database):
    """Выбор даты для удаления слотов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    date = callback.data.split("_")[2]
    slots = await db.get_all_slots(date)
    
    if not slots:
        await callback.message.edit_text(
            "❌ На эту дату нет слотов.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"📅 Дата: <b>{formatted_date}</b>\n\n"
        f"🕐 <b>Выберите слот для удаления:</b>\n"
        f"🟢 - свободен, 🔴 - занят",
        reply_markup=admin_slots_keyboard(slots, date, "delete"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_slot_confirm(callback: CallbackQuery, db: Database):
    """Подтверждение удаления слота"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    parts = callback.data.split("_")
    date = parts[2]
    time = parts[3]
    
    await db.delete_time_slot(date, time)
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"✅ <b>Слот удален!</b>\n\n"
        f"📅 Дата: <b>{formatted_date}</b>\n"
        f"🕐 Время: <b>{time}</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# === ЗАКРЫТИЕ ДНЯ ===

@router.callback_query(F.data == "admin_close_day")
async def admin_close_day_start(callback: CallbackQuery, db: Database):
    """Начало закрытия дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    dates = await db.get_working_days(start_date, end_date)
    
    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных рабочих дней.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату для закрытия:</b>",
        reply_markup=admin_calendar_keyboard(dates, "closeday"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_closeday_"))
async def admin_close_day_confirm(callback: CallbackQuery, db: Database):
    """Подтверждение закрытия дня"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    date = callback.data.split("_")[2]
    await db.close_day(date)
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"✅ <b>День закрыт!</b>\n\n"
        f"📅 Дата: <b>{formatted_date}</b>\n\n"
        f"Этот день больше не будет доступен для записи.",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# === ПРОСМОТР РАСПИСАНИЯ ===

@router.callback_query(F.data == "admin_view_schedule")
async def admin_view_schedule_start(callback: CallbackQuery, db: Database):
    """Начало просмотра расписания"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    dates = await db.get_working_days(start_date, end_date)
    
    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных рабочих дней.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату для просмотра расписания:</b>",
        reply_markup=admin_calendar_keyboard(dates, "viewday"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_viewday_"))
async def admin_view_schedule_date(callback: CallbackQuery, db: Database):
    """Просмотр расписания на дату"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    date = callback.data.split("_")[2]
    bookings = await db.get_bookings_by_date(date)
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    if not bookings:
        await callback.message.edit_text(
            f"📅 <b>Расписание на {formatted_date}</b>\n\n"
            f"Записей нет.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    schedule_text = f"📅 <b>Расписание на {formatted_date}</b>\n\n"
    
    for booking_id, user_id, username, name, phone, time in bookings:
        schedule_text += (
            f"🕐 <b>{time}</b>\n"
            f"👤 {name}\n"
            f"📱 {phone}\n"
            f"👤 @{username or 'нет'}\n"
            f"🆔 <code>{user_id}</code>\n\n"
        )
    
    await callback.message.edit_text(
        schedule_text,
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


# === ОТМЕНА ЗАПИСИ КЛИЕНТА ===

@router.callback_query(F.data == "admin_cancel_booking")
async def admin_cancel_booking_start(callback: CallbackQuery, db: Database):
    """Начало отмены записи клиента"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    dates = await db.get_working_days(start_date, end_date)
    
    if not dates:
        await callback.message.edit_text(
            "❌ Нет доступных рабочих дней.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату для отмены записи:</b>",
        reply_markup=admin_calendar_keyboard(dates, "cancelbooking"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cancelbooking_"))
async def admin_cancel_booking_date(callback: CallbackQuery, db: Database):
    """Выбор даты для отмены записи"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    date = callback.data.split("_")[2]
    bookings = await db.get_bookings_by_date(date)
    
    if not bookings:
        await callback.message.edit_text(
            "❌ На эту дату нет записей.",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"📅 Дата: <b>{formatted_date}</b>\n\n"
        f"<b>Выберите запись для отмены:</b>",
        reply_markup=admin_bookings_keyboard(bookings),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cancel_confirm_"))
async def admin_cancel_booking_confirm(callback: CallbackQuery, db: Database, scheduler):
    """Подтверждение отмены записи администратором"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    booking_id = int(callback.data.split("_")[3])
    
    # Получаем информацию о записи для отмены напоминания
    # Нужно получить job_id из базы
    async with aiosqlite.connect(db.db_path) as conn:
        async with conn.execute(
            "SELECT reminder_job_id FROM bookings WHERE id = ?",
            (booking_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                scheduler.cancel_reminder(row[0])
    
    success = await db.cancel_booking(booking_id)
    
    if success:
        await callback.message.edit_text(
            "✅ <b>Запись отменена!</b>",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Ошибка при отмене записи.</b>",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
    
    await callback.answer()
