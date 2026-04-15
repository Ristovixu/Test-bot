#!/usr/bin/env python3
"""
Простой тест подключения к Telegram API с requests
"""

import requests
import socket
from config import BOT_TOKEN

def test_connection():
    """Тестируем базовое подключение"""
    try:
        # Проверяем DNS разрешение
        ip = socket.gethostbyname('api.telegram.org')
        print(f"✅ DNS разрешение: api.telegram.org -> {ip}")

        # Проверяем TCP подключение
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((ip, 443))
        sock.close()

        if result == 0:
            print("✅ TCP подключение к порту 443: OK")
        else:
            print(f"❌ TCP подключение к порту 443: FAILED (code {result})")
            return False

    except Exception as e:
        print(f"❌ Ошибка сетевого подключения: {e}")
        return False

    return True

def test_token_requests():
    """Тестируем токен с requests"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

    print(f"🔍 Тестирую URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        print(f"📡 HTTP статус: {response.status_code}")

        data = response.json()
        print(f"📄 Ответ: {data}")

        if data.get('ok'):
            print(f"✅ Токен валиден! Бот: @{data['result']['username']}")
            return True
        else:
            print(f"❌ Ошибка токена: {data.get('description', 'Неизвестная ошибка')}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения к Telegram API")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Диагностика подключения к Telegram API\n")

    if not test_connection():
        print("\n❌ Базовое сетевое подключение не работает")
        exit(1)

    print()
    result = test_token_requests()

    if not result:
        print("\n🔧 Возможные решения:")
        print("1. Проверьте настройки VPN")
        print("2. Попробуйте другой VPN сервер")
        print("3. Проверьте фаервол/антивирус")
        print("4. Попробуйте мобильный интернет")
        print("5. Проверьте системные прокси настройки")