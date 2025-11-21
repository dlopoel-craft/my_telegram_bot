from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
import asyncio

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv("8509738400:AAFR-zOLcpNBiK0CGQXckC_tKsykSUc3tWY")

# Создаём объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот, запущенный на Railway!")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Я могу повторять то, что ты пишешь.")

@dp.message()
async def echo_message(message: types.Message):
    await message.answer(f"Ты написал: {message.text}")

# Точка входа
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())