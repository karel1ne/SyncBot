import asyncio
import os
from pyrogram import Client
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

async def main():
    if not API_ID or not API_HASH:
        print("Ошибка: API_ID или API_HASH не найдены в .env файле!")
        print("Пожалуйста, заполните .env файл перед запуском этого скрипта.")
        return

    print("Запуск процесса получения SESSION_STRING...")
    print("Вам потребуется ввести номер телефона и код из Telegram.")
    
    async with Client("session_generator", api_id=int(API_ID), api_hash=API_HASH, in_memory=True) as app:
        session_string = await app.export_session_string()
        print("\n" + "="*50)
        print("ВАША SESSION_STRING (скопируйте её полностью):")
        print("="*50 + "\n")
        print(session_string)
        print("\n" + "="*50)
        print("Добавьте эту строку в ваш .env файл:")
        print(f"SESSION_STRING={session_string}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nПроцесс прерван.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
