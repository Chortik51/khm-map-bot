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
