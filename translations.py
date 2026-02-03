from db import get_user

# ===== Переводы (минимальный набор) =====
# Если ключа/языка нет — вернём сам ключ.
TRANSLATIONS = {
    "welcome": {
        "RU": "Добро пожаловать! Выберите язык 👇",
        "EN": "Welcome! Choose language 👇",
    },

    "phone_prompt": {
        "RU": "Для регистрации отправьте номер телефона кнопкой ниже 👇",
        "EN": "To register, share your phone number using the button below 👇",
    },
    "share_phone": {
        "RU": "📱 Отправить номер телефона",
        "EN": "📱 Share phone number",
    },
    "phone_saved": {
        "RU": "✅ Номер сохранён.",
        "EN": "✅ Phone number saved.",
    },
    "phone_invalid": {
        "RU": "Пожалуйста, отправьте номер через кнопку «Отправить номер телефона».",
        "EN": "Please share your phone using the button.",
    },
    "role_prompt": {"RU": "Выберите вашу роль:", "EN": "Choose your role:"},
    "role_confirm": {"RU": "Ваша роль подтверждена:", "EN": "Your role is confirmed:"},
    "help": {"RU": "Выберите действие в меню 👇", "EN": "Choose an action in the menu 👇"},
    "lang_updated": {"RU": "Язык успешно обновлён!", "EN": "Language updated successfully!"},
    "choose_language": {"RU": "Выберите язык:", "EN": "Choose a language:"},
    "feedback": {"RU": "Отправьте ваш отзыв одним сообщением:", "EN": "Send your feedback in one message:"},
    "feedback_thanks": {"RU": "Спасибо! Отзыв записан ✅", "EN": "Thanks! Feedback saved ✅"},
    "choose_shop": {"RU": "Выберите вашу торговую точку:", "EN": "Select your shop:"},

    "faq_prompt": {"RU": "Напишите, что хотите найти в FAQ (например: «терминал», «возврат»):", "EN": "Type what you want to find in FAQ:"},
    "faq_not_found": {"RU": "Ничего не нашёл. Попробуйте другими словами.", "EN": "Nothing found. Try different words."},

    "reminders_menu": {"RU": "Выберите действие с напоминаниями:", "EN": "Choose a reminders action:"},
    "reminder_ask_minutes": {"RU": "Через сколько минут напомнить? (число)", "EN": "In how many minutes? (number)"},
    "reminder_ask_text": {"RU": "Что напомнить? (текст одним сообщением)", "EN": "What should I remind you? (one message)"},
    "reminder_set": {"RU": "Ок! Напоминание поставлено ✅", "EN": "Ok! Reminder is set ✅"},
    "daily_on": {"RU": "Ежедневный дайджест включён ✅", "EN": "Daily digest enabled ✅"},
    "daily_off": {"RU": "Ежедневный дайджест выключен ✅", "EN": "Daily digest disabled ✅"},

    "banned": {"RU": "⛔ Вам недоступен бот. Свяжитесь с администратором.", "EN": "⛔ You are banned. Contact admin."},
}

def tr(key: str, user_id: int | None = None) -> str:
    lang = "RU"
    if user_id is not None:
        user = get_user(user_id)
        if user and user[4]:
            lang = user[4]
    return TRANSLATIONS.get(key, {}).get(lang, key)

def get_user_lang(user_id: int) -> str:
    user = get_user(user_id)
    if user and user[4]:
        return user[4]
    return "RU"
