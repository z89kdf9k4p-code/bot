import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import get_user, get_all_users, save_user, save_feedback, cleanup_feedback
from states import LanguageState, Register, FeedbackState
from keyboards import (
    get_lang_kb, get_role_kb, get_shop_kb, main_menu,
    get_training_kb, SUPERVISOR_CONTACT, get_links_text
)
from translations import tr, get_user_lang

BOT_TOKEN = "8413248579:AAH_AuRcm3yLP6O38w6z-O_SmUq9pZDviHA"
ADMINS = {1242801964}

CHANGE_LANG_BUTTONS = {
    "RU": "🌐 Сменить язык",
    "EN": "🌐 Change language",
    "UZ": "🌐 Tilni o‘zgartirish",
    "TJ": "🌐 Забывает язык_TJ",
    "KG": "🌐 Смена языка_KG"
}

def is_admin(user_id):
    return user_id in ADMINS

# ===== Хэндлеры =====
async def start(message: Message, state: FSMContext):
    await state.clear()
    cleanup_feedback(message.from_user.id)
    user = get_user(message.from_user.id)
    if not user:
        await message.answer(tr("welcome"), reply_markup=get_lang_kb())
        await state.set_state(LanguageState.lang)
        return
    role, shop, lang = user[2], user[3], user[4]
    if role and shop:
        await message.answer(
            f"{tr('role_confirm', user_id=message.from_user.id)} {role}, ТТ: {shop}\n"
            f"{tr('help', user_id=message.from_user.id)}",
            reply_markup=main_menu(role, message.from_user.id, lang)
        )
    else:
        await message.answer(tr("role_prompt", user_id=message.from_user.id), reply_markup=get_role_kb(lang))
        await state.set_state(Register.role)

async def change_language(message: Message, state: FSMContext):
    if message.text not in CHANGE_LANG_BUTTONS.values():
        return
    await message.answer(tr("choose_language", user_id=message.from_user.id), reply_markup=get_lang_kb())
    await state.set_state(LanguageState.lang)

async def set_language(message: Message, state: FSMContext):
    text = message.text.strip().upper()
    if text not in {"RU", "EN", "UZ", "TJ", "KG"}:
        await message.answer("Пожалуйста, выбери язык с кнопок 👇", reply_markup=get_lang_kb())
        return
    user = get_user(message.from_user.id)
    save_user(message.from_user.id, message.from_user.username,
              role=user[2] if user else None,
              shop=user[3] if user else None,
              lang=text)
    await state.clear()
    user = get_user(message.from_user.id)
    role, shop, lang = user[2], user[3], user[4]
    if role and shop:
        await message.answer(
            f"{tr('role_confirm', user_id=message.from_user.id)} {role}, ТТ: {shop}\n"
            f"{tr('help', user_id=message.from_user.id)}",
            reply_markup=main_menu(role, message.from_user.id, lang)
        )
    else:
        await message.answer(tr("role_prompt", user_id=message.from_user.id), reply_markup=get_role_kb(lang))
        await state.set_state(Register.role)

async def set_role(message: Message, state: FSMContext):
    user_lang = get_user_lang(message.from_user.id)
    await state.update_data(role=message.text)
    await message.answer(tr("choose_shop", user_id=message.from_user.id), reply_markup=get_shop_kb(user_lang))
    await state.set_state(Register.shop)

async def set_shop(message: Message, state: FSMContext):
    user_lang = get_user_lang(message.from_user.id)
    data = await state.get_data()
    role = data.get("role")
    shop = message.text
    save_user(message.from_user.id, message.from_user.username, role=role, shop=shop, lang=user_lang)
    await message.answer(
        f"{tr('role_confirm', user_id=message.from_user.id)} {role}, ТТ: {shop}. {tr('help', user_id=message.from_user.id)}",
        reply_markup=main_menu(role, message.from_user.id, user_lang)
    )
    await state.clear()

async def feedback_start(message: Message, state: FSMContext):
    await message.answer(tr("feedback", user_id=message.from_user.id))
    await state.set_state(FeedbackState.text)

async def save_feedback_handler(message: Message, state: FSMContext):
    save_feedback(message.from_user.id, message.text)
    await message.answer(tr("feedback_thanks", user_id=message.from_user.id))
    await state.clear()

async def training_menu(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    role = user[2] if user else "Курьер"
    await message.answer("Выберите тему обучения:", reply_markup=get_training_kb(role))

async def show_supervisor_contacts(message: Message):
    await message.answer(SUPERVISOR_CONTACT)

async def show_links(message: Message):
    user = get_user(message.from_user.id)
    shop = user[3] if user else None
    await message.answer(get_links_text(shop), parse_mode="Markdown")

# ===== Admin =====
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    users = get_all_users()
    text = f"Всего пользователей: {len(users)}\n"
    for u in users:
        text += f"ID: {u[0]}, Lang: {u[4]}, Role: {u[2]}, Shop: {u[3]}\n"
    await message.answer(text)

async def admin_cleanup_feedback(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    cleanup_feedback()
    await message.answer("✅ Все фидбэки очищены")

async def admin_list_users(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    users = get_all_users()
    text = "Список пользователей:\n"
    for u in users:
        text += f"ID: {u[0]}, Lang: {u[4]}, Role: {u[2]}, Shop: {u[3]}\n"
    await message.answer(text)

async def admin_edit_user(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    try:
        parts = message.text.split(maxsplit=3)
        user_id = int(parts[1])
        field = parts[2].lower()
        value = parts[3]
    except:
        return await message.answer("❌ Использование: /edit_user <id> <role/shop/lang> <value>")
    user = get_user(user_id)
    if not user:
        return await message.answer("❌ Пользователь не найден")
    if field == "role":
        save_user(user_id, user[1], role=value, shop=user[3], lang=user[4])
    elif field == "shop":
        save_user(user_id, user[1], role=user[2], shop=value, lang=user[4])
    elif field == "lang":
        save_user(user_id, user[1], role=user[2], shop=user[3], lang=value)
    else:
        return await message.answer("❌ Поле должно быть role, shop или lang")
    await message.answer(f"✅ Пользователь {user_id} обновлён")

async def admin_broadcast(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    try:
        text = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.answer("❌ Использование: /broadcast <текст>")
    users = get_all_users()
    for u in users:
        try:
            await bot.send_message(u[0], text)
        except:
            pass
    await message.answer("✅ Сообщение отправлено всем пользователям")

# ===== Запуск =====
async def main():
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start, Command("start"))
    dp.message.register(change_language, lambda m: m.text in CHANGE_LANG_BUTTONS.values())
    dp.message.register(set_language, StateFilter(LanguageState.lang))
    dp.message.register(set_role, StateFilter(Register.role))
    dp.message.register(set_shop, StateFilter(Register.shop))
    dp.message.register(feedback_start, F.text.contains("Обратная"))
    dp.message.register(save_feedback_handler, StateFilter(FeedbackState.text))

    dp.message.register(training_menu, F.text == "📚 Обучалки")
    dp.message.register(show_supervisor_contacts, F.text == "📞 Контакты супервайзера")
    dp.message.register(show_links, F.text == "🔗 Ссылки")

    dp.message.register(admin_stats, Command(commands=["stats"]))
    dp.message.register(admin_cleanup_feedback, Command(commands=["cleanup"]))
    dp.message.register(admin_list_users, Command(commands=["users"]))
    dp.message.register(admin_edit_user, Command(commands=["edit_user"]))
    dp.message.register(lambda m: admin_broadcast(m, bot), Command(commands=["broadcast"]))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
