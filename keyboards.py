from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from translations import tr, get_user_lang

LANG_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("RU"), KeyboardButton("EN")],
        [KeyboardButton("UZ"), KeyboardButton("TJ"), KeyboardButton("KG")]
    ],
    resize_keyboard=True
)

role_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Курьер"), KeyboardButton("Сборщик")]],
    resize_keyboard=True
)

shop_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton("Бухарестская"), KeyboardButton("Бабушкина")]],
    resize_keyboard=True
)

def main_menu(role, user_id=None):
    lang = get_user_lang(user_id)
    buttons = [
        [KeyboardButton(tr("training", lang))],
        [KeyboardButton(tr("urgent_problem", lang))],
        [KeyboardButton(tr("supervisor_contacts", lang))],
        [KeyboardButton(tr("chat_links", lang))],
        [KeyboardButton(tr("feedback", lang))],
        [KeyboardButton(tr("change_lang", lang) + " 🌐")]
    ]
    if role == "сборщик":
        buttons.insert(1, [KeyboardButton(tr("assembly_rating", lang))])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)