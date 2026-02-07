"""Telegram bot (aiogram 3.x)

This file is the single entrypoint.

Key points:
- Compatible with aiogram >= 3.7 (Bot(..., default=DefaultBotProperties(...)))
- Keeps all previously existing features (registration, feedback, training, links,
  supervisor contacts, FAQ, reminders, daily digest, admin commands)
- Fixes API mismatches between bot.py <-> db.py <-> keyboards.py <-> states.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, LinkPreviewOptions

import db
from keyboards import (
    BUTTONS,
    all_btn_texts,
    btn,
    get_lang_kb,
    get_links_text,
    get_role_kb,
    get_shop_kb,
    ROLE_LABELS,
    SHOP_LABELS,
    get_training_kb,
    main_menu,
    phone_request_kb,
    reminders_menu,
    SUPERVISOR_CONTACT,
)
from states import FeedbackState, FAQState, LanguageState, Register, ReminderState, TrainingAdminState
from translations import get_user_lang, tr


# -------------------------
# CONFIG
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Поддерживаем оба варианта файла окружения: ".env" и "env" (в репозитории есть env).
_dotenv_loaded = load_dotenv(os.path.join(BASE_DIR, ".env"))
if not _dotenv_loaded:
    load_dotenv(os.path.join(BASE_DIR, "env"))

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Важно: путь к БД должен быть стабильным между перезапусками.
# Если BOT_DB относительный, сохраняем его рядом с bot.py.
_raw_db = (os.getenv("BOT_DB", "bot.db") or "bot.db").strip()
BOT_DB = _raw_db if os.path.isabs(_raw_db) else os.path.join(BASE_DIR, _raw_db)

def _parse_admin_ids(raw: str) -> set[int]:
    if not raw:
        return set()
    raw = raw.replace(",", " ")
    out: set[int] = set()
    for part in raw.split():
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out

# Admins: comma-separated or space-separated user ids.
# Поддерживаем несколько имён переменных, т.к. в разных деплоях часто путают.
ADMIN_IDS: set[int] = set()
ADMIN_IDS |= _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
ADMIN_IDS |= _parse_admin_ids(os.getenv("ADMIN_ID", ""))
ADMIN_IDS |= _parse_admin_ids(os.getenv("ADMIN_TELEGRAM_ID", ""))

# Scheduler timezone (as requested by system: Europe/Oslo)
TZ = ZoneInfo("Europe/Oslo")
DAILY_DIGEST_HOUR = 9
DAILY_DIGEST_MINUTE = 0


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("bot")
logger.info("ADMIN_IDS loaded: %s", sorted(ADMIN_IDS))


# Canonical values stored in DB (to keep backward compatibility with existing data)
ROLE_CANON = {"courier": "Курьер", "picker": "Сборщик"}
# Reverse maps (button text -> canonical RU value)
_ROLE_TEXT_TO_RU: dict[str, str] = {}
for _lang, _labels in ROLE_LABELS.items():
    _ROLE_TEXT_TO_RU[_labels["courier"]] = ROLE_CANON["courier"]
    _ROLE_TEXT_TO_RU[_labels["picker"]] = ROLE_CANON["picker"]

_SHOP_TEXT_TO_RU: dict[str, str] = {}
for _lang, _labels in SHOP_LABELS.items():
    for _ru_name, _label in _labels.items():
        # _ru_name is RU shop key (e.g. "Бухарестская"), _label is localized label shown to user
        _SHOP_TEXT_TO_RU[_label] = _ru_name


router = Router()


# -------------------------
# NAVIGATION STACK
# -------------------------

async def _push_nav(state: FSMContext, screen: str, payload: dict | None = None) -> None:
    data = await state.get_data()
    stack = data.get("nav_stack", [])
    stack.append((screen, payload or {}))
    await state.update_data(nav_stack=stack)


async def _go_home(message: Message, state: FSMContext) -> None:
    # reset to main
    await state.clear()
    await state.update_data(nav_stack=[("main", {})])
    await _show_main_menu(message)


async def _go_back(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    stack = data.get("nav_stack", [])
    if len(stack) <= 1:
        await _go_home(message, state)
        return

    stack.pop()
    screen, payload = stack[-1]
    await state.update_data(nav_stack=stack)
    await _render_screen(message, state, screen, payload)


async def _render_screen(message: Message, state: FSMContext, screen: str, payload: dict | None = None) -> None:
    payload = payload or {}
    if screen == "main":
        await _go_home(message, state)
    elif screen == "training":
        await _open_training(message, state)
    elif screen == "faq":
        await _open_faq(message, state)
    elif screen == "reminders":
        await _open_reminders(message, state)
    elif screen == "feedback":
        await _open_feedback(message, state)
    else:
        await _go_home(message, state)


# -------------------------
# COMMON CHECKS
# -------------------------

def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def _check_banned(message: Message) -> bool:
    if db.is_banned(message.from_user.id):
        await message.answer(tr("banned", message.from_user.id))
        return True
    return False


def _user_tuple_to_dict(u: tuple) -> dict:
    # db.users_db stores: (user_id, username, role, shop, lang, phone)
    return {
        "user_id": u[0],
        "username": u[1],
        "role": u[2],
        "shop": u[3],
        "lang": u[4],
        "phone": u[5] if len(u) > 5 else None,
    }


# -------------------------
# UI HELPERS
# -------------------------

async def _show_main_menu(message: Message) -> None:
    user = db.get_user(message.from_user.id)
    lang = get_user_lang(message.from_user.id)
    role = user[2] if user else None

    await message.answer(
        tr("help", message.from_user.id),
        reply_markup=main_menu(role=_ROLE_TEXT_TO_RU.get(role, role), user_id=message.from_user.id, lang=lang),
    )


# -------------------------
# START / REGISTRATION
# -------------------------

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return

    user = db.get_user(message.from_user.id)

    # new user: ask language
    if not user:
        await state.clear()
        await state.set_state(LanguageState.lang)
        await message.answer(tr("welcome", message.from_user.id), reply_markup=get_lang_kb())
        return

    # existing user: if no phone -> ask phone
    phone = user[5] if len(user) > 5 else None
    if not phone:
        lang = get_user_lang(message.from_user.id)
        await state.set_state(Register.phone)
        await message.answer(tr("phone_prompt", message.from_user.id), reply_markup=phone_request_kb(lang))
        return

    # if role/shop missing: continue registration
    if not user[2]:
        await state.set_state(Register.role)
        await message.answer(tr("role_prompt", message.from_user.id), reply_markup=get_role_kb(get_user_lang(message.from_user.id)))
        return
    if not user[3]:
        await state.set_state(Register.shop)
        await message.answer(tr("choose_shop", message.from_user.id), reply_markup=get_shop_kb(get_user_lang(message.from_user.id)))
        return

    await state.clear()
    await state.update_data(nav_stack=[("main", {})])
    await _show_main_menu(message)


# --- Language selection
@router.message(LanguageState.lang)
async def set_language(message: Message, state: FSMContext):
    if await _check_banned(message):
        return

    lang = (message.text or "").strip().upper()
    if lang not in {"RU", "EN", "UZ", "TJ", "KG"}:
        await message.answer(tr("choose_language", message.from_user.id), reply_markup=get_lang_kb())
        return

    # create/update user with chosen language
    await db.save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        lang=lang,
    )

    await state.clear()
    await state.set_state(Register.phone)
    await message.answer(tr("phone_prompt", message.from_user.id), reply_markup=phone_request_kb(lang))


# --- Phone registration
@router.message(Register.phone, F.content_type == ContentType.CONTACT)
async def set_phone(message: Message, state: FSMContext):
    if await _check_banned(message):
        return

    contact = message.contact
    if not contact or contact.user_id != message.from_user.id:
        await message.answer(tr("phone_invalid", message.from_user.id))
        return

    user = db.get_user(message.from_user.id)
    lang = user[4] if user else "RU"
    username = message.from_user.username
    role = user[2] if user else None
    shop = user[3] if user else None

    await db.save_user(
        user_id=message.from_user.id,
        username=username,
        role=_ROLE_TEXT_TO_RU.get(role, role),
        shop=_SHOP_TEXT_TO_RU.get(shop, shop),
        lang=lang,
        phone=contact.phone_number,
    )

    await message.answer(tr("phone_saved", message.from_user.id))
    await state.set_state(Register.role)
    await message.answer(tr("role_prompt", message.from_user.id), reply_markup=get_role_kb(lang))


@router.message(Register.phone)
async def phone_invalid_any(message: Message, state: FSMContext):
    # If user types text instead of contact
    await message.answer(tr("phone_invalid", message.from_user.id))


# --- Role selection
@router.message(Register.role)
async def set_role(message: Message, state: FSMContext):
    if await _check_banned(message):
        return

    role = (message.text or "").strip()
    if role not in _ROLE_TEXT_TO_RU:
        await message.answer(tr("role_prompt", message.from_user.id), reply_markup=get_role_kb(get_user_lang(message.from_user.id)))
        return

    user = db.get_user(message.from_user.id)
    lang = user[4] if user else "RU"
    shop = user[3] if user else None
    phone = user[5] if user and len(user) > 5 else None
    await db.save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        role=_ROLE_TEXT_TO_RU.get(role, role),
        shop=_SHOP_TEXT_TO_RU.get(shop, shop),
        lang=lang,
        phone=phone,
    )

    await message.answer(f"{tr('role_confirm', message.from_user.id)} {role}")
    await state.set_state(Register.shop)
    await message.answer(tr("choose_shop", message.from_user.id), reply_markup=get_shop_kb(lang))


# --- Shop selection
@router.message(Register.shop)
async def set_shop(message: Message, state: FSMContext):
    if await _check_banned(message):
        return

    shop = (message.text or "").strip()
    if shop not in _SHOP_TEXT_TO_RU:
        await message.answer(tr("choose_shop", message.from_user.id), reply_markup=get_shop_kb(get_user_lang(message.from_user.id)))
        return

    user = db.get_user(message.from_user.id)
    lang = user[4] if user else "RU"
    role = user[2] if user else None
    phone = user[5] if user and len(user) > 5 else None
    await db.save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        role=_ROLE_TEXT_TO_RU.get(role, role),
        shop=_SHOP_TEXT_TO_RU.get(shop, shop),
        lang=lang,
        phone=phone,
    )

    await state.clear()
    await state.update_data(nav_stack=[("main", {})])
    await _show_main_menu(message)


# -------------------------
# MENU BUTTONS: Back/Home/Change language
# -------------------------


@router.message(F.text.in_(all_btn_texts("back")))
async def back_button(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _go_back(message, state)


@router.message(F.text.in_(all_btn_texts("home")))
async def home_button(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _go_home(message, state)


@router.message(F.text.in_(all_btn_texts("change_lang")))
async def change_lang(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await state.clear()
    await state.set_state(LanguageState.lang)
    await message.answer(tr("choose_language", message.from_user.id), reply_markup=get_lang_kb())



# -------------------------
# KNOWLEDGE BASE (Обучалки + FAQ)
# -------------------------

SEARCH_BTNS = {
    "RU": "🔎 Поиск",
    "EN": "🔎 Search",
    "UZ": "🔎 Qidirish",
    "TJ": "🔎 Ҷустуҷӯ",
    "KG": "🔎 Издөө",
}

ADMIN_LIST_BTNS = {
    "RU": "📋 Список материалов",
    "EN": "📋 Materials list",
    "UZ": "📋 Materiallar ro'yxati",
    "TJ": "📋 Рӯйхати мавод",
    "KG": "📋 Материалдар тизмеси",
}
ADMIN_ADD_BTNS = {
    "RU": "➕ Добавить материал",
    "EN": "➕ Add material",
    "UZ": "➕ Material qo‘shish",
    "TJ": "➕ Илова кардани мавод",
    "KG": "➕ Материал кошуу",
}
ADMIN_EDIT_BTNS = {
    "RU": "✏️ Редактировать материал",
    "EN": "✏️ Edit material",
    "UZ": "✏️ Materialni tahrirlash",
    "TJ": "✏️ Таҳрири мавод",
    "KG": "✏️ Материалды түзөтүү",
}
ADMIN_DEL_BTNS = {
    "RU": "🗑 Удалить материал",
    "EN": "🗑 Delete material",
    "UZ": "🗑 Materialni o‘chirish",
    "TJ": "🗑 Пок кардани мавод",
    "KG": "🗑 Өчүрүү",
}

def _kb_label(user_id: int, mapping: dict[str,str], default: str) -> str:
    lang = get_user_lang(user_id)
    return mapping.get(lang, default)


def _knowledge_kb(user_id: int, role: str | None, lang: str, is_admin_user: bool) -> ReplyKeyboardMarkup:
    materials = db.materials_for_role(role, limit=24)
    rows: list[list[KeyboardButton]] = []

    # темы (по 2 в ряд)
    buf: list[KeyboardButton] = []
    for m in materials:
        title = (m.get("title") or "").strip()
        if not title:
            continue
        buf.append(KeyboardButton(text=title))
        if len(buf) == 2:
            rows.append(buf)
            buf = []
    if buf:
        rows.append(buf)

    # поиск
    rows.append([KeyboardButton(text=_kb_label(user_id, SEARCH_BTNS, SEARCH_BTNS["RU"]))])

    # админские действия
    if is_admin_user:
        rows.append([KeyboardButton(text=_kb_label(user_id, ADMIN_LIST_BTNS, ADMIN_LIST_BTNS["RU"]))])
        rows.append([
            KeyboardButton(text=_kb_label(user_id, ADMIN_ADD_BTNS, ADMIN_ADD_BTNS["RU"])),
            KeyboardButton(text=_kb_label(user_id, ADMIN_EDIT_BTNS, ADMIN_EDIT_BTNS["RU"])),
        ])
        rows.append([KeyboardButton(text=_kb_label(user_id, ADMIN_DEL_BTNS, ADMIN_DEL_BTNS["RU"]))])

    # навигация
    rows.append([KeyboardButton(text=btn(lang, "back")), KeyboardButton(text=btn(lang, "home"))])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def _open_knowledge(message: Message, state: FSMContext):
    await _push_nav(state, "training")  # сохраняем старое имя экрана для совместимости
    user = db.get_user(message.from_user.id)
    role = user[2] if user else ""
    lang = get_user_lang(message.from_user.id)
    is_admin_user = message.from_user.id in ADMIN_IDS
    await message.answer(
        tr("kb_menu", message.from_user.id),
        reply_markup=_knowledge_kb(message.from_user.id, role, lang, is_admin_user),
    )


@router.message(F.text.in_(all_btn_texts("training")))
async def training_menu(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _open_knowledge(message, state)


# Старые клиенты могут прислать кнопку FAQ из предыдущего меню — считаем это тем же разделом.
@router.message(F.text.in_(all_btn_texts("faq")))
async def faq_alias(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _open_knowledge(message, state)


@router.message(F.text.in_(set(SEARCH_BTNS.values())))
async def kb_search_prompt(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _push_nav(state, "faq")  # логически это поиск, но раздел тот же
    await state.set_state(FAQState.query)
    await message.answer(tr("kb_search_prompt", message.from_user.id))


@router.message(FAQState.query)
async def kb_search(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    q = (message.text or "").strip()
    results = db.search_faq(q, limit=5)
    if not results:
        await message.answer(tr("kb_not_found", message.from_user.id))
        return

    text = tr("kb_found_header", message.from_user.id)
    for r in results:
        text += f"• <b>{r.get('title','')}</b>\n"
    text += "{pick_topic}"

    # вернём клавиатуру материалов
    user = db.get_user(message.from_user.id)
    role = user[2] if user else ""
    lang = get_user_lang(message.from_user.id)
    await state.clear()
    await message.answer(text, reply_markup=_knowledge_kb(message.from_user.id, role, lang, message.from_user.id in ADMIN_IDS))


def _is_topic_title(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    # точное совпадение по title
    for a in db.FAQ_ARTICLES:
        if (a.get("title") or "").strip() == t:
            return True
    return False


@router.message(F.text.func(_is_topic_title))
async def kb_open_topic(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    title = (message.text or "").strip()
    # найдём статью
    article = next((a for a in db.FAQ_ARTICLES if (a.get("title") or "").strip() == title), None)
    body = (article or {}).get("body") or "Материал пока готовится."
    await message.answer(body)


# --- Admin: управление материалами прямо в чате ---


@router.message(F.text.in_(set(ADMIN_LIST_BTNS.values())))
async def admin_kb_list(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr("admin_no_access", message.from_user.id, id=message.from_user.id))
        return

    items = await db.faq_list(limit=200)
    if not items:
        await message.answer(tr("kb_no_materials", message.from_user.id))
        return

    text = "📋 Материалы (id — заголовок):\n\n"
    for it in items[:200]:
        text += f"{it.get('id')}. {it.get('title')}\n"
    await message.answer(text)


@router.message(F.text.in_(set(ADMIN_ADD_BTNS.values())))
async def admin_kb_add_start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr("admin_no_access", message.from_user.id, id=message.from_user.id))
        return
    await state.clear()
    await state.set_state(TrainingAdminState.title)
    await message.answer(tr("kb_admin_ask_title", message.from_user.id))


@router.message(TrainingAdminState.title)
async def admin_kb_add_title(message: Message, state: FSMContext):
    title = (message.text or "").strip()
    if not title:
        await message.answer(tr("kb_admin_title_empty", message.from_user.id))
        return
    await state.update_data(title=title)
    await state.set_state(TrainingAdminState.body)
    await message.answer(tr("kb_admin_ask_body", message.from_user.id))


@router.message(TrainingAdminState.body)
async def admin_kb_add_body(message: Message, state: FSMContext):
    body = (message.text or "").strip()
    if not body:
        await message.answer(tr("kb_admin_body_empty", message.from_user.id))
        return
    await state.update_data(body=body)
    await state.set_state(TrainingAdminState.tags)
    await message.answer(tr("kb_admin_ask_tags", message.from_user.id))


@router.message(TrainingAdminState.tags)
async def admin_kb_add_tags(message: Message, state: FSMContext):
    data = await state.get_data()
    tags = (message.text or "").strip()
    if tags == "-":
        tags = ""
    fid = await db.faq_add(data["title"], data["body"], tags)
    await state.clear()
    await message.answer(tr("kb_admin_added", message.from_user.id, id=fid))


@router.message(F.text.in_(set(ADMIN_DEL_BTNS.values())))
async def admin_kb_del_start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr("admin_no_access", message.from_user.id, id=message.from_user.id))
        return
    await state.clear()
    await state.set_state(TrainingAdminState.target_id)
    await message.answer(tr("kb_admin_ask_del_id", message.from_user.id))


@router.message(TrainingAdminState.target_id)
async def admin_kb_del_do(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(tr("kb_admin_need_id", message.from_user.id))
        return
    ok = await db.faq_delete(int(raw))
    await state.clear()
    await message.answer(tr("kb_admin_deleted", message.from_user.id) if ok else tr("kb_not_found", message.from_user.id))


@router.message(F.text.in_(set(ADMIN_EDIT_BTNS.values())))
async def admin_kb_edit_start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr("admin_no_access", message.from_user.id, id=message.from_user.id))
        return
    await state.clear()
    await state.set_state(TrainingAdminState.target_id)
    await state.update_data(action="edit")
    await message.answer(tr("kb_admin_ask_edit_id", message.from_user.id))


@router.message(TrainingAdminState.target_id, F.text.func(lambda t: (t or "").strip().isdigit()))
async def admin_kb_edit_choose(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("action") != "edit":
        return  # это не наш сценарий (удаление обрабатывается другим хэндлером)

    fid = int((message.text or "0").strip())
    items = await db.faq_list(limit=500)
    item = next((x for x in items if int(x.get("id","0")) == fid), None)
    if not item:
        await message.answer(tr("kb_admin_not_found_id", message.from_user.id))
        return

    await state.update_data(target_id=fid)
    await state.set_state(TrainingAdminState.title)
    await message.answer(
        tr("kb_admin_current_title", message.from_user.id, title=item.get("title",""))
        + tr("kb_admin_send_new_title_or_dash", message.from_user.id)
    )


@router.message(TrainingAdminState.title)
async def admin_kb_edit_title(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("action") != "edit":
        # это сценарий добавления, его обработал другой хэндлер раньше
        return

    title = (message.text or "").strip()
    if title == "-":
        title = None
    await state.update_data(title=title)
    await state.set_state(TrainingAdminState.body)
    await message.answer(tr("kb_admin_send_new_body_or_dash", message.from_user.id))


@router.message(TrainingAdminState.body)
async def admin_kb_edit_body(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("action") != "edit":
        return
    body = (message.text or "").strip()
    if body == "-":
        body = None
    await state.update_data(body=body)
    await state.set_state(TrainingAdminState.tags)
    await message.answer(tr("kb_admin_send_new_tags_or_dash", message.from_user.id))


@router.message(TrainingAdminState.tags)
async def admin_kb_edit_tags(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("action") != "edit":
        return
    tags = (message.text or "").strip()
    if tags == "-":
        tags = None
    fid = int(data["target_id"])
    ok = await db.faq_edit(fid, title=data.get("title"), body=data.get("body"), tags=tags)
    await state.clear()
    await message.answer(tr("kb_admin_updated", message.from_user.id) if ok else tr("kb_admin_update_fail", message.from_user.id))


# -------------------------
# LINKS / CONTACTS
# -------------------------


@router.message(F.text.in_(all_btn_texts("links")))
async def links(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    user = db.get_user(message.from_user.id)
    shop = user[3] if user else None
    await _push_nav(state, "links")
    await message.answer(get_links_text(shop), link_preview_options=LinkPreviewOptions(is_disabled=True))


@router.message(F.text.in_(all_btn_texts("contacts")))
async def contacts(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _push_nav(state, "contacts")
    await message.answer(SUPERVISOR_CONTACT)


# -------------------------
# FEEDBACK
# -------------------------


async def _open_feedback(message: Message, state: FSMContext):
    await _push_nav(state, "feedback")
    await state.set_state(FeedbackState.text)
    await message.answer(tr("feedback", message.from_user.id))


@router.message(F.text.in_(all_btn_texts("feedback")))
async def feedback_start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _open_feedback(message, state)


@router.message(FeedbackState.text)
async def feedback_save(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    txt = (message.text or "").strip()
    if not txt:
        await message.answer(tr("feedback", message.from_user.id))
        return
    await db.save_feedback(message.from_user.id, txt)
    await state.clear()
    await message.answer(tr("feedback_thanks", message.from_user.id))
    await _show_main_menu(message)


# -------------------------
# FAQ
# -------------------------


async def _open_faq(message: Message, state: FSMContext):
    await _push_nav(state, "faq")
    await state.set_state(FAQState.query)
    await message.answer(tr("faq_prompt", message.from_user.id))


@router.message(F.text.in_(all_btn_texts("faq")))
async def faq_start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _open_faq(message, state)


@router.message(FAQState.query)
async def faq_search(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    q = (message.text or "").strip()
    results = db.search_faq(q, limit=5)
    if not results:
        await message.answer(tr("faq_not_found", message.from_user.id))
        return

    text = "📚 FAQ:\n\n" + "\n\n".join([f"<b>{r['title']}</b>\n{r['body']}" for r in results])
    await message.answer(text)


# -------------------------
# REMINDERS + DAILY DIGEST
# -------------------------


async def _open_reminders(message: Message, state: FSMContext):
    await _push_nav(state, "reminders")
    lang = get_user_lang(message.from_user.id)
    await message.answer(tr("reminders_menu", message.from_user.id), reply_markup=reminders_menu(lang))


@router.message(F.text.in_(all_btn_texts("reminders")))
async def reminders_open(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await _open_reminders(message, state)


@router.message(F.text.in_(all_btn_texts("rem_add")))
async def reminders_add_start(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await state.set_state(ReminderState.minutes)
    await message.answer(tr("reminder_ask_minutes", message.from_user.id))


@router.message(ReminderState.minutes)
async def reminders_set_minutes(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    if not txt.isdigit():
        await message.answer(tr("reminder_ask_minutes", message.from_user.id))
        return
    await state.update_data(minutes=int(txt))
    await state.set_state(ReminderState.text)
    await message.answer(tr("reminder_ask_text", message.from_user.id))


@router.message(ReminderState.text)
async def reminders_set_text(message: Message, state: FSMContext):
    data = await state.get_data()
    minutes = int(data.get("minutes", 0) or 0)
    txt = (message.text or "").strip()
    if minutes <= 0 or not txt:
        await message.answer(tr("reminder_ask_minutes", message.from_user.id))
        await state.set_state(ReminderState.minutes)
        return
    run_at_ts = time.time() + minutes * 60
    await db.add_reminder(message.from_user.id, run_at_ts, txt)
    await state.clear()
    await message.answer(tr("reminder_set", message.from_user.id))


@router.message(F.text.in_(all_btn_texts("daily_on")))
async def daily_on(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await db.enable_daily_digest(message.from_user.id, True)
    await message.answer(tr("daily_on", message.from_user.id))


@router.message(F.text.in_(all_btn_texts("daily_off")))
async def daily_off(message: Message, state: FSMContext):
    if await _check_banned(message):
        return
    await db.enable_daily_digest(message.from_user.id, False)
    await message.answer(tr("daily_off", message.from_user.id))


# -------------------------
# ADMIN COMMANDS
# -------------------------


@router.message(Command("admin"))
async def admin_help(message: Message):
    if not _is_admin(message.from_user.id):
        await message.answer(tr("admin_no_access", message.from_user.id, id=message.from_user.id))
        return
    await message.answer(tr("admin_help", message.from_user.id))


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if not _is_admin(message.from_user.id):
        return
    users = len(db.get_all_users())
    fb = len(db.get_feedback())
    banned = len(db.banned_users)
    await message.answer(tr("admin_stats_text", message.from_user.id, users=users, fb=fb, banned=banned))


@router.message(Command("users"))
async def admin_users(message: Message):
    if not _is_admin(message.from_user.id):
        return
    users = db.get_all_users()
    if not users:
        await message.answer(tr("admin_users_empty", message.from_user.id))
        return
    lines = []
    for u in users[:50]:
        d = _user_tuple_to_dict(u)
        lines.append(
            f"{d['user_id']} | @{d['username'] or '-'} | {d['role'] or '-'} | {d['shop'] or '-'} | {d['lang']} | {d['phone'] or '-'}"
        )
    await message.answer("\n".join(lines))


@router.message(Command("edit_user"))
async def admin_edit_user(message: Message):
    if not _is_admin(message.from_user.id):
        return
    parts = (message.text or "").split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(tr("admin_format_edit_user", message.from_user.id))
        return
    uid = int(parts[1])
    field = parts[2].lower()
    value = parts[3].strip()
    u = db.get_user(uid)
    if not u:
        await message.answer(tr("admin_user_not_found", message.from_user.id))
        return
    d = _user_tuple_to_dict(u)
    if field not in {"role", "shop", "lang", "phone"}:
        await message.answer(tr("admin_bad_field", message.from_user.id))
        return
    if field == "lang":
        value = value.upper()
    d[field] = value
    await db.save_user(uid, d["username"], d["role"], d["shop"], d["lang"], d["phone"])  # type: ignore[arg-type]
    await message.answer(tr("kb_admin_updated", message.from_user.id))


@router.message(Command("broadcast"))
async def admin_broadcast(message: Message):
    if not _is_admin(message.from_user.id):
        return
    text = (message.text or "").replace("/broadcast", "", 1).strip()
    if not text:
        await message.answer(tr("admin_format_broadcast", message.from_user.id))
        return
    users = db.get_all_users()
    sent = 0
    for u in users:
        uid = u[0]
        if db.is_banned(uid):
            continue
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            continue
    await message.answer(tr("admin_sent", message.from_user.id, sent=sent))


@router.message(Command("cleanup"))
async def admin_cleanup(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await db.cleanup_feedback()
    await message.answer(tr("admin_feedback_cleared", message.from_user.id))


@router.message(Command("ban"))
async def admin_ban(message: Message):
    if not _is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(tr("admin_format_ban", message.from_user.id))
        return
    uid = int(parts[1])
    await db.ban_user(uid)
    await message.answer(tr("admin_banned_ok", message.from_user.id))


@router.message(Command("unban"))
async def admin_unban(message: Message):
    if not _is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(tr("admin_format_unban", message.from_user.id))
        return
    uid = int(parts[1])
    await db.unban_user(uid)
    await message.answer(tr("admin_unbanned_ok", message.from_user.id))


@router.message(Command("set_digest"))
async def admin_set_digest(message: Message):
    if not _is_admin(message.from_user.id):
        return
    text = (message.text or "").replace("/set_digest", "", 1).strip()
    if not text:
        await message.answer(tr("admin_format_set_digest", message.from_user.id))
        return
    await db.set_daily_digest_message(text)
    await message.answer(tr("admin_updated", message.from_user.id))


# --- FAQ admin CRUD
@router.message(Command("faq_list"))
async def admin_faq_list(message: Message):
    if not _is_admin(message.from_user.id):
        return
    items = await db.faq_list(limit=50)
    if not items:
        await message.answer(tr("admin_faq_empty", message.from_user.id))
        return
    await message.answer("\n".join([f"{a['id']}. {a['title']}" for a in items]))


@router.message(Command("faq_add"))
async def admin_faq_add(message: Message):
    if not _is_admin(message.from_user.id):
        return
    raw = (message.text or "").replace("/faq_add", "", 1).strip()
    try:
        title, body, tags = [x.strip() for x in raw.split("||")]
    except Exception:
        await message.answer(tr("admin_format_faq_add", message.from_user.id))
        return
    fid = await db.faq_add(title, body, tags)
    await message.answer(tr("kb_admin_added", message.from_user.id, id=fid))


@router.message(Command("faq_del"))
async def admin_faq_del(message: Message):
    if not _is_admin(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer(tr("admin_format_faq_del", message.from_user.id))
        return
    ok = await db.faq_delete(int(parts[1]))
    await message.answer(tr("kb_admin_deleted", message.from_user.id) if ok else tr("common_not_found", message.from_user.id))


@router.message(Command("faq_edit"))
async def admin_faq_edit(message: Message):
    if not _is_admin(message.from_user.id):
        return
    raw = (message.text or "").replace("/faq_edit", "", 1).strip()
    parts = [x.strip() for x in raw.split("||")]
    if not parts or not parts[0].isdigit():
        await message.answer(tr("admin_format_faq_edit", message.from_user.id))
        return
    fid = int(parts[0])
    title = parts[1] if len(parts) > 1 and parts[1] else None
    body = parts[2] if len(parts) > 2 and parts[2] else None
    tags = parts[3] if len(parts) > 3 and parts[3] else None
    ok = await db.faq_edit(fid, title=title, body=body, tags=tags)
    await message.answer(tr("kb_admin_updated", message.from_user.id) if ok else tr("common_not_found", message.from_user.id))


# -------------------------
# ERROR HANDLER
# -------------------------


@router.errors()
async def on_error(event, exception=None):
    """Global error handler.

    aiogram v3 can call error handlers either as (event) where event is ErrorEvent
    and the exception is available as event.exception, or as (event, exception)
    in some setups/middlewares.

    We support both signatures to avoid handler crashes masking the real error.
    """

    exc = exception
    if exc is None and hasattr(event, "exception"):
        exc = getattr(event, "exception")

    logger.error("Unhandled exception: %s", exc)
    traceback.print_exc()


# -------------------------
# SCHEDULER
# -------------------------


async def scheduler_loop(bot: Bot):
    """Background loop: reminders + daily digest."""
    last_digest_sent: dict[int, str] = {}  # user_id -> YYYY-MM-DD

    while True:
        try:
            now_ts = time.time()
            due = await db.pop_due_reminders(now_ts)
            for r in due:
                try:
                    await bot.send_message(r.user_id, tr("reminder_push", r.user_id, text=r.text))
                except Exception:
                    continue

            # Daily digest: once per day at configured time (Oslo)
            now_local = datetime.now(TZ)
            if now_local.hour == DAILY_DIGEST_HOUR and now_local.minute == DAILY_DIGEST_MINUTE:
                today = now_local.date().isoformat()
                digest_users = db.get_daily_digest_users()
                digest_text = db.get_daily_digest_message()
                for uid in digest_users:
                    if last_digest_sent.get(uid) == today:
                        continue
                    if db.is_banned(uid):
                        continue
                    try:
                        await bot.send_message(uid, f"🗞 {digest_text}")
                        last_digest_sent[uid] = today
                    except Exception:
                        continue

        except Exception as e:
            logger.error("Scheduler error: %s", e)

        # 30s tick is enough
        await asyncio.sleep(30)


# -------------------------
# MAIN
# -------------------------


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Put it in .env or environment variables.")

    await db.init_db(BOT_DB)

    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Background scheduler
    asyncio.create_task(scheduler_loop(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())