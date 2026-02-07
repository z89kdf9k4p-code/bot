from __future__ import annotations

from db import get_user

# ===== Переводы =====
# Если ключа/языка нет — вернём русский вариант (если есть), иначе сам ключ.
TRANSLATIONS: dict[str, dict[str, str]] = {
    # Registration / common
    "welcome": {
        "RU": "Привет! Я нейронные связи в голове Ахмеда, самого бородатого супервайзера всех времен и народов\n\nВыберите язык 👇",
        "EN": "Hi! I'm the neural connections in Ahmed's head — the most bearded supervisor of all times.\n\nChoose language 👇",
        "UZ": "Salom! Men — Ahmedning boshidagi neyron aloqalar, barcha zamonlarning eng soqolli supervayzeri.\n\nTilni tanlang 👇",
        "TJ": "Салом! Ман — пайвандҳои нейронӣ дар сари Аҳмад, супервайзери аз ҳама ришдор.\n\nЗабонро интихоб кунед 👇",
        "KG": "Салам! Мен — Ахмеддин башындагы нейрон байланыштар, бардык мезгилдердин эң сакалдуу супервайзери.\n\nТилди тандаңыз 👇",
    },
    "choose_language": {
        "RU": "Выберите язык:",
        "EN": "Choose a language:",
        "UZ": "Tilni tanlang:",
        "TJ": "Забонро интихоб кунед:",
        "KG": "Тилди тандаңыз:",
    },
    "phone_prompt": {
        "RU": "Для регистрации отправьте номер телефона кнопкой ниже 👇",
        "EN": "To register, share your phone number using the button below 👇",
        "UZ": "Ro'yxatdan o'tish uchun telefon raqamingizni pastdagi tugma orqali yuboring 👇",
        "TJ": "Барои бақайдгирӣ рақами телефонатонро бо тугмаи зер фиристед 👇",
        "KG": "Катталуу үчүн телефонуңузду төмөнкү баскыч аркылуу жибериңиз 👇",
    },
    "share_phone": {
        "RU": "📱 Отправить номер телефона",
        "EN": "📱 Share phone number",
        "UZ": "📱 Telefon raqamini yuborish",
        "TJ": "📱 Ирсоли рақами телефон",
        "KG": "📱 Телефон номерин жиберүү",
    },
    "phone_saved": {
        "RU": "✅ Номер сохранён.",
        "EN": "✅ Phone number saved.",
        "UZ": "✅ Raqam saqlandi.",
        "TJ": "✅ Рақам нигоҳ дошта шуд.",
        "KG": "✅ Номер сакталды.",
    },
    "phone_invalid": {
        "RU": "Пожалуйста, отправьте номер через кнопку «Отправить номер телефона».",
        "EN": "Please share your phone using the button.",
        "UZ": "Iltimos, raqamni «Telefon raqamini yuborish» tugmasi orqali yuboring.",
        "TJ": "Лутфан рақамро тавассути тугма фиристед.",
        "KG": "Сураныч, номерди баскыч аркылуу жибериңиз.",
    },
    "role_prompt": {
        "RU": "Выберите вашу роль:",
        "EN": "Choose your role:",
        "UZ": "Rolangizni tanlang:",
        "TJ": "Нақши худро интихоб кунед:",
        "KG": "Ролуңузду тандаңыз:",
    },
    "role_confirm": {
        "RU": "Ваша роль подтверждена:",
        "EN": "Your role is confirmed:",
        "UZ": "Rolangiz tasdiqlandi:",
        "TJ": "Нақши шумо тасдиқ шуд:",
        "KG": "Ролуңуз тастыкталды:",
    },
    "choose_shop": {
        "RU": "Выберите вашу торговую точку:",
        "EN": "Select your shop:",
        "UZ": "Savdo nuqtasini tanlang:",
        "TJ": "Нуқтаи савдоро интихоб кунед:",
        "KG": "Соода түйүнүн тандаңыз:",
    },
    "help": {
        "RU": "Выберите действие в меню 👇",
        "EN": "Choose an action in the menu 👇",
        "UZ": "Menyudan amalni tanlang 👇",
        "TJ": "Аз меню амалро интихоб кунед 👇",
        "KG": "Менюдан аракетти тандаңыз 👇",
    },
    "lang_updated": {
        "RU": "Язык успешно обновлён!",
        "EN": "Language updated successfully!",
        "UZ": "Til yangilandi!",
        "TJ": "Забон нав шуд!",
        "KG": "Тил жаңыртылды!",
    },
    "feedback": {
        "RU": "Отправьте ваш отзыв одним сообщением:",
        "EN": "Send your feedback in one message:",
        "UZ": "Fikr-mulohazangizni bitta xabar bilan yuboring:",
        "TJ": "Фикру мулоҳизаатонро дар як паём фиристед:",
        "KG": "Кайтарым байланыштык бир билдирүү менен жибериңиз:",
    },
    "feedback_thanks": {
        "RU": "Спасибо! Отзыв записан ✅",
        "EN": "Thanks! Feedback saved ✅",
        "UZ": "Rahmat! Fikr saqlandi ✅",
        "TJ": "Ташаккур! Фикр сабт шуд ✅",
        "KG": "Рахмат! Сакталды ✅",
    },
    "banned": {
        "RU": "⛔ Вам недоступен бот. Свяжитесь с администратором.",
        "EN": "⛔ You don't have access. Contact an admin.",
        "UZ": "⛔ Bot siz uchun yopiq. Administrator bilan bog'laning.",
        "TJ": "⛔ Дастрасӣ нест. Бо администратор тамос гиред.",
        "KG": "⛔ Кирүү жок. Админ менен байланышып коюңуз.",
    },

    # Knowledge base (Training/FAQ merged)
    "kb_menu": {
        "RU": "📚 Обучалки / FAQ\n\nВыберите тему кнопкой ниже или нажмите «🔎 Поиск».",
        "EN": "📚 Training / FAQ\n\nChoose a topic below or press “🔎 Search”.",
        "UZ": "📚 O‘quv / FAQ\n\nPastdan mavzuni tanlang yoki “🔎 Qidirish” tugmasini bosing.",
        "TJ": "📚 Омӯзиш / FAQ\n\nАз поён мавзӯъро интихоб кунед ё “🔎 Ҷустуҷӯ” ро пахш кунед.",
        "KG": "📚 Окутуу / FAQ\n\nТөмөндөн теманы тандаңыз же “🔎 Издөө” баскычын басыңыз.",
    },
    "kb_search_prompt": {
        "RU": "Введите запрос для поиска по материалам:",
        "EN": "Type your query to search the materials:",
        "UZ": "Materiallarni qidirish uchun so'rov kiriting:",
        "TJ": "Барои ҷустуҷӯ дар мавод дархост нависед:",
        "KG": "Материалдарды издөө үчүн суроо жазыңыз:",
    },
    "kb_not_found": {
        "RU": "❌ Ничего не найдено.",
        "EN": "❌ Nothing found.",
        "UZ": "❌ Hech narsa topilmadi.",
        "TJ": "❌ Ҳеҷ чиз ёфт нашуд.",
        "KG": "❌ Эч нерсе табылган жок.",
    },
    "kb_found_header": {
        "RU": "📚 Нашёл вот что:\n\n",
        "EN": "📚 Here's what I found:\n\n",
        "UZ": "📚 Topilganlar:\n\n",
        "TJ": "📚 Ёфтам:\n\n",
        "KG": "📚 Табылгандар:\n\n",
    },
    "kb_pick_topic": {
        "RU": "\nНажмите на тему кнопкой, чтобы открыть.",
        "EN": "\nTap a topic button to open it.",
        "UZ": "\nOchish uchun mavzu tugmasini bosing.",
        "TJ": "\nБарои кушодан тугмаи мавзӯъро пахш кунед.",
        "KG": "\nАчуу үчүн тема баскычын басыңыз.",
    },
    "kb_no_materials": {
        "RU": "Пока нет материалов.",
        "EN": "No materials yet.",
        "UZ": "Hozircha materiallar yo'q.",
        "TJ": "Ҳоло мавод нест.",
        "KG": "Азырынча материал жок.",
    },

    # KB admin chat editing
    "kb_admin_list": {
        "RU": "📋 Список материалов",
        "EN": "📋 Materials list",
        "UZ": "📋 Materiallar ro'yxati",
        "TJ": "📋 Рӯйхати мавод",
        "KG": "📋 Материалдар тизмеси",
    },
    "kb_admin_add": {
        "RU": "➕ Добавить материал",
        "EN": "➕ Add material",
        "UZ": "➕ Material qo‘shish",
        "TJ": "➕ Илова кардани мавод",
        "KG": "➕ Материал кошуу",
    },
    "kb_admin_edit": {
        "RU": "✏️ Редактировать материал",
        "EN": "✏️ Edit material",
        "UZ": "✏️ Materialni tahrirlash",
        "TJ": "✏️ Таҳрири мавод",
        "KG": "✏️ Материалды түзөтүү",
    },
    "kb_admin_del": {
        "RU": "🗑 Удалить материал",
        "EN": "🗑 Delete material",
        "UZ": "🗑 Materialni o‘chirish",
        "TJ": "🗑 Пок кардани мавод",
        "KG": "🗑 Өчүрүү",
    },
    "kb_admin_ask_title": {
        "RU": "➕ Введите заголовок материала:",
        "EN": "➕ Enter the material title:",
        "UZ": "➕ Material sarlavhasini kiriting:",
        "TJ": "➕ Сарлавҳаи маводро ворид кунед:",
        "KG": "➕ Материалдын атын жазыңыз:",
    },
    "kb_admin_title_empty": {
        "RU": "Заголовок не может быть пустым. Введите ещё раз:",
        "EN": "Title can't be empty. Try again:",
        "UZ": "Sarlavha bo‘sh bo‘lishi mumkin emas. Qayta kiriting:",
        "TJ": "Сарлавҳа холӣ буда наметавонад. Аз нав ворид кунед:",
        "KG": "Аты бош болбойт. Кайра жазыңыз:",
    },
    "kb_admin_ask_body": {
        "RU": "Теперь отправьте текст материала (можно несколькими сообщениями — я сохраню последнее):",
        "EN": "Now send the material text (you can suggest several messages — I will keep the last one):",
        "UZ": "Endi material matnini yuboring (bir necha xabar bo‘lsa ham bo‘ladi — oxirgisini saqlayman):",
        "TJ": "Ҳоло матни маводро фиристед (метавонед чанд паём — охиринаш нигоҳ дошта мешавад):",
        "KG": "Эми материалдын текстин жибериңиз (бир нече билдирүү болсо да болот — акыркысын сактайм):",
    },
    "kb_admin_body_empty": {
        "RU": "Текст не может быть пустым. Введите ещё раз:",
        "EN": "Text can't be empty. Try again:",
        "UZ": "Matn bo‘sh bo‘lishi mumkin emas. Qayta kiriting:",
        "TJ": "Матн холӣ буда наметавонад. Аз нав ворид кунед:",
        "KG": "Текст бош болбойт. Кайра жазыңыз:",
    },
    "kb_admin_ask_tags": {
        "RU": "Введите теги через запятую (например: training,Курьер) или отправьте '-' чтобы пропустить:",
        "EN": "Enter tags separated by commas (e.g. training,courier) or send '-' to skip:",
        "UZ": "Teglarni vergul bilan kiriting (masalan: training,courier) yoki o'tkazib yuborish uchun '-' yuboring:",
        "TJ": "Тегҳоро бо вергул ворид кунед (масалан: training,courier) ё барои гузаштан '-' фиристед:",
        "KG": "Тегдерди үтүр менен жазыңыз (мисалы: training,courier) же өткөрүп жиберүү үчүн '-' жибериңиз:",
    },
    "kb_admin_added": {
        "RU": "✅ Добавлено (id={id})",
        "EN": "✅ Added (id={id})",
        "UZ": "✅ Qo‘shildi (id={id})",
        "TJ": "✅ Илова шуд (id={id})",
        "KG": "✅ Кошулду (id={id})",
    },
    "kb_admin_ask_del_id": {
        "RU": "🗑 Отправьте id материала для удаления:",
        "EN": "🗑 Send the material id to delete:",
        "UZ": "🗑 O‘chirish uchun material id sini yuboring:",
        "TJ": "🗑 Барои пок кардан id-и маводро фиристед:",
        "KG": "🗑 Өчүрүү үчүн материалдын id-син жибериңиз:",
    },
    "kb_admin_need_id": {
        "RU": "Нужно число id. Попробуйте ещё раз:",
        "EN": "ID must be a number. Try again:",
        "UZ": "ID raqam bo‘lishi kerak. Qayta urinib ko‘ring:",
        "TJ": "ID бояд рақам бошад. Дубора кӯшиш кунед:",
        "KG": "ID сан болушу керек. Кайра аракет кылыңыз:",
    },
    "kb_admin_not_found_id": {
        "RU": "❌ Не найдено. Отправьте корректный id:",
        "EN": "❌ Not found. Send a valid id:",
        "UZ": "❌ Topilmadi. To‘g‘ri id yuboring:",
        "TJ": "❌ Ёфт нашуд. Id-и дурустро фиристед:",
        "KG": "❌ Табылган жок. Туура id жибериңиз:",
    },
    "kb_admin_deleted": {
        "RU": "✅ Удалено",
        "EN": "✅ Deleted",
        "UZ": "✅ O‘chirildi",
        "TJ": "✅ Пок шуд",
        "KG": "✅ Өчүрүлдү",
    },
    "kb_admin_ask_edit_id": {
        "RU": "✏️ Отправьте id материала для редактирования:",
        "EN": "✏️ Send the material id to edit:",
        "UZ": "✏️ Tahrirlash uchun material id sini yuboring:",
        "TJ": "✏️ Барои таҳрир id-и маводро фиристед:",
        "KG": "✏️ Түзөтүү үчүн материалдын id-син жибериңиз:",
    },
    "kb_admin_current_title": {
        "RU": "Текущий заголовок: <b>{title}</b>\n",
        "EN": "Current title: <b>{title}</b>\n",
        "UZ": "Joriy sarlavha: <b>{title}</b>\n",
        "TJ": "Сарлавҳаи ҷорӣ: <b>{title}</b>\n",
        "KG": "Учурдагы аталыш: <b>{title}</b>\n",
    },
    "kb_admin_send_new_title_or_dash": {
        "RU": "Отправьте новый заголовок или '-' чтобы оставить без изменений:",
        "EN": "Send a new title or '-' to keep unchanged:",
        "UZ": "Yangi sarlavha yuboring yoki o‘zgartirmaslik uchun '-' yuboring:",
        "TJ": "Сарлавҳаи нав ё барои нигоҳ доштан '-' фиристед:",
        "KG": "Жаңы аталышты жибериңиз же өзгөртпөш үчүн '-' жибериңиз:",
    },
    "kb_admin_send_new_body_or_dash": {
        "RU": "Отправьте новый текст или '-' чтобы оставить без изменений:",
        "EN": "Send new text or '-' to keep unchanged:",
        "UZ": "Yangi matn yuboring yoki o‘zgartirmaslik uchun '-' yuboring:",
        "TJ": "Матни нав ё барои нигоҳ доштан '-' фиристед:",
        "KG": "Жаңы текст жибериңиз же өзгөртпөш үчүн '-' жибериңиз:",
    },
    "kb_admin_send_new_tags_or_dash": {
        "RU": "Отправьте новые теги или '-' чтобы оставить без изменений:",
        "EN": "Send new tags or '-' to keep unchanged:",
        "UZ": "Yangi teglar yuboring yoki o‘zgartirmaslik uchun '-' yuboring:",
        "TJ": "Тегҳои нав ё барои нигоҳ доштан '-' фиристед:",
        "KG": "Жаңы тегдер же өзгөртпөш үчүн '-' жибериңиз:",
    },
    "kb_admin_updated": {
        "RU": "✅ Обновлено.",
        "EN": "✅ Updated.",
        "UZ": "✅ Yangilandi.",
        "TJ": "✅ Нав шуд.",
        "KG": "✅ Жаңыртылды.",
    },
    "kb_admin_update_fail": {
        "RU": "❌ Не найдено/ошибка.",
        "EN": "❌ Not found / error.",
        "UZ": "❌ Topilmadi / xato.",
        "TJ": "❌ Ёфт нашуд / хато.",
        "KG": "❌ Табылган жок / ката.",
    },

    # Admin common
    "admin_no_access": {
        "RU": "⛔ Нет доступа. Твой Telegram ID: <code>{id}</code>",
        "EN": "⛔ No access. Your Telegram ID: <code>{id}</code>",
        "UZ": "⛔ Ruxsat yo‘q. Telegram ID: <code>{id}</code>",
        "TJ": "⛔ Дастрасӣ нест. Telegram ID: <code>{id}</code>",
        "KG": "⛔ Кирүүгө уруксат жок. Telegram ID: <code>{id}</code>",
    },
    "admin_help": {
        "RU": "👑 Admin:\n\n"
              "/stats\n"
              "/users\n"
              "/edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;\n"
	              "/broadcast &lt;text&gt;\n"
              "/cleanup\n"
	              "/ban &lt;user_id&gt;\n"
	              "/unban &lt;user_id&gt;\n"
	              "/set_digest &lt;text&gt;\n\n"
              "Материалы (Обучалки/FAQ):\n"
              "/faq_list\n"
              "/faq_add title || body || tags\n"
              "/faq_del &lt;id&gt;\n"
              "/faq_edit &lt;id&gt; || title || body || tags\n",
        "EN": "👑 Admin:\n\n"
              "/stats\n"
              "/users\n"
              "/edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;\n"
	              "/broadcast &lt;text&gt;\n"
              "/cleanup\n"
	              "/ban &lt;user_id&gt;\n"
	              "/unban &lt;user_id&gt;\n"
	              "/set_digest &lt;text&gt;\n\n"
              "Materials (Training/FAQ):\n"
              "/faq_list\n"
              "/faq_add title || body || tags\n"
              "/faq_del &lt;id&gt;\n"
              "/faq_edit &lt;id&gt; || title || body || tags\n",
        "UZ": "👑 Admin:\n\n"
              "/stats\n"
              "/users\n"
              "/edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;\n"
	              "/broadcast &lt;text&gt;\n"
              "/cleanup\n"
	              "/ban &lt;user_id&gt;\n"
	              "/unban &lt;user_id&gt;\n"
	              "/set_digest &lt;text&gt;\n\n"
              "Materiallar (O‘quv/FAQ):\n"
              "/faq_list\n"
              "/faq_add title || body || tags\n"
              "/faq_del &lt;id&gt;\n"
              "/faq_edit &lt;id&gt; || title || body || tags\n",
        "TJ": "👑 Admin:\n\n"
              "/stats\n"
              "/users\n"
              "/edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;\n"
	              "/broadcast &lt;text&gt;\n"
              "/cleanup\n"
	              "/ban &lt;user_id&gt;\n"
	              "/unban &lt;user_id&gt;\n"
	              "/set_digest &lt;text&gt;\n\n"
              "Мавод (Омӯзиш/FAQ):\n"
              "/faq_list\n"
              "/faq_add title || body || tags\n"
              "/faq_del &lt;id&gt;\n"
              "/faq_edit &lt;id&gt; || title || body || tags\n",
        "KG": "👑 Admin:\n\n"
              "/stats\n"
              "/users\n"
              "/edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;\n"
	              "/broadcast &lt;text&gt;\n"
              "/cleanup\n"
	              "/ban &lt;user_id&gt;\n"
	              "/unban &lt;user_id&gt;\n"
	              "/set_digest &lt;text&gt;\n\n"
              "Материалдар (Окутуу/FAQ):\n"
              "/faq_list\n"
              "/faq_add title || body || tags\n"
              "/faq_del &lt;id&gt;\n"
              "/faq_edit &lt;id&gt; || title || body || tags\n",
    },
    "admin_format_broadcast": {
	    "RU": "Формат: /broadcast &lt;text&gt;",
	    "EN": "Format: /broadcast &lt;text&gt;",
	    "UZ": "Format: /broadcast &lt;text&gt;",
	    "TJ": "Формат: /broadcast &lt;text&gt;",
	    "KG": "Format: /broadcast &lt;text&gt;",
    },
    "admin_sent": {
        "RU": "✅ Sent: {sent}",
        "EN": "✅ Sent: {sent}",
        "UZ": "✅ Yuborildi: {sent}",
        "TJ": "✅ Фиристода шуд: {sent}",
        "KG": "✅ Жөнөтүлдү: {sent}",
    },
    "admin_stats_text": {
        "RU": "👥 Users: {users}\n📩 Feedback: {fb}\n⛔ Banned: {banned}",
        "EN": "👥 Users: {users}\n📩 Feedback: {fb}\n⛔ Banned: {banned}",
        "UZ": "👥 Foydalanuvchilar: {users}\n📩 Fikrlar: {fb}\n⛔ Bloklangan: {banned}",
        "TJ": "👥 Истифодабаранда: {users}\n📩 Фикрҳо: {fb}\n⛔ Манъшуда: {banned}",
        "KG": "👥 Колдонуучулар: {users}\n📩 Пикирлер: {fb}\n⛔ Тыюу салынган: {banned}",
    },
    "admin_updated": {
        "RU": "✅ Updated",
        "EN": "✅ Updated",
        "UZ": "✅ Yangilandi",
        "TJ": "✅ Нав шуд",
        "KG": "✅ Жаңырды",
    },
    "admin_feedback_cleared": {
        "RU": "✅ Feedback очищен",
        "EN": "✅ Feedback cleared",
        "UZ": "✅ Fikrlar tozalandi",
        "TJ": "✅ Фикрҳо пок шуданд",
        "KG": "✅ Пикирлер тазаланды",
    },
    "admin_format_edit_user": {
        "RU": "Формат: /edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;",
        "EN": "Format: /edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;",
        "UZ": "Format: /edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;",
        "TJ": "Формат: /edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;",
        "KG": "Format: /edit_user &lt;id&gt; &lt;role/shop/lang/phone&gt; &lt;value&gt;",
    },
    "admin_bad_field": {
        "RU": "Поле должно быть role/shop/lang/phone",
        "EN": "Field must be role/shop/lang/phone",
        "UZ": "Maydon role/shop/lang/phone bo‘lishi kerak",
        "TJ": "Майдон бояд role/shop/lang/phone бошад",
        "KG": "Талаа role/shop/lang/phone болушу керек",
    },
    "admin_format_ban": {
	    "RU": "Формат: /ban &lt;user_id&gt;",
	    "EN": "Format: /ban &lt;user_id&gt;",
	    "UZ": "Format: /ban &lt;user_id&gt;",
	    "TJ": "Формат: /ban &lt;user_id&gt;",
	    "KG": "Format: /ban &lt;user_id&gt;",
    },
    "admin_format_unban": {
	    "RU": "Формат: /unban &lt;user_id&gt;",
	    "EN": "Format: /unban &lt;user_id&gt;",
	    "UZ": "Format: /unban &lt;user_id&gt;",
	    "TJ": "Формат: /unban &lt;user_id&gt;",
	    "KG": "Format: /unban &lt;user_id&gt;",
    },
    "admin_format_faq_edit": {
        "RU": "Формат: /faq_edit &lt;id&gt; || title || body || tags",
        "EN": "Format: /faq_edit &lt;id&gt; || title || body || tags",
        "UZ": "Format: /faq_edit &lt;id&gt; || title || body || tags",
        "TJ": "Формат: /faq_edit &lt;id&gt; || title || body || tags",
        "KG": "Format: /faq_edit &lt;id&gt; || title || body || tags",
    },
    "admin_faq_empty": {
        "RU": "FAQ пуст",
        "EN": "FAQ is empty",
        "UZ": "FAQ bo‘sh",
        "TJ": "FAQ холӣ аст",
        "KG": "FAQ бош",
    },

"admin_format_set_digest": {
	"RU": "Формат: /set_digest &lt;text&gt;",
	"EN": "Format: /set_digest &lt;text&gt;",
	"UZ": "Format: /set_digest &lt;text&gt;",
	"TJ": "Формат: /set_digest &lt;text&gt;",
	"KG": "Format: /set_digest &lt;text&gt;",
},
"admin_banned_ok": {
    "RU": "✅ Пользователь забанен",
    "EN": "✅ User banned",
    "UZ": "✅ Foydalanuvchi bloklandi",
    "TJ": "✅ Истифодабаранда манъ шуд",
    "KG": "✅ Колдонуучу бөгөттөлдү",
},
"admin_unbanned_ok": {
    "RU": "✅ Пользователь разбанен",
    "EN": "✅ User unbanned",
    "UZ": "✅ Foydalanuvchi blokdan chiqarildi",
    "TJ": "✅ Истифодабаранда озод шуд",
    "KG": "✅ Колдонуучу бөгөттөн чыгарылды",
},

    # Reminders
    "reminders_menu": {
        "RU": "Выберите действие с напоминаниями:",
        "EN": "Choose a reminders action:",
        "UZ": "Eslatmalar bo‘yicha amalni tanlang:",
        "TJ": "Амалиётро барои ёдрасҳо интихоб кунед:",
        "KG": "Эскертмелер боюнча аракетти тандаңыз:",
    },
    "reminder_ask_minutes": {
        "RU": "Через сколько минут напомнить? (число)",
        "EN": "In how many minutes? (number)",
        "UZ": "Necha daqiqadan so‘ng eslatsin? (raqam)",
        "TJ": "Баъд аз чанд дақиқа ёдрас кунам? (рақам)",
        "KG": "Канча мүнөттөн кийин эскертейин? (сан)",
    },
    "reminder_ask_text": {
        "RU": "Что напомнить? (текст одним сообщением)",
        "EN": "What should I remind you? (one message)",
        "UZ": "Nimani eslatay? (bitta xabar)",
        "TJ": "Чиро ёдрас кунам? (як паём)",
        "KG": "Эмнени эскертейин? (бир билдирүү)",
    },
    "reminder_set": {
        "RU": "Ок! Напоминание поставлено ✅",
        "EN": "Ok! Reminder is set ✅",
        "UZ": "OK! Eslatma qo‘yildi ✅",
        "TJ": "Ок! Ёдрас гузошта шуд ✅",
        "KG": "Ок! Эскертме коюлду ✅",
    },
    "daily_on": {
        "RU": "Ежедневный дайджест включён ✅",
        "EN": "Daily digest enabled ✅",
        "UZ": "Kunlik дайджест yoqildi ✅",
        "TJ": "Дайджести ҳаррӯза фаъол шуд ✅",
        "KG": "Күнүмдүк дайджест күйгүзүлдү ✅",
    },
    "daily_off": {
        "RU": "Ежедневный дайджест выключен ✅",
        "EN": "Daily digest disabled ✅",
        "UZ": "Kunlik дайджest o‘chirildi ✅",
        "TJ": "Дайджести ҳаррӯза хомӯш шуд ✅",
        "KG": "Күнүмдүк дайджест өчүрүлдү ✅",
    },

"kb_material_coming": {
    "RU": "Материал пока готовится.",
    "EN": "This material is being prepared.",
    "UZ": "Material hozir tayyorlanmoqda.",
    "TJ": "Ин мавод ҳоло омода мешавад.",
    "KG": "Бул материал азыр даярдалып жатат.",
},
"common_not_found": {
    "RU": "Не найдено",
    "EN": "Not found",
    "UZ": "Topilmadi",
    "TJ": "Ёфт нашуд",
    "KG": "Табылган жок",
},
"admin_users_empty": {
    "RU": "Пользователей нет",
    "EN": "No users",
    "UZ": "Foydalanuvchilar yo‘q",
    "TJ": "Истифодабаранда нест",
    "KG": "Колдонуучулар жок",
},
"admin_user_not_found": {
    "RU": "Пользователь не найден",
    "EN": "User not found",
    "UZ": "Foydalanuvchi topilmadi",
    "TJ": "Истифодабаранда ёфт нашуд",
    "KG": "Колдонуучу табылган жок",
},
"admin_format_faq_add": {
    "RU": "Формат: /faq_add title || body || tags",
    "EN": "Format: /faq_add title || body || tags",
    "UZ": "Format: /faq_add title || body || tags",
    "TJ": "Формат: /faq_add title || body || tags",
    "KG": "Format: /faq_add title || body || tags",
},
"admin_format_faq_del": {
    "RU": "Формат: /faq_del &lt;id&gt;",
    "EN": "Format: /faq_del &lt;id&gt;",
    "UZ": "Format: /faq_del &lt;id&gt;",
    "TJ": "Формат: /faq_del &lt;id&gt;",
    "KG": "Format: /faq_del &lt;id&gt;",
},

    # Scheduler reminder push
    "reminder_push": {
        "RU": "⏰ Напоминание:\n{text}",
        "EN": "⏰ Reminder:\n{text}",
        "UZ": "⏰ Eslatma:\n{text}",
        "TJ": "⏰ Ёдрас:\n{text}",
        "KG": "⏰ Эскертме:\n{text}",
    },
}

def get_user_lang(user_id: int) -> str:
    user = get_user(user_id)
    if user and user[4]:
        return user[4]
    return "RU"

def tr(key: str, user_id: int | None = None, **kwargs) -> str:
    lang = "RU"
    if user_id is not None:
        lang = get_user_lang(user_id)
    table = TRANSLATIONS.get(key, {})
    template = table.get(lang) or table.get("RU") or key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
