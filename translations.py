# Простейшая структура переводов
# Здесь можно расширить под любые ключи и языки
TRANSLATIONS = {
    "welcome": {
        "RU": "Добро пожаловать!",
        "EN": "Welcome!",
    },
    "role_prompt": {
        "RU": "Выберите вашу роль:",
        "EN": "Choose your role:"
    },
    "role_confirm": {
        "RU": "Ваша роль подтверждена:",
        "EN": "Your role is confirmed:"
    },
    "help": {
        "RU": "Используйте меню ниже для работы с ботом",
        "EN": "Use the menu below to work with the bot"
    },
    "lang_updated": {
        "RU": "Язык успешно обновлён!",
        "EN": "Language updated successfully!"
    },
    "choose_language": {
        "RU": "Выберите язык:",
        "EN": "Choose a language:"
    },
    "feedback": {
        "RU": "Отправьте ваш отзыв:",
        "EN": "Send your feedback:"
    },
    "feedback_thanks": {
        "RU": "Спасибо за ваш отзыв!",
        "EN": "Thank you for your feedback!"
    },
    "choose_shop": {
        "RU": "Выберите вашу торговую точку:",
        "EN": "Select your shop:"
    },
    "change_lang": {
        "RU": "Сменить язык",
        "EN": "Change language"
    }
}

def tr(key, user_id=None):
    # Берём язык пользователя
    from db import get_user
    lang = "RU"
    if user_id:
        user = get_user(user_id)
        if user and user[4]:
            lang = user[4]
    return TRANSLATIONS.get(key, {}).get(lang, key)
