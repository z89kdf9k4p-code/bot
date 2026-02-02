import sqlite3

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    role TEXT,
    shop TEXT,
    lang TEXT DEFAULT 'RU'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()

def save_user(user_id, username, role=None, shop=None, lang="RU"):
    cursor.execute("""
    INSERT INTO users (user_id, username, role, shop, lang)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        role=COALESCE(excluded.role, users.role),
        shop=COALESCE(excluded.shop, users.shop),
        lang=COALESCE(excluded.lang, users.lang)
    """, (user_id, username, role, shop, lang))
    conn.commit()

def save_feedback(user_id, text):
    cursor.execute("INSERT INTO feedback (user_id, text) VALUES (?, ?)", (user_id, text))
    conn.commit()

def cleanup_feedback(days=30):
    cursor.execute("DELETE FROM feedback WHERE created_at <= datetime('now', ?)", (f'-{days} days',))
    conn.commit()
    