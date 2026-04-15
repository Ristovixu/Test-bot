#!/usr/bin/env python3
"""
Простой тест токена бота
"""

import asyncio
import aiohttp
from config import BOT_TOKEN

async def test_token():
    """Тестируем токен бота"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()
                if data.get('ok'):
                    print(f"✅ Токен валиден! Бот: @{data['result']['username']}")
                    return True
                else:
                    print(f"❌ Ошибка токена: {data.get('description', 'Неизвестная ошибка')}")
                    return False
        except asyncio.TimeoutError:
            print("❌ Таймаут подключения к Telegram API")
            return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_token())
    if not result:
        print("\n🔧 Возможные решения:")
        print("1. Проверьте токен у @BotFather")
        print("2. Убедитесь, что бот не заблокирован")
        print("3. Проверьте интернет-соединение")
        print("4. Попробуйте VPN если Telegram заблокирован в вашем регионе")