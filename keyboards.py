from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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
def get_role_kb(lang="RU"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Курьер"), KeyboardButton(text="Сборщик")]
        ],
        resize_keyboard=True
    )

# ===== Выбор магазина =====
def get_shop_kb(lang="RU"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Бухарестская"), KeyboardButton(text="Бабушкина")]
        ],
        resize_keyboard=True
    )

# ===== Главное меню пользователя =====
def main_menu(role, user_id, lang="RU"):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Мои доставки")],
            [KeyboardButton(text="📩 Обратная связь")],
            [KeyboardButton(text="🌐 Сменить язык")],
            [KeyboardButton(text="📚 Обучалки")],
            [KeyboardButton(text="📞 Контакты супервайзера")],
            [KeyboardButton(text="🔗 Ссылки")]
        ],
        resize_keyboard=True
    )
    return kb

# ===== Обучалки =====
def get_training_kb(role):
    if role.lower() == "курьер":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Основные правила")],
                [KeyboardButton(text="Погрузка")],
                [KeyboardButton(text="Подключение терминала")],
                [KeyboardButton(text="⬅️ Назад")]
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
                [KeyboardButton(text="⬅️ Назад")]
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
    if shop == "Бабушкина":
        return (
            "[Ссылка на чат с сотрудниками магазина](https://t.me/+QQ0hPMMEZuhmYmFi)\n"
            "[Канал с новостями](https://t.me/+4yNEGoqcXwU2ZDky)\n"
            "[Чат самовывоза](https://t.me/+wCg1Tj5G-LQ1ZmIy)\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot\n"
            "[Партнерский портал](https://partner.kuper.ru/)"
        )
    elif shop == "Бухарестская":
        return (
            "[Ссылка на чат с сотрудниками магазина](https://t.me/buharestscayg)\n"
            "[Канал с новостями](https://t.me/+4yNEGoqcXwU2ZDky)\n"
            "[Чат самовывоза](https://t.me/+M77ybMN2m08zNGUy)\n"
            "Горячая линия для партнеров: +7 800 333-24-28\n"
            "Бот КУПЕР: @SM_courierinfo_bot\n"
            "[Партнерский портал](https://partner.kuper.ru/)"
        )
    else:
        return "Ссылки недоступны для вашей точки"
