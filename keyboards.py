from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# ===== ЯЗЫКИ =====
LANG_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="RU"), KeyboardButton(text="EN")],
        [KeyboardButton(text="UZ"), KeyboardButton(text="TJ"), KeyboardButton(text="KG")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


# ===== РОЛИ =====
ROLE_COURIER = "Курьер"
ROLE_PICKER = "Сборщик"

ROLE_BUTTONS = {ROLE_COURIER, ROLE_PICKER}

role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=ROLE_COURIER),
            KeyboardButton(text=ROLE_PICKER),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


# ===== МАГАЗИНЫ =====
SHOP_BUCHAREST = "Бухарестская"
SHOP_BABUSHKINA = "Бабушкина"

SHOP_BUTTONS = {SHOP_BUCHAREST, SHOP_BABUSHKINA}

shop_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=SHOP_BUCHAREST),
            KeyboardButton(text=SHOP_BABUSHKINA),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


# ===== ГЛАВНОЕ МЕНЮ =====
def main_menu(role: str, user_id: int):
    buttons = []

    if role == ROLE_COURIER:
        buttons.append([KeyboardButton(text="📦 Мои доставки")])

    if role == ROLE_PICKER:
        buttons.append([KeyboardButton(text="🛒 Мои сборки")])

    buttons.extend(
        [
            [KeyboardButton(text="💬 Обратная связь")],
            [KeyboardButton(text="🌐 Сменить язык")],
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
