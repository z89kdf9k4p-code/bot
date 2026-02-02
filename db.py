_users = {}
_feedbacks = {}

def get_user(user_id):
    return _users.get(user_id)

def get_all_users():
    return list(_users.values())

def save_user(user_id, username, role=None, shop=None, lang=None):
    _users[user_id] = (user_id, username, role, shop, lang)

def save_feedback(user_id, text):
    _feedbacks[user_id] = text

def cleanup_feedback(user_id=None):
    if user_id:
        _feedbacks.pop(user_id, None)
    else:
        _feedbacks.clear()
