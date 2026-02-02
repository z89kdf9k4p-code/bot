from db import get_user

# ===== Словарь переводов =====
TRANSLATIONS = {
    "welcome": {"RU": "Добро пожаловать!", "EN": "Welcome!"},
    "role_prompt": {"RU": "Выберите вашу роль:", "EN": "Choose your role:"},
    "role_confirm": {"RU": "Ваша роль подтверждена:", "EN": "Your role is confirmed:"},
    "help": {"RU": "Используйте меню ниже для работы с ботом", "EN": "Use the menu below to work with the bot"},
    "lang_updated": {"RU": "Язык успешно обновлён!", "EN": "Language updated successfully!"},
    "choose_language": {"RU": "Выберите язык:", "EN": "Choose a language:"},
    "feedback": {"RU": "Отправьте ваш отзыв:", "EN": "Send your feedback:"},
    "feedback_thanks": {"RU": "Спасибо за ваш отзыв!", "EN": "Thank you for your feedback!"},
    "choose_shop": {"RU": "Выберите вашу торговую точку:", "EN": "Select your shop:"},
    "change_lang": {"RU": "Сменить язык", "EN": "Change language"}
}

# ===== Функция для перевода =====
def tr(key, user_id=None):
    """Возвращает перевод строки по ключу и языку пользователя"""
    lang = "RU"
    if user_id:
        user = get_user(user_id)
        if user and user[4]:
            lang = user[4]
    return TRANSLATIONS.get(key, {}).get(lang, key)

# ===== Новая функция для получения языка пользователя =====
def get_user_lang(user_id):
    """Возвращает язык пользователя из базы, по умолчанию 'RU'"""
    user = get_user(user_id)
    if user and user[4]:
        return user[4]
    return "RU"
