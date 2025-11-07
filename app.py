import os
import asyncio
import multiprocessing
import sqlite3
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# === НАСТРОЙКИ ===
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ ERROR: TOKEN not found")
    exit(1)

DB_FILE = "markers.db"
EXPIRATION_SECONDS = 20 * 60  # 20 минут

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# === СОЗДАНИЕ ТАБЛИЦЫ ДЛЯ МЕТОК ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            timestamp INTEGER
        )
    """)
    conn.commit()
    conn.close()

# === УДАЛЕНИЕ СТАРЫХ МЕТОК ===
def cleanup_old_markers():
    while True:
        now = int(time.time())
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM markers WHERE timestamp < ?", (now - EXPIRATION_SECONDS,))
        conn.commit()
        conn.close()
        time.sleep(60)  # чистим каждую минуту

# === FLASK API ===
@app.route("/")
def index():
    return send_from_directory("static", "map.html")

@app.route("/api/markers")
def get_markers():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT lat, lon, timestamp FROM markers")
    markers = [{"lat": row[0], "lon": row[1], "timestamp": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify(markers)

@app.route("/api/add_marker", methods=["POST"])
def add_marker():
    data = request.json
    lat, lon = data.get("lat"), data.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "invalid data"}), 400
    ts = int(time.time())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO markers (lat, lon, timestamp) VALUES (?, ?, ?)", (lat, lon, ts))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# === TELEGRAM БОТ ===
@dp.message(CommandStart())
async def start_cmd(msg: types.Message):
    btn = types.InlineKeyboardButton(text="🌍 Открыть карту", url="https://khm-map-bot.onrender.com")
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[btn]])
    await msg.answer(
        "👋 Привет! Это интерактивная карта Хмельницкого.\n\n"
        "Нажми кнопку ниже, чтобы открыть карту и поставить свою метку (она исчезнет через 20 минут).",
        reply_markup=kb
    )

async def start_bot():
    print("✅ Telegram bot started polling...")
    await dp.start_polling(bot)

def run_bot_process():
    asyncio.run(start_bot())

# === MAIN ===
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=cleanup_old_markers, daemon=True).start()
    bot_process = multiprocessing.Process(target=run_bot_process)
    bot_process.start()
    run_flask()
    bot_process.join()
