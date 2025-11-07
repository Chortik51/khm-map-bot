import os
import asyncio
import multiprocessing
from flask import Flask, send_from_directory
from aiogram import Bot, Dispatcher, types

# --- TOKEN ---
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERROR: Telegram TOKEN not found in environment variables")
    exit(1)

# --- BOT ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def send_map_link(message: types.Message):
    await message.answer("Привет 👋\n🌍 Карта Хмельницкого:\nhttps://khm-map-bot.onrender.com")

async def start_bot():
    print("✅ Telegram bot started polling...")
    await dp.start_polling(bot)

def run_bot_process():
    asyncio.run(start_bot())

# --- FLASK ---
app = Flask(__name__)

@app.route("/")
def index():
    return send_from_directory("static", "map.html")

# --- MAIN ---
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    bot_process = multiprocessing.Process(target=run_bot_process)
    bot_process.start()
    run_flask()
    bot_process.join()
