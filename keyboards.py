from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ===== Тексты кнопок (локализация интерфейса) =====
# Важно: это именно тексты кнопок, а не переводы ответов бота.
BUTTONS = {
    "feedback": {
        "RU": "📩 Обратная связь",
        "EN": "📩 Feedback",
        "UZ": "📩 Fikr-mulohaza",
        "TJ": "📩 Фикру мулоҳиза",
        "KG": "📩 Кайтарым байланыш",
    },
    "change_lang": {
        "RU": "🌐 Сменить язык",
        "EN": "🌐 Change language",
        "UZ": "🌐 Tilni o‘zgartirish",
        "TJ": "🌐 Забонро иваз кардан",
        "KG": "🌐 Тилди өзгөртүү",
    },
    "training": {
        "RU": "📚 Обучалки / FAQ",
        "EN": "📚 Training / FAQ",
        "UZ": "📚 O‘quv / FAQ",
        "TJ": "📚 Омӯзиш / FAQ",
        "KG": "📚 Окутуу / FAQ",
    },
    "faq": {
        "RU": "❓ FAQ",
        "EN": "❓ FAQ",
        "UZ": "❓ FAQ",
        "TJ": "❓ FAQ",
        "KG": "❓ FAQ",
    },
    "reminders": {
        "RU": "⏰ Напоминания",
        "EN": "⏰ Reminders",
        "UZ": "⏰ Eslatmalar",
        "TJ": "⏰ Ёдраскуниҳо",
        "KG": "⏰ Эскертмелер",
    },
    "contacts": {
        "RU": "📞 Контакты супервайзера",
        "EN": "📞 Supervisor contacts",
        "UZ": "📞 Supervayzer kontaktlari",
        "TJ": "📞 Тамосҳои супервайзер",
        "KG": "📞 Супервайзер байланыштары",
    },
    "links": {
        "RU": "🔗 Ссылки",
        "EN": "🔗 Links",
        "UZ": "🔗 Havolalar",
        "TJ": "🔗 Пайвандҳо",
        "KG": "🔗 Шилтемелер",
    },
    "back": {
        "RU": "⬅️ Назад",
        "EN": "⬅️ Back",
        "UZ": "⬅️ Orqaga",
        "TJ": "⬅️ Бозгашт",
        "KG": "⬅️ Артка",
    },
    "home": {
        "RU": "🏠 В меню",
        "EN": "🏠 Home",
        "UZ": "🏠 Bosh меню",
        "TJ": "🏠 Меню",
        "KG": "🏠 Башкы меню",
    },

    # под-меню "Напоминания"
    "rem_add": {
        "RU": "➕ Создать напоминание",
        "EN": "➕ New reminder",
        "UZ": "➕ Eslatma qo‘shish",
        "TJ": "➕ Ёдраскунии нав",
        "KG": "➕ Эскертме түзүү",
    },
    "daily_on": {
        "RU": "📅 Включить дайджест",
        "EN": "📅 Enable digest",
        "UZ": "📅 Dayjest yoqish",
        "TJ": "📅 Дайджестро фаъол кардан",
        "KG": "📅 Дайджестти күйгүзүү",
    },
    "daily_off": {
        "RU": "❌ Выключить дайджест",
        "EN": "❌ Disable digest",
        "UZ": "❌ Dayjest o‘chirish",
        "TJ": "❌ Дайджестро хомӯш кардан",
        "KG": "❌ Дайджестти өчүрүү",
    },

    "share_phone": {
        "RU": "📱 Отправить номер телефона",
        "EN": "📱 Share phone number",
        "UZ": "📱 Telefon raqamini yuborish",
        "TJ": "📱 Рақами телефонро фиристед",
        "KG": "📱 Телефон номерин жөнөтүү",
    },
}


def btn(lang: str, key: str) -> str:
    """Получить текст кнопки по языку. Если языка нет — вернём RU."""
    return BUTTONS.get(key, {}).get(lang, BUTTONS.get(key, {}).get("RU", key))


def all_btn_texts(key: str) -> set[str]:
    """Все возможные тексты кнопки (нужно для фильтров в хэндлерах)."""
    return set(BUTTONS.get(key, {}).values())

# ===== Выбор языка =====
def get_lang_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="RU"), KeyboardButton(text="EN")],
            [KeyboardButton(text="UZ"), KeyboardButton(text="TJ"), KeyboardButton(text="KG")]
        ],
        resize_keyboard=True
    )

# ===== Выбор роли =====
ROLE_LABELS = {
    "RU": {"courier": "Курьер", "picker": "Сборщик"},
    "EN": {"courier": "Courier", "picker": "Picker"},
    "UZ": {"courier": "Kuryer", "picker": "Yig‘uvchi"},
    "TJ": {"courier": "Курьер", "picker": "Ҷамъоварӣ"},
    "KG": {"courier": "Курьер", "picker": "Терүүчү"},
}

SHOP_LABELS = {
    # названия точек — обычно собственные, но дадим “человечные” подписи
    "RU": {"Бухарестская": "Бухарестская", "Бабушкина": "Бабушкина"},
    "EN": {"Бухарестская": "Bukharestskaya", "Бабушкина": "Babushkina"},
    "UZ": {"Бухарестская": "Buxarestskaya", "Бабушкина": "Babushkina"},
    "TJ": {"Бухарестская": "Бухарестская", "Бабушкина": "Бабушкина"},
    "KG": {"Бухарестская": "Бухарестская", "Бабушкина": "Бабушкина"},
}

def get_role_kb(lang: str = "RU"):
    labels = ROLE_LABELS.get(lang, ROLE_LABELS["RU"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=labels["courier"]), KeyboardButton(text=labels["picker"])]],
        resize_keyboard=True
    )

# ===== Выбор магазина =====
def get_shop_kb(lang: str = "RU"):
    labels = SHOP_LABELS.get(lang, SHOP_LABELS["RU"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=labels["Бухарестская"]), KeyboardButton(text=labels["Бабушкина"])]],
        resize_keyboard=True
    )

# ===== Главное меню пользователя =====
def main_menu(role, user_id, lang="RU"):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn(lang, "training"))],
            [KeyboardButton(text=btn(lang, "reminders"))],
            [KeyboardButton(text=btn(lang, "links"))],
            [KeyboardButton(text=btn(lang, "contacts"))],
            [KeyboardButton(text=btn(lang, "feedback"))],
            [KeyboardButton(text=btn(lang, "change_lang"))],
        ],
        resize_keyboard=True
    )
    return kb

# ===== Под-меню "Напоминания" =====
def reminders_menu(lang: str = "RU"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=btn(lang, "rem_add"))],
            [KeyboardButton(text=btn(lang, "daily_on")), KeyboardButton(text=btn(lang, "daily_off"))],
            [KeyboardButton(text=btn(lang, "back")), KeyboardButton(text=btn(lang, "home"))],
        ],
        resize_keyboard=True
    )

# ===== Обучалки =====
def get_training_kb(role: str, lang: str = "RU"):
    # (темы пока на RU — можно расширить позже, сейчас важно чтобы кнопки и навигация были живыми)
    if (role or "").lower() == "курьер":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Основные правила")],
                [KeyboardButton(text="Погрузка")],
                [KeyboardButton(text="Подключение терминала")],
                [KeyboardButton(text=btn(lang, "back")), KeyboardButton(text=btn(lang, "home"))]
            ],
            resize_keyboard=True
        )
    else:  # Сборщик
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Основные правила")],
                [KeyboardButton(text="Правила сборки")],
                [KeyboardButton(text="Возвраты")],
                [KeyboardButton(text="Закрытие точки")],
                [KeyboardButton(text=btn(lang, "back")), KeyboardButton(text=btn(lang, "home"))]
            ],
            resize_keyboard=True
        )
    return kb

# ===== Контакты супервайзера =====
SUPERVISOR_CONTACT = (
    "Контакт супервайзера:\n"
    "Мударов Ахмед\n"
    "Telegram: @get_w1ld\n"
    "Моб. номер: +79217666065\n"
    "Выходные: суббота и воскресенье\n\n"
    "Контакт старшей смены:\n"
    "Уткина Анна\n"
    "Telegram: @Annaytkina1994"
)

# ===== Ссылки по магазину =====

def get_links_text(shop):
    """Возвращает HTML-текст со ссылками (под parse_mode=HTML)."""
    def a(text: str, url: str) -> str:
        return f'<a href="{url}">{text}</a>'

    if shop == "Бабушкина":
        return (
            f"{a('Чат с сотрудниками магазина', 'https://t.me/+QQ0hPMMEZuhmYmFi')}\n"
            f"{a('Канал с новостями', 'https://t.me/+4yNEGoqcXwU2ZDky')}\n"
            f"{a('Чат самовывоза', 'https://t.me/+wCg1Tj5G-LQ1ZmIy')}\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot\n"
            f"{a('Партнерский портал', 'https://partner.kuper.ru/')}"
        )
    elif shop == "Бухарестская":
        return (
            f"{a('Чат с сотрудниками магазина', 'https://t.me/buharestscayg')}\n"
            f"{a('Канал с новостями', 'https://t.me/+4yNEGoqcXwU2ZDky')}\n"
            f"{a('Чат самовывоза', 'https://t.me/+M77ybMN2m08zNGUy')}\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot\n"
            f"{a('Партнерский портал', 'https://partner.kuper.ru/')}"
        )
    elif shop == "Комендантский":
        return (
            f"{a('Чат с сотрудниками магазина', 'https://t.me/+E5Ok9aVVqHc2MWIy')}\n"
            f"{a('Канал с новостями', 'https://t.me/+4yNEGoqcXwU2ZDky')}\n"
            f"{a('Чат самовывоза', 'https://t.me/+d8GZc2E4R7c3OGIy')}\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot\n"
            f"{a('Партнерский портал', 'https://partner.kuper.ru/')}"
        )
    elif shop == "Парнас":
        return (
            f"{a('Чат с сотрудниками магазина', 'https://t.me/+vzwyU4T4HfA5NmFi')}\n"
            f"{a('Канал с новостями', 'https://t.me/+4yNEGoqcXwU2ZDky')}\n"
            f"{a('Чат самовывоза', 'https://t.me/+v-qnHzWv7NQzZTIy')}\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot\n"
            f"{a('Партнерский портал', 'https://partner.kuper.ru/')}"
        )
    else:
        return (
            "Выберите точку при регистрации, чтобы получить ссылки.\n"
            f"{a('Партнерский портал', 'https://partner.kuper.ru/')}"
        )

def phone_request_kb(lang: str) -> ReplyKeyboardMarkup:
    """Клавиатура запроса контакта (Telegram Contact)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn(lang, "share_phone"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

