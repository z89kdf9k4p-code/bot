from aiogram.fsm.state import StatesGroup, State

# ===== Выбор языка =====
class LanguageState(StatesGroup):
    lang = State()

# ===== Регистрация пользователя =====
class Register(StatesGroup):
    phone = State()
    role = State()
    shop = State()

# ===== Обратная связь =====
class FeedbackState(StatesGroup):
    text = State()

# ===== FAQ поиск =====
class FAQState(StatesGroup):
    query = State()

# ===== Напоминания =====
class ReminderState(StatesGroup):
    minutes = State()
    text = State()


# ===== Управление обучалками (админ) =====
class TrainingAdminState(StatesGroup):
    action = State()      # add/edit/delete
    title = State()
    body = State()
    tags = State()
    target_id = State()
