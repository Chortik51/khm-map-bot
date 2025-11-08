from flask import Flask, request, jsonify, render_template
import sqlite3, time, threading, os

app = Flask(__name__)
DB_FILE = "markers.db"

# ---------- Инициализация базы ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            timestamp REAL,
            user_id TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- Главная страница ----------
@app.route("/")
def index():
    return render_template("map.html")

# ---------- Получить метки ----------
@app.route("/api/markers", methods=["POST"])
def get_markers():
    data = request.json or {}
    user_id = data.get("user_id", "")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, lat, lon, timestamp, user_id FROM markers")
    rows = c.fetchall()
    conn.close()

    now = time.time()
    markers = []
    for row in rows:
        if now - row[3] <= 1200:  # 20 минут
            markers.append({
                "id": row[0],
                "lat": row[1],
                "lon": row[2],
                "timestamp": row[3],
                "is_owner": (row[4] == user_id)
            })
    return jsonify(markers)

# ---------- Добавить метку ----------
@app.route("/api/add_marker", methods=["POST"])
def add_marker():
    data = request.json
    lat = data.get("lat")
    lon = data.get("lon")
    user_id = data.get("user_id")
    ts = time.time()

    if not all([lat, lon, user_id]):
        return jsonify({"error": "missing fields"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO markers (lat, lon, timestamp, user_id) VALUES (?, ?, ?, ?)",
        (lat, lon, ts, user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

# ---------- Удалить метку (только свою) ----------
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

# ---------- Автоочистка старых меток ----------
def cleanup_old():
    while True:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM markers WHERE strftime('%s','now') - timestamp > 1200")
        conn.commit()
        conn.close()
        time.sleep(60)

threading.Thread(target=cleanup_old, daemon=True).start()

# ---------- Запуск ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
