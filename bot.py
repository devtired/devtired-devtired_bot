import asyncio
import random
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- КОНФИГ ---
API_TOKEN = '8472036941:AAEXRFyKTE9wZaxwW3VhCuiS22GYH2opzeM'
ADMIN_ID = 6981304315  

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class Feedback(StatesGroup):
    waiting_for_answer = State()

# --- ССЫЛКИ ---
PLAYLIST_URL = "https://open.spotify.com/playlist/0XGGQ0iphsvxp3b3q0cEHN?si=f0e926c1ba114016"
DONATE_DA = "https://www.donationalerts.com/r/devarovfwk1"
DONATE_MONO = "https://send.monobank.ua/ATvzoHF1sG"

# --- ЛОКАЛИЗАЦИЯ ---
LANGS = {
    'ru': {
        'start': "Привет\n\nЯ посредник. Пиши сообщение, я передам его владельцу. Если будет время — отвечу.",
        'profile': "👤 Профиль",
        'faq': "💬 Вопросы",
        'playlist': "🎵 Плейлист",
        'donate': "💸 Поддержать",
        'change_lang': "🌐 Сменить язык",
        'back': "← Назад",
        'reg_date': "Дата входа",
        'ans_sent': "Отправлено",
        'faq_text': (
            "─── **ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ** ───\n\n"
            "🔹 **Кто ты?**\n"
            "Живу в Германии, учу немецкий. Программирую для себя. 🧑‍💻\n\n"
            "🔹 **Писать второй раз?**\n"
            "Нет смысла. Если не ответил сразу — не отвечу и потом. 🌑\n\n"
            "🔹 **Почему такой вайб?**\n"
            "Бот живет как я — ненавидя жизнь и серую массу, которую называют людьми. 🌫\n\n"
            "🔹 **Что за музыка?**\n"
            "Меланхоличное инди, lofi и slowed треки. То, что помогает вывозить. 🎧\n\n"
            "🔹 **Можно подружиться?**\n"
            "Вряд ли. 🧱\n\n"
            "🔹 **Что делаешь в свободное время?**\n"
            "Сплю. 💤"
        ),
        'playlist_text': "🎶 **Loser**\n\nМой Spotify плейлист. Нажми кнопку ниже.",
        'donate_text': "🏦 **Донат**\n\nЕсли есть желание поддержать:",
        'reject': "Сейчас нет возможности для диалога"
    },
    'en': {
        'start': "Hi\n\nI'm a proxy. Send a message, I'll forward it. I'll reply if I have time.",
        'profile': "👤 Profile",
        'faq': "💬 FAQ",
        'playlist': "🎵 Playlist",
        'donate': "💸 Support",
        'change_lang': "🌐 Change language",
        'back': "← Back",
        'reg_date': "Joined date",
        'ans_sent': "Sent",
        'faq_text': (
            "─── **FREQUENTLY ASKED QUESTIONS** ───\n\n"
            "🔹 **Who are you?**\n"
            "Living in Germany, learning German. Code for myself. 🧑‍💻\n\n"
            "🔹 **Double text?**\n"
            "No point. If I didn't reply once, I won't at all. 🌑\n\n"
            "🔹 **Why this vibe?**\n"
            "The bot lives like me — hating life and the grey mass called humans. 🌫\n\n"
            "🔹 **Music?**\n"
            "Melancholic indie, lofi and slowed tracks. Stuff to survive the day. 🎧\n\n"
            "🔹 **Can we be friends?**\n"
            "Unlikely. 🧱\n\n"
            "🔹 **Free time?**\n"
            "I sleep. 💤"
        ),
        'playlist_text': "🎶 **Loser**\n\nMy Spotify playlist. Button below.",
        'donate_text': "🏦 **Donate**\n\nIf you want to support:",
        'reject': "No possibility for dialogue right now"
    }
}


# --- СИСТЕМА ДАННЫХ ---
def get_user_info(user_id):
    try:
        with open("users_data.txt", "r") as f:
            for line in f:
                uid, lang, date = line.strip().split('|')
                if uid == str(user_id): return lang, date
    except: pass
    return None, None

def save_user_info(user_id, lang=None, date=None):
    users = {}
    try:
        with open("users_data.txt", "r") as f:
            for line in f:
                uid, l, d = line.strip().split('|')
                users[uid] = [l, d]
    except: pass
    
    if str(user_id) not in users:
        users[str(user_id)] = [lang or 'ru', date or datetime.now().strftime("%d.%m.%Y")]
    else:
        if lang: users[str(user_id)][0] = lang
        if date: users[str(user_id)][1] = date

    with open("users_data.txt", "w") as f:
        for uid, val in users.items():
            f.write(f"{uid}|{val[0]}|{val[1]}\n")

def is_banned(user_id):
    try:
        with open("blacklist.txt", "r") as f:
            return str(user_id) in f.read().splitlines()
    except: return False

def ban_user(user_id):
    if not is_banned(user_id):
        with open("blacklist.txt", "a") as f: f.write(f"{user_id}\n")

def unban_user(user_id):
    if is_banned(user_id):
        with open("blacklist.txt", "r") as f: lines = f.readlines()
        with open("blacklist.txt", "w") as f:
            for line in lines:
                if line.strip() != str(user_id): f.write(line)

# --- КЛАВИАТУРЫ ---
def get_lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="RU 🇷🇺", callback_data="setlang_ru"),
         InlineKeyboardButton(text="EN 🇺🇸", callback_data="setlang_en")]
    ])

def get_main_menu(lang):
    l = LANGS[lang]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l['profile'], callback_data="profile"),
         InlineKeyboardButton(text=l['faq'], callback_data="faq")],
        [InlineKeyboardButton(text=l['playlist'], callback_data="playlist_menu"),
         InlineKeyboardButton(text=l['donate'], callback_data="donate_menu")],
        [InlineKeyboardButton(text=l['change_lang'], callback_data="change_language_process")]
    ])

def get_admin_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Ответить", callback_data=f"ans_{user_id}")],
        [InlineKeyboardButton(text="🥀 Отстать", callback_data=f"stfu_{user_id}"),
         InlineKeyboardButton(text="🚫 В бан", callback_data=f"ban_{user_id}")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_banned(message.from_user.id): return
    lang, date = get_user_info(message.from_user.id)
    if not lang:
        await message.answer("Choose language / Выберите язык:", reply_markup=get_lang_kb())
    else:
        await message.answer(LANGS[lang]['start'], reply_markup=get_main_menu(lang))

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    save_user_info(call.from_user.id, lang=lang)
    await call.message.edit_text(LANGS[lang]['start'], reply_markup=get_main_menu(lang))

@dp.callback_query(F.data == "change_language_process")
async def change_lang_btn(call: types.CallbackQuery):
    await call.message.edit_text("Choose language / Выберите язык:", reply_markup=get_lang_kb())

@dp.callback_query(F.data == "main_menu")
async def back_to_main(call: types.CallbackQuery):
    lang, date = get_user_info(call.from_user.id)
    lang = lang or 'ru'
    await call.message.edit_text(LANGS[lang]['start'], reply_markup=get_main_menu(lang))

@dp.callback_query(F.data == "playlist_menu")
async def show_playlist(call: types.CallbackQuery):
    lang, date = get_user_info(call.from_user.id)
    lang = lang or 'ru'
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎧 Spotify", url=PLAYLIST_URL)],
        [InlineKeyboardButton(text=LANGS[lang]['back'], callback_data="main_menu")]
    ])
    await call.message.edit_text(LANGS[lang]['playlist_text'], reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "donate_menu")
async def show_donate(call: types.CallbackQuery):
    lang, date = get_user_info(call.from_user.id)
    lang = lang or 'ru'
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="DA (RU/INT)", url=DONATE_DA)],
        [InlineKeyboardButton(text="Monobank (UA)", url=DONATE_MONO)],
        [InlineKeyboardButton(text=LANGS[lang]['back'], callback_data="main_menu")]
    ])
    await call.message.edit_text(LANGS[lang]['donate_text'], reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "profile")
async def show_profile(call: types.CallbackQuery):
    lang, date = get_user_info(call.from_user.id)
    lang = lang or 'ru'
    text = (f"🆔 **{LANGS[lang]['profile']}**\n\n"
            f"Ник — {call.from_user.full_name}\n"
            f"ID — `{call.from_user.id}`\n"
            f"{LANGS[lang]['reg_date']} — {date}")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANGS[lang]['back'], callback_data="main_menu")]])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "faq")
async def show_faq(call: types.CallbackQuery):
    lang, date = get_user_info(call.from_user.id)
    lang = lang or 'ru'
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANGS[lang]['back'], callback_data="main_menu")]])
    await call.message.edit_text(LANGS[lang]['faq_text'], reply_markup=kb, parse_mode="Markdown")

@dp.message(F.chat.id != ADMIN_ID)
async def handle_msg(message: types.Message):
    if is_banned(message.from_user.id): return
    lang, date = get_user_info(message.from_user.id)
    lang = lang or 'ru'
    header = f"👤 {message.from_user.full_name} | `{message.from_user.id}`"
    content = f"`{message.text}`" if message.text else "[Media]"
    await bot.send_message(ADMIN_ID, f"{header}\n\n{content}", reply_markup=get_admin_kb(message.from_user.id), parse_mode="Markdown")
    await message.reply(LANGS[lang]['ans_sent'])

# --- АДМИНКА ---

@dp.callback_query(F.data.startswith("ban_"))
async def process_ban(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    ban_user(user_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Разблокировать", callback_data=f"unban_{user_id}")]])
    await call.message.edit_text(text=f"🚫 Юзер {user_id} заблокирован.", reply_markup=kb)

@dp.callback_query(F.data.startswith("unban_"))
async def process_unban(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    unban_user(user_id)
    await call.message.edit_text(text=f"✅ Юзер {user_id} разблокирован.")

@dp.callback_query(F.data.startswith("stfu_"))
async def process_stfu(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    lang, date = get_user_info(user_id)
    lang = lang or 'ru'
    try:
        await bot.send_message(user_id, LANGS[lang]['reject'])
        await call.answer("Sent")
    except: await call.answer("Error")

@dp.callback_query(F.data.startswith("ans_"))
async def start_ans(call: types.CallbackQuery, state: FSMContext):
    user_id = int(call.data.split("_")[1])
    await state.update_data(target_id=user_id)
    await state.set_state(Feedback.waiting_for_answer)
    await call.message.answer(f"💬 Ответ для {user_id}:")
    await call.answer()

@dp.message(Feedback.waiting_for_answer, F.from_user.id == ADMIN_ID)
async def send_ans(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        await message.copy_to(data['target_id'])
        await message.answer("🚀 Отправлено")
    except: await message.answer("❌ Ошибка")
    await state.clear()

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
