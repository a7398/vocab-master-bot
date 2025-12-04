import telebot
import sqlite3
from deep_translator import GoogleTranslator
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8362433533:AAFyQGD1BXITGQpb2_M9W4dvCg6AQjpiQTE'
bot = telebot.TeleBot(API_TOKEN)

# ------------------ БАЗА ------------------
def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    """)
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

def register_user(username):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if user:
        conn.close()
        return user[0]
    cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def add_word(user_id, word, en, ko):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vocab (user_id, word, translation_en, translation_ko) VALUES (?, ?, ?, ?)",
        (user_id, word, en, ko)
    )
    conn.commit()
    conn.close()

def delete_word(user_id, word):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vocab WHERE user_id=? AND word=?", (user_id, word))
    conn.commit()
    conn.close()

def get_vocab(user_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT word, translation_en, translation_ko FROM vocab WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ------------------ ПЕРЕВОД ------------------
def detect_language(text: str):
    text = text.strip()
    if any('\uAC00' <= ch <= '\uD7AF' for ch in text):
        return 'ko'
    elif any('\u0400' <= ch <= '\u04FF' for ch in text):
        return 'ru'
    elif any('A' <= ch <= 'z' for ch in text):
        return 'en'
    return 'en'

def translate(text, target_lang):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except:
        return f"[не удалось перевести на {target_lang}]"

# ------------------ СТАРТОВОЕ МЕНЮ ------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = register_user(message.from_user.username)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌐 Перевести слово", "📚 Мой словарь", "❌ Удалить слово")
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.username}! ✨\nВыбери действие:",
        reply_markup=markup
    )

# ------------------ ОБРАБОТКА МЕНЮ ------------------
user_states = {}  # user_id -> состояние ("translate" или "delete")

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    user_id = register_user(message.from_user.username)
    state = user_states.get(user_id)

    if state == "translate":
        user_states[user_id] = None
        process_translate(message, user_id)
        return
    elif state == "delete":
        user_states[user_id] = None
        delete_word_step(message, user_id)
        return

    if message.text == "🌐 Перевести слово":
        bot.send_message(message.chat.id, "Напиши слово или фразу:")
        user_states[user_id] = "translate"
    elif message.text == "📚 Мой словарь":
        words = get_vocab(user_id)
        if not words:
            bot.send_message(message.chat.id, "Словарь пуст 😢")
        else:
            text = ""
            for w, en, ko in words:
                text += f"📌 {w}\n🇬🇧 {en}\n🇰🇷 {ko}\n\n"
            bot.send_message(message.chat.id, text)
    elif message.text == "❌ Удалить слово":
        bot.send_message(message.chat.id, "Какое слово удалить?")
        user_states[user_id] = "delete"
    else:
        bot.send_message(message.chat.id, "Выбери действие кнопками.")

# ------------------ ПЕРЕВОД И КНОПКИ ------------------
def process_translate(message, user_id):
    text = message.text.strip()
    src_lang = detect_language(text)
    targets = [l for l in ("en","ru","ko") if l != src_lang]
    translations = {lang: translate(text, lang) for lang in targets}

    # Показываем переводы
    output = f"📝 Исходный текст ({src_lang}): {text}\n\n"
    for lang, flag in [('en','🇬🇧'),('ru','🇷🇺'),('ko','🇰🇷')]:
        if lang in translations:
            output += f"{flag} {translations[lang]}\n"
    bot.send_message(message.chat.id, output)

    # Кнопки для копирования
    markup = InlineKeyboardMarkup()
    for lang, flag in [('en','🇬🇧'),('ru','🇷🇺'),('ko','🇰🇷')]:
        if lang in translations:
            markup.add(InlineKeyboardButton(f"{flag} Скопировать", callback_data=f"copy|{translations[lang]}"))
    bot.send_message(message.chat.id, "Нажми кнопку, чтобы скопировать перевод:", reply_markup=markup)

    # Сохраняем в словарь EN и KO
    add_word(user_id, text, translations.get('en',''), translations.get('ko',''))

# ------------------ CALLBACK COPY ------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("copy|"))
def callback_copy(call):
    _, text = call.data.split("|",1)
    bot.answer_callback_query(call.id, "Скопировано!")
    bot.send_message(call.message.chat.id, f"📋 {text}")

# ------------------ УДАЛЕНИЕ ------------------
def delete_word_step(message, user_id):
    word = message.text.strip()
    delete_word(user_id, word)
    bot.send_message(message.chat.id, f"Слово '{word}' удалено.")

# ------------------ ЗАПУСК ------------------
init_db()
print("Бот запущен...")
bot.infinity_polling()
