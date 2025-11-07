import asyncio
from aiogram import Bot, Dispatcher, types

TOKEN = "8280839809:AAFAQPvRJoWQ6KVd8JFwe_h5SfWC3-Le0I0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def echo(msg: types.Message):
    await msg.answer("Привет! Карта доступна по ссылке:\nhttps://твой-домен.onrender.com")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
