# handlers/subscription.py
"""
Обработчики проверки подписки на канал
"""

from aiogram import Router, Bot
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from config import CHANNEL_ID, CHANNEL_LINK
from keyboards.inline import subscription_check_keyboard, main_menu
import logging

router = Router()
logger = logging.getLogger(__name__)


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """
    Проверить подписку пользователя на канал
    Возвращает True, если подписан, иначе False
    """
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Статусы: creator, administrator, member - подписан
        # left, kicked - не подписан
        return member.status in ["creator", "administrator", "member"]
    except TelegramBadRequest as e:
        logger.error(f"Ошибка проверки подписки для пользователя {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при проверке подписки: {e}")
        return False


@router.callback_query(lambda c: c.data == "check_subscription")
async def process_check_subscription(callback: CallbackQuery, bot: Bot):
    """Обработка проверки подписки"""
    await callback.answer()
    
    is_subscribed = await check_subscription(bot, callback.from_user.id)
    
    if is_subscribed:
        await callback.message.edit_text(
            "✅ <b>Отлично!</b>\n\n"
            "Вы подписаны на канал. Теперь вы можете записаться на маникюр.",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "❌ <b>Подписка не найдена</b>\n\n"
            "Для записи необходимо подписаться на наш канал.\n"
            "После подписки нажмите кнопку «Проверить подписку».",
            reply_markup=subscription_check_keyboard(CHANNEL_LINK),
            parse_mode="HTML"
        )
