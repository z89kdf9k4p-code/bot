from aiogram.fsm.state import StatesGroup, State

# ===== Выбор языка =====
class LanguageState(StatesGroup):
    lang = State()

# ===== Регистрация пользователя =====
class Register(StatesGroup):
    role = State()
    shop = State()

# ===== Обратная связь =====
class FeedbackState(StatesGroup):
    text = State()
