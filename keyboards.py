from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ===== ЯЗЫКИ =====
def get_lang_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("RU"), KeyboardButton("EN")],
            [KeyboardButton("UZ"), KeyboardButton("TJ"), KeyboardButton("KG")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ===== РОЛИ =====
ROLE_MAP = {
    "RU": ["Курьер", "Сборщик"],
    "EN": ["Courier", "Picker"],
    "UZ": ["Yetkazuvchi", "Tarkibchi"],
    "TJ": ["Курьер_TJ", "Сборщик_TJ"],
    "KG": ["Курьер_KG", "Сборщик_KG"]
}

def get_role_kb(lang: str):
    roles = ROLE_MAP.get(lang, ROLE_MAP["RU"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=r) for r in roles]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

ROLE_BUTTONS = set(sum(ROLE_MAP.values(), []))

# ===== МАГАЗИНЫ =====
SHOP_MAP = {
    "RU": ["Бухарестская", "Бабушкина"],
    "EN": ["Bucharest", "Babushkina"],
    "UZ": ["Buxarest", "Bobo"],
    "TJ": ["Бухарестская_TJ", "Бабушкина_TJ"],
    "KG": ["Бухарестская_KG", "Бабушкина_KG"]
}

def get_shop_kb(lang: str):
    shops = SHOP_MAP.get(lang, SHOP_MAP["RU"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=s) for s in shops]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

SHOP_BUTTONS = set(sum(SHOP_MAP.values(), []))

# ===== ГЛАВНОЕ МЕНЮ =====
def main_menu(role: str, user_id: int, lang: str):
    buttons = []

    # Основные кнопки по роли
    buttons.append([KeyboardButton("📦 Мои доставки")])
    buttons.append([KeyboardButton("💬 Обратная связь")])
    buttons.append([KeyboardButton("🌐 Сменить язык")])
    buttons.append([KeyboardButton("📚 Обучалки")])
    buttons.append([KeyboardButton("📞 Контакты супервайзера")])
    buttons.append([KeyboardButton("🔗 Ссылки")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

# ===== ОБУЧАЛКИ =====
def get_training_kb(role: str):
    if role.lower() == "курьер" or role.lower() == "courier":
        buttons = [
            [KeyboardButton("📌 Основные правила")],
            [KeyboardButton("🚚 Погрузка")],
            [KeyboardButton("🔌 Подключение терминала")],
            [KeyboardButton("⬅️ Назад")]
        ]
    else:  # Сборщик / Picker
        buttons = [
            [KeyboardButton("📌 Основные правила")],
            [KeyboardButton("🛒 Правила сборки")],
            [KeyboardButton("🔄 Возвраты")],
            [KeyboardButton("🏁 Закрытие точки")],
            [KeyboardButton("⬅️ Назад")]
        ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

# ===== КОНТАКТЫ СУПЕРВАЙЗЕРА =====
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

# ===== ССЫЛКИ ПО МАГАЗИНАМ =====
def get_links_text(shop: str):
    if shop == "Бабушкина":
        return (
            "Ссылка на чат с сотрудниками магазина: [ссылка](https://t.me/+QQ0hPMMEZuhmYmFi)\n"
            "Канал с новостями: [ссылка](https://t.me/+4yNEGoqcXwU2ZDky)\n"
            "Чат самовывоза: [ссылка](https://t.me/+wCg1Tj5G-LQ1ZmIy)\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot 🤩\n"
            "Партнерский портал: [ссылка](https://partner.kuper.ru/)"
        )
    elif shop == "Бухарестская":
        return (
            "Ссылка на чат с сотрудниками магазина: [ссылка](https://t.me/buharestscayg)\n"
            "Канал с новостями: [ссылка](https://t.me/+4yNEGoqcXwU2ZDky)\n"
            "Чат самовывоза: [ссылка](https://t.me/+M77ybMN2m08zNGUy)\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot 🤩\n"
            "Партнерский портал: [ссылка](https://partner.kuper.ru/)"
        )
    else:
        return "Ссылки недоступны для вашей торговой точки."
