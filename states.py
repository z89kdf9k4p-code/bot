from aiogram.fsm.state import StatesGroup, State

class LanguageState(StatesGroup):
    lang = State()

class Register(StatesGroup):
    role = State()
    shop = State()

class FeedbackState(StatesGroup):
    text = State()
