import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = set(map(int, os.getenv("ADMIN_ID", "").split()))


logging.info(f"✅ Бот запущен. Администраторы: {ADMIN_IDS}")

# Инициализация бота
# bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище ожидаемых ответов (admin_id -> user_id)
pending_replies = {}
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer("🔹 Вы администратор. Вы можете отвечать на обращения пользователей.")
    else:
        await message.answer(
            "Здравствуйте!\n\nПожалуйста, отправьте вашу жалобу или пожелание одним сообщением и дождитесь подтверждения.")


# Добавление нового администратора
@dp.message(Command("add_admin"))
async def add_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    try:
        new_admin_id = int(message.text.split()[1])
        if new_admin_id in ADMIN_IDS:
            await message.answer("⚠ Этот пользователь уже является администратором.")
            return
        ADMIN_IDS.add(new_admin_id)
        await message.answer("✅ Администратор добавлен!")
    except (IndexError, ValueError):
        await message.answer("❌ Используйте команду в формате: /add_admin <ID>")


# Основной обработчик сообщений
@dp.message()
async def handle_messages(message: Message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in ADMIN_IDS:
        await message.answer("✅ Обращение принято\n\nБлагодарим")
        admin_text = f"📩 *Новое обращение от пользователя {user_id}:*\n\n{text}"
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Ответить", callback_data=f"reply_{user_id}")
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, admin_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения админу {admin_id}: {e}")
    elif user_id in ADMIN_IDS and user_id in pending_replies:
        target_id = pending_replies.pop(user_id)
        try:
            await bot.send_message(target_id, f"📩 *Ответ от администрации:*\n\n{message.text}", parse_mode="Markdown")
            await message.answer(f"✅ Ответ отправлен пользователю {target_id}.")
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке ответа пользователю: {e}")
    elif user_id in ADMIN_IDS:
        await message.answer("❌ Нет ожидающих ответов.")


# Обработчик кнопки "Ответить"
@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def process_reply_button(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[1])
    pending_replies[callback_query.from_user.id] = user_id
    await bot.send_message(callback_query.from_user.id, f"✍ Введите ваш ответ для пользователя {user_id}.")
    await callback_query.answer()


# # Запуск бота
# async def main():
#     logging.basicConfig(level=logging.INFO)
#     await dp.start_polling(bot)

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

