import os
import asyncio
import threading
from flask import Flask, send_from_directory
from aiogram import Bot, Dispatcher, types

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERROR: Telegram TOKEN not found in environment variables")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# --- BOT ---
@dp.message()
async def send_map_link(message: types.Message):
    await message.answer("Привет 👋\n🌍 Карта Хмельницкого:\nhttps://khm-map-bot.onrender.com")

async def start_bot():
    print("✅ Telegram bot started polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Bot error: {e}")

# --- FLASK ---
@app.route("/")
def index():
    return send_from_directory("static", "map.html")

# --- RUN ---
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(start_bot()), daemon=True).start()
    run_flask()
