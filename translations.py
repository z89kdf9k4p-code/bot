T = {
    "welcome": {
        "RU": "Привет! Я нейронные связи из головы супервайзера Ахмеда. Выбери язык:",
        "EN": "Hi! I'm Ahmed's supervisor neural links. Choose your language:",
        "UZ": "Salom! Men Ahmedning nazoratchi neyron bog'lari. Tilni tanlang:",
        "TJ": "Салом! Ман пайвандҳои асаби назоратгари Ахмед. Забонро интихоб кунед:",
        "KG": "Салам! Мен Ахмеддин супервайзери нейрон байланышымын. Тилди тандаңыз:"
    },
    "role_prompt": {
        "RU": "Выбери свою роль:", "EN": "Choose your role:", "UZ": "Rolni tanlang:",
        "TJ": "Ролатонро интихоб кунед:", "KG": "Ролуңузду тандаңыз:"
    },
    "choose_shop": {
        "RU": "Выбери торговую точку:", "EN": "Choose your main shop:",
        "UZ": "Asosiy savdo nuqtangizni tanlang:", "TJ": "Фурӯшгоҳи асосии худро интихоб кунед:",
        "KG": "Башкы соода чектеңизди тандаңыз:"
    },
    "role_confirm": {
        "RU": "Отлично! Твоя роль", "EN": "Great! Your role is", "UZ": "Zo'r! Sizning rolingiz",
        "TJ": "Аъло! Роли шумо", "KG": "Супер! Сиздин ролуңуз"
    },
    "help": {
        "RU": "Чем могу помочь?", "EN": "What can I help you with?", "UZ": "Sizga nima yordam bera olaman?",
        "TJ": "Чӣ гуна ман ба шумо кӯмак карда метавонам?", "KG": "Эмне жардам бере алам?"
    },
    "feedback_thanks": {"RU":"Спасибо за отзыв! 🙌","EN":"Thank you for your feedback! 🙌","UZ":"Fikringiz uchun rahmat! 🙌","TJ":"Ташаккур барои фикратон! 🙌","KG":"Пикириңиз үчүн рахмат! 🙌"},
    "choose_language": {"RU":"Выберите язык:","EN":"Choose language:","UZ":"Tilni tanlang:","TJ":"Забонро интихоб кунед:","KG":"Тилди тандаңыз:"},
    "lang_updated": {"RU":"Язык обновлён ✅","EN":"Language updated ✅","UZ":"Til yangilandi ✅","TJ":"Забон нав карда шуд ✅","KG":"Тил жаңыртылды ✅"},
    "training":{"RU":"Обучалки новичкам","EN":"Training","UZ":"Yangi boshlanuvchilar","TJ":"Омӯзиш","KG":"Жаңы баштагандар"},
    "urgent_problem":{"RU":"Срочная проблема 🚨","EN":"Urgent problem 🚨","UZ":"Tezkor muammo 🚨","TJ":"Муаммои саривақтӣ 🚨","KG":"Тез жардам 🚨"},
    "supervisor_contacts":{"RU":"Контакты супервайзера","EN":"Supervisor contacts","UZ":"Nazoratchi kontaktlari","TJ":"Тамос бо назоратчӣ","KG":"Супервайзер байланыштары"},
    "chat_links":{"RU":"Ссылки на чаты","EN":"Chat links","UZ":"Chat havolalari","TJ":"Ссылка ба чат","KG":"Чат шилтемелери"},
    "feedback":{"RU":"Оставить предложение","EN":"Feedback","UZ":"Fikringizni qoldiring","TJ":"Фикр гузоред","KG":"Пикир калтырыңыз"},
    "change_lang":{"RU":"Сменить язык","EN":"Change language","UZ":"Tilni o'zgartirish","TJ":"Забонро иваз кунед","KG":"Тилди өзгөртүү"},
    "assembly_rating":{"RU":"Рейтинг сборки","EN":"Assembly rating","UZ":"Yig‘ish reytingi","TJ":"Рейтинги ҷамъоварӣ","KG":"Жыйноо рейтинги"}
}

from db import get_user

def get_user_lang(user_id):
    user = get_user(user_id)
    return user[4] if user and user[4] else "RU"

def tr(key, user_id=None, lang=None):
    if user_id:
        lang = get_user_lang(user_id)
    if not lang:
        lang = "RU"
    return T.get(key, {}).get(lang, key)