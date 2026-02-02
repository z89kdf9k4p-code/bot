# ===== Простейшая "БД" в памяти =====
users_db = {}
feedback_db = []

def get_user(user_id):
    return users_db.get(user_id)

def save_user(user_id, username, role=None, shop=None, lang="RU"):
    users_db[user_id] = (user_id, username, role, shop, lang)

def save_feedback(user_id, text):
    feedback_db.append((user_id, text))

def cleanup_feedback(user_id=None):
    global feedback_db
    if user_id:
        feedback_db = [f for f in feedback_db if f[0] != user_id]
    else:
        feedback_db = []

def get_all_users():
    return list(users_db.values())
