import asyncio
import logging
import os
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.error_event import ErrorEvent
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import (
    init_db, close_db,
    get_user, get_all_users, save_user,
    save_feedback, cleanup_feedback,
    is_banned, ban_user, unban_user,
    add_reminder, pop_due_reminders,
    enable_daily_digest, get_daily_digest_users,
    set_daily_digest_message, get_daily_digest_message,
    search_faq,
)
from states import LanguageState, Register, FeedbackState, FAQState, ReminderState
from keyboards import (
    get_lang_kb, get_role_kb, get_shop_kb, main_menu,
    get_training_kb, SUPERVISOR_CONTACT, get_links_text,
    all_btn_texts, btn, reminders_menu, phone_request_kb,
)
from translations import tr, get_user_lang

# =========================
# Настройки
# =========================
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8413248579:AAH_AuRcm3yLP6O38w6z-O_SmUq9pZDviHA")
ADMINS = {1242801964}

TZ = ZoneInfo("Asia/Seoul")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("bot")


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


# =========================
# Навигация (Back/Home)
# =========================
ROOT_SCREEN = "main"

def _nav_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn(lang, "back")), KeyboardButton(text=btn(lang, "home"))]],
        resize_keyboard=True
    )

async def nav_reset(state: FSMContext):
    await state.update_data(nav_stack=[ROOT_SCREEN])

async def nav_push(state: FSMContext, screen: str):
    data = await state.get_data()
    stack = data.get("nav_stack") or [ROOT_SCREEN]
    if stack and stack[-1] == screen:
        return
    stack.append(screen)
    await state.update_data(nav_stack=stack)

async def nav_pop(state: FSMContext) -> str:
    data = await state.get_data()
    stack = data.get("nav_stack") or [ROOT_SCREEN]
    if len(stack) <= 1:
        return ROOT_SCREEN
    stack.pop()
    await state.update_data(nav_stack=stack)
    return stack[-1] if stack else ROOT_SCREEN

async def nav_current(state: FSMContext) -> str:
    data = await state.get_data()
    stack = data.get("nav_stack") or [ROOT_SCREEN]
    return stack[-1] if stack else ROOT_SCREEN


# =========================
# Рендер экранов
# =========================
async def render_main(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    if not user:
        # нет пользователя → старт регистрации
        await message.answer(tr("welcome"), reply_markup=get_lang_kb())
        await state.set_state(LanguageState.lang)
        return

    role, shop, lang, phone = user[2], user[3], user[4], (user[5] if len(user) > 5 else None)
    await nav_reset(state)

    if not phone:
        await message.answer(tr("phone_prompt", user_id=message.from_user.id), reply_markup=phone_request_kb(lang))
        await state.set_state(Register.phone)
        return

    if role and shop:
        await message.answer(
            f"{tr('role_confirm', user_id=message.from_user.id)} {role}, ТТ: {shop}\n{tr('help', user_id=message.from_user.id)}",
            reply_markup=main_menu(role, message.from_user.id, lang)
        )
    else:
        await message.answer(tr("role_prompt", user_id=message.from_user.id), reply_markup=get_role_kb(lang))
        await state.set_state(Register.role)

async def render_training(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    role = user[2] if user else "Курьер"
    lang = get_user_lang(message.from_user.id)
    await message.answer("Выберите тему обучения:", reply_markup=get_training_kb(role, lang))

async def render_faq(message: Message, state: FSMContext):
    lang = get_user_lang(message.from_user.id)
    await message.answer(tr("faq_prompt", user_id=message.from_user.id), reply_markup=_nav_kb(lang))
    await state.set_state(FAQState.query)

async def render_reminders(message: Message, state: FSMContext):
    lang = get_user_lang(message.from_user.id)
    await message.answer(tr("reminders_menu", user_id=message.from_user.id), reply_markup=reminders_menu(lang))
    await state.clear()


# =========================
# Guards
# =========================
async def guard_ban(message: Message) -> bool:
    if is_banned(message.from_user.id):
        await message.answer(tr("banned", user_id=message.from_user.id))
        return True
    return False


# =========================
# Хэндлеры (регистрация)
# =========================
async def start(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await cleanup_feedback(message.from_user.id)
    await render_main(message, state)


async def change_language(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    if (message.text or "").strip() not in all_btn_texts("change_lang"):
        return
    await message.answer(tr("choose_language", user_id=message.from_user.id), reply_markup=get_lang_kb())
    await state.set_state(LanguageState.lang)


async def set_language(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    text = (message.text or "").strip().upper()
    if text not in {"RU", "EN", "UZ", "TJ", "KG"}:
        await message.answer("Пожалуйста, выбери язык с кнопок 👇", reply_markup=get_lang_kb())
        return
    user = get_user(message.from_user.id)
    await save_user(
        message.from_user.id,
        message.from_user.username,
        role=user[2] if user else None,
        shop=user[3] if user else None,
        lang=text,
        phone=(user[5] if user and len(user) > 5 else None),
    )
    await render_main(message, state)




async def set_phone(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    user_lang = get_user_lang(message.from_user.id)

    if not message.contact or not message.contact.phone_number:
        await message.answer(tr("phone_invalid", user_id=message.from_user.id), reply_markup=phone_request_kb(user_lang))
        return

    # защита: принимаем контакт только самого пользователя
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer(tr("phone_invalid", user_id=message.from_user.id), reply_markup=phone_request_kb(user_lang))
        return

    phone = message.contact.phone_number
    user = get_user(message.from_user.id)
    role = user[2] if user else None
    shop = user[3] if user else None
    lang = user[4] if user else user_lang

    await save_user(message.from_user.id, message.from_user.username, role=role, shop=shop, lang=lang, phone=phone)
    await message.answer(tr("phone_saved", user_id=message.from_user.id))
    await render_main(message, state)


async def set_role(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    user_lang = get_user_lang(message.from_user.id)
    await state.update_data(role=(message.text or "").strip())
    await message.answer(tr("choose_shop", user_id=message.from_user.id), reply_markup=get_shop_kb(user_lang))
    await state.set_state(Register.shop)


async def set_shop(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    user_lang = get_user_lang(message.from_user.id)
    data = await state.get_data()
    role = data.get("role")
    shop = (message.text or "").strip()
    user = get_user(message.from_user.id)
    await save_user(message.from_user.id, message.from_user.username, role=role, shop=shop, lang=user_lang, phone=(user[5] if user and len(user) > 5 else None))
    await render_main(message, state)


# =========================
# Обратная связь
# =========================
async def feedback_start(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await nav_push(state, "feedback")
    await message.answer(tr("feedback", user_id=message.from_user.id), reply_markup=_nav_kb(get_user_lang(message.from_user.id)))
    await state.set_state(FeedbackState.text)


async def save_feedback_handler(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await save_feedback(message.from_user.id, message.text or "")
    await message.answer(tr("feedback_thanks", user_id=message.from_user.id))
    # после фидбэка — назад в главное меню
    await render_main(message, state)


# =========================
# Обучалки
# =========================
async def training_menu(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await nav_push(state, "training")
    await render_training(message, state)


async def training_topic(message: Message):
    """Простейшие ответы на темы обучения. Функцию не вырезаем — расширять можно позже."""
    topic = (message.text or "").strip()
    topics = {
        "Основные правила": (
            "• Всегда проверяйте адрес/комментарии к заказу\n"
            "• Соблюдайте технику безопасности\n"
            "• В спорных ситуациях пишите супервайзеру"
        ),
        "Погрузка": (
            "• Проверяйте целостность упаковки\n"
            "• Тяжёлое — вниз, хрупкое — вверх\n"
            "• Не оставляйте заказ без присмотра"
        ),
        "Подключение терминала": (
            "• Включите терминал и проверьте заряд\n"
            "• Убедитесь, что есть связь/интернет\n"
            "• При ошибках — перезапуск и обращение к супервайзеру"
        ),
        "Правила сборки": (
            "• Сверяйте позиции по приложению\n"
            "• Следите за сроками годности\n"
            "• Холодное/заморозку — в конце"
        ),
        "Возвраты": (
            "• Фиксируйте причину возврата\n"
            "• Делайте фото при повреждении\n"
            "• Действуйте по регламенту точки"
        ),
        "Закрытие точки": (
            "• Закройте все активные процессы\n"
            "• Сверьте остатки/инвентарь (если применимо)\n"
            "• Сообщите старшей смены о завершении"
        ),
    }
    text = topics.get(topic)
    if text:
        await message.answer(text)


# =========================
# FAQ / база знаний
# =========================
async def faq_menu(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await nav_push(state, "faq")
    await render_faq(message, state)


async def faq_search(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    q = (message.text or "").strip()
    lang = get_user_lang(message.from_user.id)
    results = search_faq(q)
    if not results:
        await message.answer(tr("faq_not_found", user_id=message.from_user.id), reply_markup=_nav_kb(lang))
        return
    # выдаём топ-результаты
    blocks = []
    for art in results:
        blocks.append(f"**{art['title']}**\n{art['body']}")
    await message.answer("\n\n".join(blocks), parse_mode="Markdown", reply_markup=_nav_kb(lang))


# =========================
# Напоминания + дайджест
# =========================
async def reminders_entry(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await nav_push(state, "reminders")
    await render_reminders(message, state)


async def reminder_add_start(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    lang = get_user_lang(message.from_user.id)
    await message.answer(tr("reminder_ask_minutes", user_id=message.from_user.id), reply_markup=_nav_kb(lang))
    await state.set_state(ReminderState.minutes)


async def reminder_set_minutes(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    try:
        minutes = int((message.text or "").strip())
        if minutes <= 0 or minutes > 60 * 24 * 14:  # максимум 14 дней
            raise ValueError
    except ValueError:
        return await message.answer("Введите число минут (1..20160).")
    await state.update_data(minutes=minutes)
    await message.answer(tr("reminder_ask_text", user_id=message.from_user.id))
    await state.set_state(ReminderState.text)


async def reminder_set_text(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    data = await state.get_data()
    minutes = int(data.get("minutes", 1))
    text = (message.text or "").strip()
    run_at = datetime.now(tz=TZ) + timedelta(minutes=minutes)
    await add_reminder(message.from_user.id, run_at.timestamp(), text)
    await message.answer(tr("reminder_set", user_id=message.from_user.id))
    await render_reminders(message, state)


async def daily_on(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await enable_daily_digest(message.from_user.id, True)
    await message.answer(tr("daily_on", user_id=message.from_user.id))
    await render_reminders(message, state)


async def daily_off(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await enable_daily_digest(message.from_user.id, False)
    await message.answer(tr("daily_off", user_id=message.from_user.id))
    await render_reminders(message, state)


# =========================
# Контакты / Ссылки
# =========================
async def show_supervisor_contacts(message: Message):
    if is_banned(message.from_user.id):
        return await message.answer(tr("banned", user_id=message.from_user.id))
    await message.answer(SUPERVISOR_CONTACT)


async def show_links(message: Message):
    if is_banned(message.from_user.id):
        return await message.answer(tr("banned", user_id=message.from_user.id))
    user = get_user(message.from_user.id)
    shop = user[3] if user else None
    await message.answer(get_links_text(shop), parse_mode="Markdown")


# =========================
# Навигация кнопками Back/Home
# =========================
async def back_handler(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    screen = await nav_pop(state)
    if screen == "training":
        return await render_training(message, state)
    if screen == "faq":
        return await render_faq(message, state)
    if screen == "reminders":
        return await render_reminders(message, state)
    # по умолчанию — домой
    return await render_main(message, state)


async def home_handler(message: Message, state: FSMContext):
    if await guard_ban(message):
        return
    await render_main(message, state)


# =========================
# Admin
# =========================
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    users = get_all_users()
    text = f"Всего пользователей: {len(users)}\n"
    for u in users:
        text += f"ID: {u[0]}, Lang: {u[4]}, Role: {u[2]}, Shop: {u[3]}, Phone: {u[5] if len(u)>5 else None}\n"
    await message.answer(text)

async def admin_cleanup_feedback(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    await cleanup_feedback()
    await message.answer("✅ Все фидбэки очищены")

async def admin_list_users(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    users = get_all_users()
    text = "Список пользователей:\n"
    for u in users:
        text += f"ID: {u[0]}, Lang: {u[4]}, Role: {u[2]}, Shop: {u[3]}, Phone: {u[5] if len(u)>5 else None}\n"
    await message.answer(text)

async def admin_edit_user(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    try:
        parts = message.text.split(maxsplit=3)
        user_id = int(parts[1])
        field = parts[2].lower()
        value = parts[3]
    except Exception:
        return await message.answer("❌ Использование: /edit_user <id> <role/shop/lang> <value>")
    user = get_user(user_id)
    if not user:
        return await message.answer("❌ Пользователь не найден")
    if field == "role":
        await save_user(user_id, user[1], role=value, shop=user[3], lang=user[4])
    elif field == "shop":
        await save_user(user_id, user[1], role=user[2], shop=value, lang=user[4])
    elif field == "lang":
        await save_user(user_id, user[1], role=user[2], shop=user[3], lang=value.upper())
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
    sent = 0
    for u in users:
        try:
            await bot.send_message(u[0], text)
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Отправлено: {sent}/{len(users)}")

async def admin_ban(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
    except Exception:
        return await message.answer("❌ Использование: /ban <user_id>")
    await ban_user(user_id)
    await message.answer(f"✅ Пользователь {user_id} забанен")

async def admin_unban(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
    except Exception:
        return await message.answer("❌ Использование: /unban <user_id>")
    await unban_user(user_id)
    await message.answer(f"✅ Пользователь {user_id} разбанен")

async def admin_set_digest(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    try:
        text = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.answer("❌ Использование: /set_digest <текст>")
    await set_daily_digest_message(text)
    await message.answer("✅ Текст дайджеста обновлён")

async def admin_help(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Только для админа")
    await message.answer(
        "Админ-команды:\n"
        "/stats — статистика\n"
        "/users — список\n"
        "/edit_user <id> <role/shop/lang> <value>\n"
        "/broadcast <текст>\n"
        "/cleanup — очистить фидбэк\n"
        "/ban <user_id> /unban <user_id>\n"
        "/set_digest <текст> — текст ежедневного дайджеста\n"
    )


# =========================
# (Старый раздел «Мои доставки») — оставлен как функция,
# но пункт удалён из меню и не регистрируется.
# =========================
async def my_deliveries(message: Message):
    await message.answer(
        "Раздел «Мои доставки» отключён. "
        "Если понадобится вернуть — можно подключить API/таблицу и сделать список доставок."
    )


# =========================
# Планировщик (reminders + daily digest)
# =========================
async def scheduler_loop(bot: Bot):
    last_digest_date_by_user: dict[int, str] = {}  # user_id -> YYYY-MM-DD (в TZ)
    while True:
        try:
            # 1) Напоминания
            now = datetime.now(tz=TZ)
            for rem in await pop_due_reminders(now.timestamp()):
                try:
                    await bot.send_message(rem.user_id, f"⏰ Напоминание:\n{rem.text}")
                except Exception:
                    pass

            # 2) Дайджест (в 09:00 по TZ)
            digest_users = get_daily_digest_users()
            if digest_users:
                today = now.strftime("%Y-%m-%d")
                if now.hour == 9 and now.minute == 0:
                    msg = get_daily_digest_message()
                    for uid in digest_users:
                        if last_digest_date_by_user.get(uid) == today:
                            continue
                        try:
                            await bot.send_message(uid, f"📬 {msg}")
                            last_digest_date_by_user[uid] = today
                        except Exception:
                            pass

        except Exception as e:
            logger.exception("Scheduler error: %s", e)

        await asyncio.sleep(5)


# =========================
# Ошибки → админу
# =========================
async def on_error(event: ErrorEvent, bot: Bot):
    # Логируем локально
    logger.exception("Unhandled error", exc_info=event.exception)

    # Уведомляем админа (кратко)
    tb = "".join(traceback.format_exception(type(event.exception), event.exception, event.exception.__traceback__))
    short = tb[-3500:]  # влезаем в лимиты
    text = (
        "⚠️ Ошибка в боте\n"
        f"Update: {type(event.update).__name__}\n"
        f"Exception: {type(event.exception).__name__}: {event.exception}\n\n"
        f"<pre>{short}</pre>"
    )
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass
    return True


# =========================
# Запуск
# =========================
async def main():
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    # sqlite init
    await init_db(os.getenv('BOT_DB', 'bot.db'))

    # errors
    async def _err(e: ErrorEvent):
        return await on_error(e, bot)
    dp.errors.register(_err)

    # /start
    dp.message.register(start, Command("start"))

    # home/back
    dp.message.register(home_handler, lambda m: (m.text or "").strip() in all_btn_texts("home"))
    dp.message.register(back_handler, lambda m: (m.text or "").strip() in all_btn_texts("back"))

    # lang
    dp.message.register(change_language, lambda m: (m.text or "").strip() in all_btn_texts("change_lang"))
    dp.message.register(set_language, StateFilter(LanguageState.lang))
    dp.message.register(set_phone, StateFilter(Register.phone))

    # register
    dp.message.register(set_role, StateFilter(Register.role))
    dp.message.register(set_shop, StateFilter(Register.shop))

    # menu actions
    dp.message.register(training_menu, lambda m: (m.text or "").strip() in all_btn_texts("training"))
    dp.message.register(faq_menu, lambda m: (m.text or "").strip() in all_btn_texts("faq"))
    dp.message.register(reminders_entry, lambda m: (m.text or "").strip() in all_btn_texts("reminders"))
    dp.message.register(show_links, lambda m: (m.text or "").strip() in all_btn_texts("links"))
    dp.message.register(show_supervisor_contacts, lambda m: (m.text or "").strip() in all_btn_texts("contacts"))
    dp.message.register(feedback_start, lambda m: (m.text or "").strip() in all_btn_texts("feedback"))

    # training topics
    dp.message.register(training_topic, lambda m: (m.text or "").strip() in {
        "Основные правила", "Погрузка", "Подключение терминала",
        "Правила сборки", "Возвраты", "Закрытие точки"
    })

    # feedback state
    dp.message.register(save_feedback_handler, StateFilter(FeedbackState.text))

    # FAQ state
    dp.message.register(faq_search, StateFilter(FAQState.query))

    # reminders sub-menu
    dp.message.register(reminder_add_start, lambda m: (m.text or "").strip() in all_btn_texts("rem_add"))
    dp.message.register(daily_on, lambda m: (m.text or "").strip() in all_btn_texts("daily_on"))
    dp.message.register(daily_off, lambda m: (m.text or "").strip() in all_btn_texts("daily_off"))

    # reminder flow
    dp.message.register(reminder_set_minutes, StateFilter(ReminderState.minutes))
    dp.message.register(reminder_set_text, StateFilter(ReminderState.text))

    # Admin commands
    dp.message.register(admin_help, Command(commands=["admin"]))
    dp.message.register(admin_stats, Command(commands=["stats"]))
    dp.message.register(admin_cleanup_feedback, Command(commands=["cleanup"]))
    dp.message.register(admin_list_users, Command(commands=["users"]))
    dp.message.register(admin_edit_user, Command(commands=["edit_user"]))
    dp.message.register(lambda m: admin_broadcast(m, bot), Command(commands=["broadcast"]))
    dp.message.register(admin_ban, Command(commands=["ban"]))
    dp.message.register(admin_unban, Command(commands=["unban"]))
    dp.message.register(admin_set_digest, Command(commands=["set_digest"]))

    # scheduler
    asyncio.create_task(scheduler_loop(bot))

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())
