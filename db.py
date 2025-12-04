import sqlite3

conn = sqlite3.connect('bot.db')
cursor = conn.cursor()

# ------------------ Таблица пользователей ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ------------------ Таблица всех слов ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    lang_code TEXT NOT NULL
)
""")

# ------------------ Связь пользователя с конкретными словами ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS personwords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    word_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(word_id) REFERENCES words(id)
)
""")

# ------------------ Таблица для быстрого словаря бота ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS vocab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    word TEXT,
    translation_en TEXT,
    translation_ko TEXT
)
""")

conn.commit()
conn.close()
print("Все таблицы созданы!")
