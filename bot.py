import asyncio
import logging
import os
import traceback
from datetime import datetime, timedelta

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from states import Register, FAQState, ReminderState
from keyboards import (
    main_menu,
    phone_request_kb,
    faq_menu,
    reminder_menu,
    home_back_kb,
)
import db


# -------------------------------------------------
# INIT
# -------------------------------------------------

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = {
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

router = Router()


# -------------------------------------------------
# HELPERS
# -------------------------------------------------


async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def push_nav(state: FSMContext, screen: str, payload: dict | None = None):
    data = await state.get_data()
    stack = data.get("nav_stack", [])
    stack.append((screen, payload or {}))
    await state.update_data(nav_stack=stack)


async def nav_back(message: Message, state: FSMContext):
    data = await state.get_data()
    stack = data.get("nav_stack", [])

    if len(stack) <= 1:
        await show_main_menu(message, state)
        return

    stack.pop()
    screen, payload = stack[-1]

    await state.update_data(nav_stack=stack)

    await render_screen(message, state, screen, payload)


async def render_screen(
    message: Message,
    state: FSMContext,
    screen: str,
    payload: dict | None = None,
):
    payload = payload or {}

    if screen == "main":
        await show_main_menu(message, state)

    elif screen == "faq":
        await show_faq_menu(message, state)

    elif screen == "reminder":
        await show_reminder_menu(message, state)


# -------------------------------------------------
# START / REGISTER
# -------------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):

    user = await db.get_user(message.from_user.id)

    if not user or not user.get("phone"):
        await state.set_state(Register.phone)
        await message.answer(
            "📱 Пожалуйста, отправьте номер телефона",
            reply_markup=phone_request_kb(),
        )
        return

    await show_main_menu(message, state)


@router.message(Register.phone, F.content_type == ContentType.CONTACT)
async def set_phone(message: Message, state: FSMContext):

    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer("❌ Отправьте свой номер")
        return

    await db.save_user(
        message.from_user.id,
        phone=contact.phone_number,
        name=message.from_user.full_name,
    )

    await state.clear()

    await message.answer("✅ Регистрация завершена")

    await show_main_menu(message, state)


# -------------------------------------------------
# MAIN MENU
# -------------------------------------------------


async def show_main_menu(message: Message, state: FSMContext):

    await state.clear()

    await state.update_data(nav_stack=[("main", {})])

    await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu(),
    )


@router.message(F.text == "⬅️ Назад")
async def back_btn(message: Message, state: FSMContext):
    await nav_back(message, state)


@router.message(F.text == "🏠 В меню")
async def home_btn(message: Message, state: FSMContext):
    await show_main_menu(message, state)


# -------------------------------------------------
# FAQ
# -------------------------------------------------


async def show_faq_menu(message: Message, state: FSMContext):

    await push_nav(state, "faq")

    await message.answer(
        "❓ Введите запрос для поиска",
        reply_markup=home_back_kb(),
    )

    await state.set_state(FAQState.search)


@router.message(F.text == "❓ FAQ")
async def open_faq(message: Message, state: FSMContext):
    await show_faq_menu(message, state)


@router.message(FAQState.search)
async def faq_search(message: Message, state: FSMContext):

    query = message.text.strip()

    results = await db.search_faq(query)

    if not results:
        await message.answer("❌ Ничего не найдено")
        return

    text = "📚 Результаты:\n\n"

    for r in results[:5]:
        text += f"🔹 <b>{r['title']}</b>\n{r['body']}\n\n"

    await message.answer(text, reply_markup=home_back_kb())


# -------------------------------------------------
# REMINDERS
# -------------------------------------------------


async def show_reminder_menu(message: Message, state: FSMContext):

    await push_nav(state, "reminder")

    await message.answer(
        "⏰ Напоминания",
        reply_markup=reminder_menu(),
    )


@router.message(F.text == "⏰ Напоминания")
async def open_reminder(message: Message, state: FSMContext):
    await show_reminder_menu(message, state)


@router.message(F.text == "➕ Создать напоминание")
async def create_reminder(message: Message, state: FSMContext):

    await message.answer("Через сколько минут напомнить?")

    await state.set_state(ReminderState.time)


@router.message(ReminderState.time)
async def reminder_time(message: Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("Введите число")
        return

    await state.update_data(minutes=int(message.text))

    await message.answer("Введите текст напоминания")

    await state.set_state(ReminderState.text)


@router.message(ReminderState.text)
async def reminder_text(message: Message, state: FSMContext):

    data = await state.get_data()

    minutes = data["minutes"]

    when = datetime.utcnow() + timedelta(minutes=minutes)

    await db.add_reminder(
        message.from_user.id,
        when,
        message.text,
    )

    await state.clear()

    await message.answer("✅ Напоминание сохранено")


# -------------------------------------------------
# ADMIN
# -------------------------------------------------


@router.message(Command("admin"))
async def admin_help(message: Message):

    if not await is_admin(message.from_user.id):
        return

    text = """
👑 Admin:

/stats
/users
/ban <id>
/unban <id>
/broadcast <text>

/faq_list
/faq_add title || body || tags
/faq_del id
/faq_edit id || title || body || tags
"""

    await message.answer(text)


@router.message(Command("stats"))
async def admin_stats(message: Message):

    if not await is_admin(message.from_user.id):
        return

    users = await db.count_users()

    await message.answer(f"👥 Пользователей: {users}")


@router.message(Command("broadcast"))
async def admin_broadcast(message: Message):

    if not await is_admin(message.from_user.id):
        return

    text = message.text.replace("/broadcast", "").strip()

    if not text:
        return

    users = await db.get_all_users()

    sent = 0

    for u in users:
        try:
            await message.bot.send_message(u["user_id"], text)
            sent += 1
        except:
            pass

    await message.answer(f"✅ Отправлено: {sent}")


# -------------------------------------------------
# FAQ ADMIN
# -------------------------------------------------


@router.message(Command("faq_list"))
async def faq_list(message: Message):

    if not await is_admin(message.from_user.id):
        return

    data = await db.get_all_faq()

    if not data:
        await message.answer("Пусто")
        return

    text = ""

    for i in data:
        text += f"{i['id']}. {i['title']}\n"

    await message.answer(text)


@router.message(Command("faq_add"))
async def faq_add(message: Message):

    if not await is_admin(message.from_user.id):
        return

    try:
        data = message.text.replace("/faq_add", "").strip()

        title, body, tags = [x.strip() for x in data.split("||")]

        await db.add_faq(title, body, tags)

        await message.answer("✅ Добавлено")

    except:
        await message.answer("Формат: /faq_add title || body || tags")


@router.message(Command("faq_del"))
async def faq_del(message: Message):

    if not await is_admin(message.from_user.id):
        return

    try:
        faq_id = int(message.text.split()[1])

        await db.delete_faq(faq_id)

        await message.answer("✅ Удалено")

    except:
        await message.answer("Формат: /faq_del id")


@router.message(Command("faq_edit"))
async def faq_edit(message: Message):

    if not await is_admin(message.from_user.id):
        return

    try:
        data = message.text.replace("/faq_edit", "").strip()

        parts = [x.strip() for x in data.split("||")]

        faq_id = int(parts[0])

        title = parts[1] if len(parts) > 1 else None
        body = parts[2] if len(parts) > 2 else None
        tags = parts[3] if len(parts) > 3 else None

        await db.edit_faq(faq_id, title, body, tags)

        await message.answer("✅ Обновлено")

    except:
        await message.answer("Формат: /faq_edit id || title || body || tags")


# -------------------------------------------------
# ERRORS
# -------------------------------------------------


@router.errors()
async def error_handler(event, exception):

    logger.error(exception)

    traceback.print_exc()


# -------------------------------------------------
# SCHEDULER
# -------------------------------------------------


async def scheduler_loop(bot: Bot):

    while True:

        try:
            reminders = await db.get_due_reminders()

            for r in reminders:

                await bot.send_message(
                    r["user_id"],
                    f"⏰ Напоминание:\n{r['text']}",
                )

                await db.delete_reminder(r["id"])

        except Exception as e:
            logger.error(e)

        await asyncio.sleep(30)


# -------------------------------------------------
# MAIN
# -------------------------------------------------


async def main():

    await db.init_db()

    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    asyncio.create_task(scheduler_loop(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
