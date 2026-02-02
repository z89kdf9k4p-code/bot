import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import get_user, save_user, save_feedback, cleanup_feedback
from states import LanguageState, Register, FeedbackState
from keyboards import LANG_KB, role_kb, shop_kb, main_menu
from translations import tr, get_user_lang

BOT_TOKEN = "8413248579:AAH_AuRcm3yLP6O38w6z-O_SmUq9pZDviHA"
ADMINS = [1242801964]


# ---------- Хэндлеры ----------
async def start(message: Message, state: FSMContext):
    cleanup_feedback()
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(tr("welcome"))
        await message.answer(tr("welcome"), reply_markup=LANG_KB)
        await state.set_state(LanguageState.lang)
        return

    lang = get_user_lang(message.from_user.id)
    role, shop = user[2], user[3]

    if role and shop:
        await message.answer(
            f"{tr('role_confirm', user_id=message.from_user.id)} {role}, ТТ: {shop}\n"
            f"{tr('help', user_id=message.from_user.id)}",
            reply_markup=main_menu(role, user_id=message.from_user.id)
        )
    else:
        await message.answer(
            tr("role_prompt", user_id=message.from_user.id),
            reply_markup=role_kb
        )
        await state.set_state(Register.role)


async def set_language(message: Message, state: FSMContext):
    text = message.text.strip().upper()

    if text not in {"RU", "EN", "UZ", "TJ", "KG"}:
        await message.answer(
            "Пожалуйста, выбери язык с кнопок 👇",
            reply_markup=LANG_KB
        )
        return

    save_user(
        message.from_user.id,
        message.from_user.username,
        lang=text
    )

    await state.clear()

    await message.answer(
        tr("lang_updated", user_id=message.from_user.id),
        reply_markup=role_kb
    )


async def change_language(message: Message, state: FSMContext):
    await message.answer(
        tr("choose_language", user_id=message.from_user.id),
        reply_markup=LANG_KB
    )
    await state.set_state(LanguageState.lang)


async def set_role(message: Message, state: FSMContext):
    await state.update_data(role=message.text.lower())
    await message.answer(
        tr("choose_shop", user_id=message.from_user.id),
        reply_markup=shop_kb
    )
    await state.set_state(Register.shop)


async def set_shop(message: Message, state: FSMContext):
    data = await state.get_data()
    role = data["role"]
    shop = message.text

    save_user(
        message.from_user.id,
        message.from_user.username,
        role=role,
        shop=shop,
        lang=get_user_lang(message.from_user.id)
    )

    await message.answer(
        f"{tr('role_confirm', user_id=message.from_user.id)} {role}, ТТ: {shop}. "
        f"{tr('help', user_id=message.from_user.id)}",
        reply_markup=main_menu(role, user_id=message.from_user.id)
    )
    await state.clear()


async def feedback_start(message: Message, state: FSMContext):
    await message.answer(tr("feedback", user_id=message.from_user.id))
    await state.set_state(FeedbackState.text)


async def save_feedback_handler(message: Message, state: FSMContext):
    save_feedback(message.from_user.id, message.text)
    await message.answer(tr("feedback_thanks", user_id=message.from_user.id))
    await state.clear()


# ---------- Запуск ----------
async def main():
    bot = Bot(BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start, Command("start"))
    dp.message.register(set_language, StateFilter(LanguageState.lang))
    dp.message.register(change_language, F.text.contains("🌐"))
    dp.message.register(set_role, StateFilter(Register.role))
    dp.message.register(set_shop, StateFilter(Register.shop))
    dp.message.register(feedback_start, F.text.contains(tr("feedback", user_id=None)))
    dp.message.register(save_feedback_handler, StateFilter(FeedbackState.text))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
