import os
import asyncio
import multiprocessing
import sqlite3
import time
import threading
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
            timestamp INTEGER,
            user_id TEXT
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
        time.sleep(60)

# === FLASK API ===
@app.route("/")
def index():
    return send_from_directory("static", "map.html")

@app.route("/api/markers", methods=["POST"])
def get_markers():
    data = request.json
    current_user = data.get("user_id")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, timestamp, user_id FROM markers")
    markers = []
    for row in c.fetchall():
        markers.append({
            "id": row[0],
            "lat": row[1],
            "lon": row[2],
            "timestamp": row[3],
            "is_owner": (row[4] == current_user)
        })
    conn.close()
    return jsonify(markers)

@app.route("/api/add_marker", methods=["POST"])
def add_marker():
    data = request.json
    lat, lon, user_id = data.get("lat"), data.get("lon"), data.get("user_id")
    if lat is None or lon is None or not user_id:
        return jsonify({"error": "invalid data"}), 400
    ts = int(time.time())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO markers (lat, lon, timestamp, user_id) VALUES (?, ?, ?, ?)",
              (lat, lon, ts, user_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/api/delete_marker", methods=["POST"])
def delete_marker():
    data = request.json
    marker_id = data.get("id")
    user_id = data.get("user_id")
    if not marker_id or not user_id:
        return jsonify({"error": "invalid data"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM markers WHERE id = ? AND user_id = ?", (marker_id, user_id))
    conn.commit()
    deleted = c.rowcount
    conn.close()

    if deleted > 0:
        return jsonify({"status": "deleted"})
    else:
        return jsonify({"status": "not_owner"}), 403

# === TELEGRAM БОТ ===
@dp.message(CommandStart())
async def start_cmd(msg: types.Message):
    btn = types.InlineKeyboardButton(text="🌍 Открыть карту", url="https://khm-map-bot.onrender.com")
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[btn]])
    await msg.answer(
        "👋 Привет! Это интерактивная карта Хмельницкого.\n\n"
        "Ты можешь добавить метку касанием карты. Она исчезнет через 20 минут.\n"
        "Ты можешь удалить только свои метки.",
        reply_markup=kb
    )

async def start_bot():
    print("✅ Telegram bot started polling...")
    await dp.start_polling(bot)

def run_bot_process():
    asyncio.run(start_bot())

def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=cleanup_old_markers, daemon=True).start()
    bot_process = multiprocessing.Process(target=run_bot_process)
    bot_process.start()
    run_flask()
    bot_process.join()
