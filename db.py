# ===== SQLite-backed "БД" + кэш в памяти =====
# Цель: данные переживают перезапуск бота, но чтения быстрые (из кэша).
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import aiosqlite
import re
import difflib

# ----------------------------
# Глобальное состояние
# ----------------------------
_DB_PATH: str = "bot.db"
_db: aiosqlite.Connection | None = None
_db_lock = asyncio.Lock()

# Кэши (используются синхронными функциями чтения — удобно для переводов/кнопок)
users_db: dict[int, tuple[int, str | None, str | None, str | None, str, str | None]] = {}
feedback_db: list[tuple[int, str, datetime]] = []
banned_users: set[int] = set()

# FAQ: храним с id, чтобы можно было удалять/редактировать
FAQ_ARTICLES: list[dict[str, str]] = []  # {"id": "1", "title": "...", "body": "...", "tags": "a,b"}

# Планировщик
@dataclass
class Reminder:
    id: int
    run_at_ts: float
    user_id: int
    text: str

reminders: list[Reminder] = []
daily_digest_users: set[int] = set()
daily_digest_message: str = "Ежедневный дайджест: проверьте обновления в «Обучалки» и «Ссылки»."


# ----------------------------
# SQLite helpers
# ----------------------------

async def _fetchone(conn: aiosqlite.Connection, query: str, params: tuple = ()) -> aiosqlite.Row | None:
    async with conn.execute(query, params) as cur:
        return await cur.fetchone()

async def _fetchall(conn: aiosqlite.Connection, query: str, params: tuple = ()) -> list[aiosqlite.Row]:
    async with conn.execute(query, params) as cur:
        return await cur.fetchall()

async def _execute(conn: aiosqlite.Connection, query: str, params: tuple = ()) -> None:
    await conn.execute(query, params)
    await conn.commit()

# ----------------------------
# Init / schema
# ----------------------------
SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  role TEXT,
  shop TEXT,
  lang TEXT NOT NULL,
  phone TEXT
);

CREATE TABLE IF NOT EXISTS banned_users (
  user_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  text TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  run_at_ts REAL NOT NULL,
  text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_digest_users (
  user_id INTEGER PRIMARY KEY,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS faq (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  tags TEXT DEFAULT '',
  created_at TEXT NOT NULL
);
"""

DEFAULT_FAQ = [
    ("Как начать работу", "Нажмите /start и пройдите регистрацию: язык → роль → точка.", "start,registration"),
    ("Куда писать при проблемах", "Используйте меню «Контакты супервайзера» или «Обратная связь».", "support,feedback"),
    ("Где взять ссылки", "В меню нажмите «Ссылки» — они зависят от вашей точки.", "links"),
    ("Основные правила", "• Соблюдайте технику безопасности\n• Следуйте инструкциям супервайзера\n• Проверяйте заказы перед выдачей/выездом", "training,Курьер,Сборщик"),
    ("Погрузка", "• Аккуратно размещайте товары\n• Тяжёлое — вниз\n• Хрупкое — сверху\n• Проверяйте целостность", "training,Курьер"),
    ("Подключение терминала", "• Включите терминал\n• Проверьте интернет\n• Войдите в приложение\n• Проведите тестовую операцию", "training,Курьер,Сборщик"),
    ("Правила сборки", "• Собирайте по списку\n• Проверяйте сроки годности\n• Хрупкое упаковывайте отдельно", "training,Сборщик"),
    ("Возвраты", "• Зафиксируйте причину\n• Сфотографируйте при необходимости\n• Сообщите старшему смены", "training,Курьер,Сборщик"),
    ("Закрытие точки", "• Сверьте остатки\n• Уберите рабочее место\n• Сообщите о проблемах супервайзеру", "training,Сборщик"),
]


async def init_db(db_path: str = "bot.db") -> None:
    """
    1) Открывает SQLite
    2) Создаёт таблицы
    3) Загружает кэши в память
    """
    global _DB_PATH, _db
    _DB_PATH = db_path

    async with _db_lock:
        if _db is None:
            _db = await aiosqlite.connect(_DB_PATH)
            _db.row_factory = aiosqlite.Row
            await _db.executescript(SCHEMA_SQL)
            await _db.commit()
            # --- миграции схемы (безопасно для существующей БД) ---
            cur = await _db.execute("PRAGMA table_info(users)")
            rows = await cur.fetchall()
            await cur.close()
            cols = [r["name"] for r in rows]
            if "phone" not in cols:
                await _db.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                await _db.commit()

    # первичная инициализация дефолтов
    await _ensure_defaults()
    await _reload_caches()


async def close_db() -> None:
    global _db
    async with _db_lock:
        if _db is not None:
            await _db.close()
            _db = None


async def _ensure_defaults() -> None:
    assert _db is not None

    # daily digest message
    row = await _fetchone(_db, "SELECT value FROM settings WHERE key='daily_digest_message'")
    if row is None:
        await _db.execute(
            "INSERT OR REPLACE INTO settings(key,value) VALUES('daily_digest_message', ?)",
            (daily_digest_message,),
        )

    # FAQ defaults: only if empty
    row = await _fetchone(_db, "SELECT COUNT(1) AS c FROM faq")
    if row["c"] == 0:
        now = datetime.now(timezone.utc).isoformat()
        await _db.executemany(
            "INSERT INTO faq(title, body, tags, created_at) VALUES(?,?,?,?)",
            [(t, b, tags, now) for (t, b, tags) in DEFAULT_FAQ],
        )

    await _db.commit()


async def _reload_caches() -> None:
    """Загружает все нужные сущности в кэш."""
    assert _db is not None

    users_db.clear()
    banned_users.clear()
    feedback_db.clear()
    reminders.clear()
    daily_digest_users.clear()
    FAQ_ARTICLES.clear()

    async with _db.execute("SELECT user_id, username, role, shop, lang, phone FROM users") as cur:
        async for r in cur:
            users_db[int(r["user_id"])] = (int(r["user_id"]), r["username"], r["role"], r["shop"], r["lang"], r["phone"])

    async with _db.execute("SELECT user_id FROM banned_users") as cur:
        async for r in cur:
            banned_users.add(int(r["user_id"]))

    async with _db.execute("SELECT user_id, text, created_at FROM feedback ORDER BY id DESC LIMIT 500") as cur:
        async for r in cur:
            # хранить datetime в UTC
            try:
                ts = datetime.fromisoformat(r["created_at"])
            except Exception:
                ts = datetime.now(timezone.utc)
            feedback_db.append((int(r["user_id"]), r["text"], ts))

    async with _db.execute("SELECT id, user_id, run_at_ts, text FROM reminders ORDER BY run_at_ts ASC") as cur:
        async for r in cur:
            reminders.append(Reminder(id=int(r["id"]), user_id=int(r["user_id"]), run_at_ts=float(r["run_at_ts"]), text=r["text"]))

    async with _db.execute("SELECT user_id FROM daily_digest_users WHERE enabled=1") as cur:
        async for r in cur:
            daily_digest_users.add(int(r["user_id"]))

    row = await _fetchone(_db, "SELECT value FROM settings WHERE key='daily_digest_message'")
    global daily_digest_message
    if row and row["value"]:
        daily_digest_message = str(row["value"])

    async with _db.execute("SELECT id, title, body, tags FROM faq ORDER BY id ASC") as cur:
        async for r in cur:
            FAQ_ARTICLES.append(
                {"id": str(r["id"]), "title": r["title"], "body": r["body"], "tags": r["tags"] or ""}
            )

# ----------------------------
# Sync READ API (кэш)
# ----------------------------
def get_user(user_id: int):
    return users_db.get(user_id)

def get_all_users():
    return list(users_db.values())

def is_banned(user_id: int) -> bool:
    return user_id in banned_users

def get_feedback():
    return list(feedback_db)

def get_daily_digest_users() -> set[int]:
    return set(daily_digest_users)

def get_daily_digest_message() -> str:
    return daily_digest_message

# ----------------------------
# Async WRITE API (SQLite + кэш)
# ----------------------------
async def save_user(user_id: int, username: str | None, role: str | None = None, shop: str | None = None, lang: str = "RU", phone: str | None = None):
    assert _db is not None
    await _db.execute(
        "INSERT INTO users(user_id, username, role, shop, lang, phone) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, role=excluded.role, shop=excluded.shop, lang=excluded.lang, phone=COALESCE(excluded.phone, users.phone)",
        (user_id, username, role, shop, lang, phone),
    )
    await _db.commit()
    prev = users_db.get(user_id)
    cache_phone = phone if phone is not None else (prev[5] if prev and len(prev) > 5 else None)
    users_db[user_id] = (user_id, username, role, shop, lang, cache_phone)

async def ban_user(user_id: int):
    assert _db is not None
    await _db.execute("INSERT OR REPLACE INTO banned_users(user_id) VALUES(?)", (user_id,))
    await _db.commit()
    banned_users.add(user_id)

async def unban_user(user_id: int):
    assert _db is not None
    await _db.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,))
    await _db.commit()
    banned_users.discard(user_id)

async def save_feedback(user_id: int, text: str):
    assert _db is not None
    created = datetime.now(timezone.utc).isoformat()
    await _db.execute("INSERT INTO feedback(user_id, text, created_at) VALUES(?,?,?)", (user_id, text, created))
    await _db.commit()
    # кэш: держим максимум 500
    feedback_db.insert(0, (user_id, text, datetime.fromisoformat(created)))
    del feedback_db[500:]

async def cleanup_feedback(user_id: int | None = None):
    assert _db is not None
    global feedback_db
    if user_id is not None:
        await _db.execute("DELETE FROM feedback WHERE user_id=?", (user_id,))
        feedback_db = [f for f in feedback_db if f[0] != user_id]
    else:
        await _db.execute("DELETE FROM feedback")
        feedback_db = []
    await _db.commit()

async def add_reminder(user_id: int, run_at_ts: float, text: str):
    assert _db is not None
    cur = await _db.execute("INSERT INTO reminders(user_id, run_at_ts, text) VALUES(?,?,?)", (user_id, run_at_ts, text))
    await _db.commit()
    rid = cur.lastrowid or 0
    reminders.append(Reminder(id=int(rid), user_id=user_id, run_at_ts=run_at_ts, text=text))
    reminders.sort(key=lambda r: r.run_at_ts)

async def pop_due_reminders(now_ts: float) -> list[Reminder]:
    """
    Достаём из SQLite и кэша напоминания, которые пора отправить.
    Возвращаем список Reminder и удаляем их из БД.
    """
    assert _db is not None
    due_ids: list[int] = []
    due: list[Reminder] = []
    # кэш уже отсортирован по времени
    while reminders and reminders[0].run_at_ts <= now_ts:
        r = reminders.pop(0)
        due.append(r)
        due_ids.append(r.id)

    if due_ids:
        q_marks = ",".join(["?"] * len(due_ids))
        await _db.execute(f"DELETE FROM reminders WHERE id IN ({q_marks})", tuple(due_ids))
        await _db.commit()
    return due

async def enable_daily_digest(user_id: int, enabled: bool):
    assert _db is not None
    if enabled:
        await _db.execute("INSERT OR REPLACE INTO daily_digest_users(user_id, enabled) VALUES(?,1)", (user_id,))
        daily_digest_users.add(user_id)
    else:
        await _db.execute("DELETE FROM daily_digest_users WHERE user_id=?", (user_id,))
        daily_digest_users.discard(user_id)
    await _db.commit()

async def set_daily_digest_message(text: str):
    assert _db is not None
    global daily_digest_message
    new_text = (text or "").strip()
    if not new_text:
        return
    daily_digest_message = new_text
    await _db.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('daily_digest_message', ?)",
        (daily_digest_message,),
    )
    await _db.commit()

# ----------------------------
# FAQ: CRUD + поиск
# ----------------------------
async def faq_add(title: str, body: str, tags: str = "") -> int:
    assert _db is not None
    now = datetime.now(timezone.utc).isoformat()
    cur = await _db.execute("INSERT INTO faq(title, body, tags, created_at) VALUES(?,?,?,?)", (title, body, tags, now))
    await _db.commit()
    fid = int(cur.lastrowid or 0)
    FAQ_ARTICLES.append({"id": str(fid), "title": title, "body": body, "tags": tags})
    return fid

async def faq_delete(faq_id: int) -> bool:
    assert _db is not None
    await _db.execute("DELETE FROM faq WHERE id=?", (faq_id,))
    await _db.commit()
    before = len(FAQ_ARTICLES)
    FAQ_ARTICLES[:] = [a for a in FAQ_ARTICLES if int(a.get("id","0")) != int(faq_id)]
    return len(FAQ_ARTICLES) != before

async def faq_list(limit: int = 50) -> list[dict[str, str]]:
    # возвращаем копию
    return list(FAQ_ARTICLES[:limit])


def materials_for_role(role: str | None = None, limit: int = 30) -> list[dict[str, str]]:
    """Список материалов для роли (использует кэш FAQ_ARTICLES).

    Правило фильтрации по тегам:
    - если tags пустые -> показываем всем
    - если role задан -> показываем статьи, где role встречается в tags (case-insensitive)
    - также всегда показываем статьи с тегом 'training' или 'kb'
    """
    role_norm = (role or "").strip().lower()
    out: list[dict[str, str]] = []
    for a in FAQ_ARTICLES:
        tags = (a.get("tags") or "").lower()
        if not tags:
            out.append(a)
            continue
        if "training" in tags or "kb" in tags:
            if not role_norm or role_norm in tags:
                out.append(a)
            else:
                # training без указания роли — показываем всем
                if any(r in tags for r in ["курьер", "сборщик"]) is False:
                    out.append(a)
            continue
        if role_norm and role_norm in tags:
            out.append(a)

    # сортируем по title для стабильности
    out.sort(key=lambda x: (x.get("title") or "").lower())
    return out[:limit]

async def faq_edit(faq_id: int, title: str | None = None, body: str | None = None, tags: str | None = None) -> bool:
    assert _db is not None
    # найдём текущее
    cur = await _fetchone(_db, "SELECT id, title, body, tags FROM faq WHERE id=?", (faq_id,))
    if cur is None:
        return False
    new_title = title if title is not None else cur["title"]
    new_body = body if body is not None else cur["body"]
    new_tags = tags if tags is not None else (cur["tags"] or "")
    await _db.execute("UPDATE faq SET title=?, body=?, tags=? WHERE id=?", (new_title, new_body, new_tags, faq_id))
    await _db.commit()
    # обновим кэш
    for a in FAQ_ARTICLES:
        if int(a.get("id","0")) == int(faq_id):
            a["title"] = new_title
            a["body"] = new_body
            a["tags"] = new_tags
            break
    return True


def _tokenize(s: str) -> list[str]:
    return [t for t in re.split(r"[^0-9A-Za-zА-Яа-яЁё]+", (s or "").lower()) if t]

def _token_set_ratio(a: str, b: str) -> float:
    # Простая метрика "похожести" без сторонних зависимостей:
    # 1) token overlap
    # 2) difflib ratio
    ta, tb = set(_tokenize(a)), set(_tokenize(b))
    if not ta or not tb:
        overlap = 0.0
    else:
        overlap = len(ta & tb) / max(len(ta), len(tb))
    seq = difflib.SequenceMatcher(a=a.lower(), b=b.lower()).ratio()
    return 0.55 * overlap + 0.45 * seq


def search_faq(query: str, limit: int = 5) -> list[dict[str, str]]:
    """
    "Умный" поиск:
    - token overlap (устойчив к перестановкам/частичным совпадениям)
    - difflib SequenceMatcher (ловит опечатки/похожие фразы)
    - учитываем title/body/tags
    """
    q = (query or "").strip()
    if not q:
        return []

    scored: list[tuple[float, dict[str, str]]] = []
    for art in FAQ_ARTICLES:
        title = art.get("title", "")
        body = art.get("body", "")
        tags = art.get("tags", "")
        hay = f"{title}\n{body}\n{tags}"
        score = _token_set_ratio(q, hay)
        # небольшая надбавка, если совпало в заголовке
        score += 0.10 * _token_set_ratio(q, title)
        if score > 0.15:
            scored.append((score, art))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:limit]]
