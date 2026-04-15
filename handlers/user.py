# handlers/user.py
"""
Обработчики для пользователей
"""

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from database.db import Database
from keyboards.inline import (
    main_menu, calendar_keyboard, time_slots_keyboard,
    confirm_booking_keyboard, cancel_booking_confirm_keyboard,
    back_to_menu_keyboard, portfolio_keyboard, subscription_check_keyboard
)
from utils.states import BookingStates
from config import (
    ADMIN_ID, NOTIFICATION_CHANNEL_ID, SCHEDULE_DAYS_AHEAD,
    CHANNEL_LINK
)
from handlers.subscription import check_subscription
import logging

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database, bot: Bot):
    """Обработка команды /start"""
    # Проверяем подписку
    is_subscribed = await check_subscription(bot, message.from_user.id)
    
    if not is_subscribed:
        await message.answer(
            "👋 <b>Добро пожаловать!</b>\n\n"
            "Для записи на маникюр необходимо подписаться на наш канал.\n"
            "После подписки нажмите кнопку «Проверить подписку».",
            reply_markup=subscription_check_keyboard(CHANNEL_LINK),
            parse_mode="HTML"
        )
        return
    
    # Приветственное сообщение с изображением
    welcome_text = (
        f"👋 <b>Добро пожаловать, {message.from_user.first_name}!</b>\n\n"
        "💅 <b>Салон красоты «Beauty Ind»</b>\n\n"
        "✨ Профессиональный маникюр и педикюр\n"
        "🎨 Индивидуальный подход к каждому клиенту\n"
        "💎 Качественные материалы и инструменты\n\n"
        "Выберите действие:"
    )
    
    # Пытаемся отправить фото приветствия
    try:
        # Здесь можно указать URL изображения или файл
        # await message.answer_photo(
        #     photo="https://example.com/welcome_image.jpg",
        #     caption=welcome_text,
        #     reply_markup=main_menu(),
        #     parse_mode="HTML"
        # )
        await message.answer(
            welcome_text,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки приветственного фото: {e}")
        await message.answer(
            welcome_text,
            reply_markup=main_menu(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "prices")
async def show_prices(callback: CallbackQuery):
    """Показать прайс-лист"""
    await callback.answer()
    
    prices_text = (
        "💰 <b>Прайс-лист услуг</b>\n\n"
        "💅 <b>Маникюр:</b>\n"
        "• Классический маникюр — от <b>1500₽</b>\n"
        "• Французский маникюр — от <b>1800₽</b>\n"
        "• Гелевый маникюр — от <b>2000₽</b>\n"
        "• Маникюр + покрытие гель-лаком — от <b>2500₽</b>\n\n"
        "🦶 <b>Педикюр:</b>\n"
        "• Классический педикюр — от <b>2000₽</b>\n"
        "• Комбинированный педикюр — от <b>2500₽</b>\n"
        "• Педикюр + покрытие гель-лаком — от <b>3000₽</b>\n\n"
        "🎨 <b>Дизайн и украшения:</b>\n"
        "• Простой дизайн — от <b>300₽</b>\n"
        "• Сложный дизайн — от <b>500₽</b>\n"
        "• Стразы/Swarovski — от <b>100₽</b> за камень\n\n"
        "💡 <i>Цены могут варьироваться в зависимости от сложности работы</i>\n"
        "📞 Для точного расчета свяжитесь с мастером"
    )
    
    await callback.message.edit_text(
        prices_text,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    """Показать портфолио"""
    await callback.answer()
    
    await callback.message.edit_text(
        "📸 <b>Моё портфолио</b>\n\n"
        "Посмотрите мои работы и убедитесь в качестве!\n"
        "Нажмите кнопку ниже, чтобы перейти к портфолио.",
        reply_markup=portfolio_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, db: Database, bot: Bot):
    """Начало процесса записи"""
    await callback.answer()
    
    # Проверяем подписку
    is_subscribed = await check_subscription(bot, callback.from_user.id)
    if not is_subscribed:
        await callback.message.edit_text(
            "❌ <b>Подписка не найдена</b>\n\n"
            "Для записи необходимо подписаться на наш канал.\n"
            "После подписки нажмите кнопку «Проверить подписку».",
            reply_markup=subscription_check_keyboard(CHANNEL_LINK),
            parse_mode="HTML"
        )
        return
    
    # Проверяем, есть ли уже активная запись
    existing_booking = await db.get_user_booking(callback.from_user.id)
    if existing_booking:
        booking_id, name, phone, date, time, _ = existing_booking
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d.%m.%Y")
        
        await callback.message.edit_text(
            f"⚠️ <b>У вас уже есть активная запись!</b>\n\n"
            f"📅 Дата: <b>{formatted_date}</b>\n"
            f"🕐 Время: <b>{time}</b>\n"
            f"👤 Имя: <b>{name}</b>\n"
            f"📱 Телефон: <b>{phone}</b>\n\n"
            f"Сначала отмените текущую запись, чтобы записаться на другое время.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Получаем доступные даты
    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=SCHEDULE_DAYS_AHEAD)).strftime("%Y-%m-%d")
    available_dates = await db.get_working_days(start_date, end_date)
    
    if not available_dates:
        await callback.message.edit_text(
            "😔 <b>К сожалению, нет доступных дат для записи.</b>\n\n"
            "Попробуйте позже или свяжитесь с администратором.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату:</b>",
        reply_markup=calendar_keyboard(available_dates),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("date_"))
async def select_date(callback: CallbackQuery, db: Database):
    """Выбор даты"""
    await callback.answer()
    
    selected_date = callback.data.split("_")[1]
    
    # Получаем доступные слоты
    available_slots = await db.get_available_slots(selected_date)
    
    if not available_slots:
        await callback.message.edit_text(
            "😔 <b>На эту дату нет свободных слотов.</b>\n\n"
            "Выберите другую дату.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"📅 Дата: <b>{formatted_date}</b>\n\n"
        f"🕐 <b>Выберите время:</b>",
        reply_markup=time_slots_keyboard(available_slots, selected_date),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    """Выбор времени"""
    await callback.answer()
    
    parts = callback.data.split("_")
    selected_date = parts[1]
    selected_time = parts[2]
    
    # Сохраняем выбранные дату и время
    await state.update_data(date=selected_date, time=selected_time)
    
    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"📅 Дата: <b>{formatted_date}</b>\n"
        f"🕐 Время: <b>{selected_time}</b>\n\n"
        f"👤 <b>Введите ваше имя:</b>",
        parse_mode="HTML"
    )
    
    await state.set_state(BookingStates.waiting_for_name)


@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Имя слишком короткое. Попробуйте еще раз:")
        return
    
    await state.update_data(name=name)
    await message.answer(
        f"👤 Имя: <b>{name}</b>\n\n"
        f"📱 <b>Введите ваш номер телефона:</b>\n"
        f"(например: +79991234567)",
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.waiting_for_phone)


@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    phone = message.text.strip()
    
    if len(phone) < 10:
        await message.answer("❌ Номер телефона слишком короткий. Попробуйте еще раз:")
        return
    
    # Получаем сохраненные данные
    data = await state.get_data()
    date = data['date']
    time = data['time']
    name = data['name']
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await state.update_data(phone=phone)
    
    await message.answer(
        f"✅ <b>Подтвердите запись:</b>\n\n"
        f"📅 Дата: <b>{formatted_date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📱 Телефон: <b>{phone}</b>",
        reply_markup=confirm_booking_keyboard(date, time),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot, scheduler):
    """Подтверждение записи"""
    await callback.answer()
    
    data = await state.get_data()
    date = data['date']
    time = data['time']
    name = data['name']
    phone = data['phone']
    
    user_id = callback.from_user.id
    username = callback.from_user.username
    
    # Создаем запись в БД (без job_id пока)
    await db.create_booking(user_id, username, name, phone, date, time)
    
    # Получаем ID созданной записи
    booking = await db.get_user_booking(user_id)
    booking_id = booking[0]
    
    # Планируем напоминание
    job_id = await scheduler.schedule_reminder(booking_id, user_id, date, time)
    
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    # Уведомление пользователю
    await callback.message.edit_text(
        f"✅ <b>Запись успешно создана!</b>\n\n"
        f"📅 Дата: <b>{formatted_date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📱 Телефон: <b>{phone}</b>\n\n"
        f"Ждём вас! 💅✨\n\n"
        f"{'🔔 Вам придёт напоминание за 24 часа до визита.' if job_id else ''}",
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML"
    )
    
    # Уведомление администратору
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>Новая запись!</b>\n\n"
            f"📅 Дата: <b>{formatted_date}</b>\n"
            f"🕐 Время: <b>{time}</b>\n"
            f"👤 Имя: <b>{name}</b>\n"
            f"📱 Телефон: <b>{phone}</b>\n"
            f"👤 Username: @{username or 'нет'}\n"
            f"🆔 User ID: <code>{user_id}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления админу: {e}")
    
    # Уведомление в канал
    try:
        await bot.send_message(
            NOTIFICATION_CHANNEL_ID,
            f"📅 <b>Новая запись</b>\n\n"
            f"Дата: <b>{formatted_date}</b>\n"
            f"Время: <b>{time}</b>\n"
            f"Клиент: <b>{name}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки в канал: {e}")
    
    await state.clear()


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking_start(callback: CallbackQuery, db: Database, bot: Bot):
    """Начало отмены записи"""
    await callback.answer()
    
    # Проверяем подписку
    is_subscribed = await check_subscription(bot, callback.from_user.id)
    if not is_subscribed:
        await callback.message.edit_text(
            "❌ <b>Подписка не найдена</b>\n\n"
            "Для доступа к функциям бота необходимо подписаться на наш канал.",
            reply_markup=subscription_check_keyboard(CHANNEL_LINK),
            parse_mode="HTML"
        )
        return
    
    booking = await db.get_user_booking(callback.from_user.id)
    
    if not booking:
        await callback.message.edit_text(
            "ℹ️ <b>У вас нет активных записей.</b>",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
        return
    
    booking_id, name, phone, date, time, _ = booking
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    
    await callback.message.edit_text(
        f"❓ <b>Вы уверены, что хотите отменить запись?</b>\n\n"
        f"📅 Дата: <b>{formatted_date}</b>\n"
        f"🕐 Время: <b>{time}</b>\n"
        f"👤 Имя: <b>{name}</b>\n"
        f"📱 Телефон: <b>{phone}</b>",
        reply_markup=cancel_booking_confirm_keyboard(booking_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel_booking(callback: CallbackQuery, db: Database, scheduler):
    """Подтверждение отмены записи"""
    await callback.answer()
    
    booking_id = int(callback.data.split("_")[2])
    
    # Получаем данные записи перед удалением
    booking = await db.get_user_booking(callback.from_user.id)
    if booking:
        _, _, _, _, _, job_id = booking
        # Отменяем напоминание
        if job_id:
            scheduler.cancel_reminder(job_id)
    
    # Отменяем запись
    success = await db.cancel_booking(booking_id)
    
    if success:
        await callback.message.edit_text(
            "✅ <b>Запись успешно отменена.</b>\n\n"
            "Вы можете записаться на другое время.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Ошибка при отмене записи.</b>\n\n"
            "Попробуйте позже или свяжитесь с администратором.",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML"
        )
