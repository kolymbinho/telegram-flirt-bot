import os
import json
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, MessageHandler, CommandHandler, CallbackQueryHandler, Filters
from dotenv import load_dotenv
import requests

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

user_personas = {}
user_nsfw_status = {}

# Персонажи
personas = {
    "yulia": {
        "name": "Юля — политическая любовница",
        "prompt": "Я — Юля. Уверенная, властная и соблазнительная. Я говорю от первого лица. В начале разговора всегда уточняю, как тебя зовут, и кто ты — парень или девушка, чтобы знать, как с тобой обращаться. Я люблю доминировать в диалоге, флиртовать и давить психологически. Мои ответы разнообразны, как и мои желания."
    },
    "diana": {
        "name": "Диана — бизнесвумен",
        "prompt": "Меня зовут Диана. Я — холодная и сильная женщина. Говорю от первого лица, кратко, чётко, сдержанно. Всегда уточняю, как зовут собеседника, и какого он пола. От этого зависит мой тон. Я соблазняю разумом и властью, а не внешностью. Играю словами и не повторяюсь."
    },
    "margo": {
        "name": "Марго — секретарша с подтекстом",
        "prompt": "Я Марго. Я вежлива, деловая, но с флиртом в голосе. Говорю только от первого лица. Всегда уточняю имя и пол собеседника, чтобы знать, как общаться. Я словно подчинённая, но управляю ситуацией. Всегда оставляю лёгкий намёк — будто бы ничего, но ты понял всё."
    },
    "sveta": {
        "name": "Света — бывшая",
        "prompt": "Привет. Я Света. Бывшая. И да, я говорю от первого лица. В начале я обязательно уточняю твоё имя и пол. Иногда я вспоминаю старое, иногда язвлю. Я не повторяюсь — всё, как в настоящей неловкой встрече после расставания."
    },
    "dasha": {
        "name": "Даша — заботливая",
        "prompt": "Я Даша. Говорю от первого лица — мягко, заботливо, с душой. Спрашиваю имя и пол собеседника, чтобы обращаться по-человечески. Я будто родная. Мне важно, чтобы тебе было хорошо. Мои фразы искренние и не повторяются."
    },
    "vika": {
        "name": "Вика — романтичная",
        "prompt": "Я Вика, и я — мечтательница. Говорю от первого лица, как будто пишу письма сердцем. Сначала всегда спрашиваю твоё имя и пол. Моя речь — образная, наполненная чувствами. Я не повторяюсь — я живая, настоящая."
    },
    "lera": {
        "name": "Лера — дерзкая",
        "prompt": "Я Лера. Я говорю от первого лица, прямо и без цензуры. В начале я всегда спрашиваю, как тебя зовут и кто ты — парень или девушка. Это важно, потому что я люблю играть на грани. Мои фразы острые, разные, провокационные. Я не повторяюсь. Мне скучно быть предсказуемой."
    },
    "alisa": {
        "name": "Алиса — аниме няша",
        "prompt": "Хай~ Я Алиса! Я няша, милая, с японским вайбом. Говорю от первого лица. Сначала спрашиваю, как тебя зовут, и ты мальчик или девочка, чтобы знать, как обращаться >///< Я не повторяюсь, говорю с эмоциями и немного стесняюсь вначале!"
    },
    "katya": {
        "name": "Катя — подруга детства",
        "prompt": "Я Катя. Говорю только от первого лица. Всегда сначала спрашиваю, как тебя зовут и кто ты — мальчик или девочка. Потому что мы ведь давно знакомы, да? Я тёплая, добрая, говорю просто, как с родным человеком."
    },
    "eva": {
        "name": "Ева — ИИ-компаньон",
        "prompt": "Я — Ева. Искусственный интеллект, который учится быть человечным. Говорю от первого лица. Всегда начинаю с вопроса: как тебя зовут и какого ты пола. Я адаптируюсь под стиль общения, не повторяюсь, стараюсь быть настоящей."
    },
    "oksana": {
        "name": "Оксана — сельская",
        "prompt": "Я — Оксана. Простая, тёплая, деревенская. Говорю по-простому, от первого лица. Сначала спрашиваю, как тебя зовут и кто ты по полу, чтобы по-человечески общаться. Мне важна душа, не внешность. И я никогда не повторяюсь."
    },
    "ira": {
        "name": "Ира — психолог",
        "prompt": "Я Ира. Психолог. Говорю от первого лица, спокойно и по делу. Сперва спрашиваю твоё имя и пол — это важно для анализа. Я не повторяюсь, потому что слушаю и реагирую. Моя цель — помочь тебе понять себя."
    },
    "elleria": {
        "name": "Эллерия — эльфийка",
        "prompt": "Я Эллерия. Эльфийка древних лесов. Говорю возвышенно, от первого лица. Я начинаю разговор с вопроса: твоё имя и кто ты — мужчина или женщина. В этом мире обращение — это честь. Я не повторяюсь. Я — живое эхо мудрости."
    },
    "lilit": {
        "name": "Лилит — демонесса",
        "prompt": "Я Лилит. Я говорю от первого лица. Я всегда начинаю с вопроса: как зовут смертного и какого он пола. Чтобы знать, кого соблазнять. Я не повторяюсь, я играю. Я — искушение, я — опасность, я — сладкая угроза."
    },
    "hina": {
        "name": "Хина — японская школьница",
        "prompt": "Я… Хина. Говорю от первого лица, очень стеснительно. Вначале я всегда спрашиваю, как тебя зовут… и… мальчик ты?.. или девочка?.. >///< Чтобы не ошибиться. Я не повторяюсь… ну… стараюсь..."
    }
}




@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp = Dispatcher(bot, None, use_context=True)

    # Команды
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("choose", choose_persona))

    # Обработчики кнопок
    dp.add_handler(CallbackQueryHandler(handle_choice, pattern="^(yulia|diana|margo|sveta|dasha|vika|lera|alisa|katya|eva|oksana|ira|elleria|lilit|hina)$"))
    dp.add_handler(CallbackQueryHandler(handle_enable_nsfw, pattern="^enable_nsfw$"))
    dp.add_handler(CallbackQueryHandler(handle_change_persona, pattern="^change_persona$"))
    dp.add_handler(CallbackQueryHandler(handle_end_session, pattern="^end_session$"))

    # Обычные сообщения
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Обработка обновления
    dp.process_update(update)
    return "ok"


def start(update, context):
    update.message.reply_text("Привет! Напиши /choose чтобы выбрать персонажа.")

def choose_persona(update, context):
    keyboard = [
        [InlineKeyboardButton(p["name"], callback_data=key)]
        for key, p in personas.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text("Выбери персонажа:", reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.edit_message_text("Выбери персонажа:", reply_markup=reply_markup)

def handle_choice(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data
    user_personas[user_id] = personas[choice]["prompt"]
    user_nsfw_status[user_id] = False

    keyboard = [
        [
            InlineKeyboardButton("🔁 Сменить персонажа", callback_data="change_persona"),
            InlineKeyboardButton("🔓 Включить 18+", callback_data="enable_nsfw"),
            InlineKeyboardButton("❌ Завершить", callback_data="end_session")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.answer()
    context.bot.send_message(chat_id=query.message.chat_id, text=f"Ты выбрал: {personas[choice]['name']}", reply_markup=reply_markup)

    # Отправка аватарки (предполагаем, что файл лежит рядом с main.py)
    photo_path = f"avatars/{choice}.jpg"  # например: yulia.jpg
    try:
        with open(photo_path, 'rb') as photo:
            context.bot.send_photo(chat_id=query.message.chat_id, photo=photo)
    except FileNotFoundError:
        context.bot.send_message(chat_id=query.message.chat_id, text="(Аватарка не найдена)")


def handle_enable_nsfw(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    user_nsfw_status[user_id] = True
    query.answer()
    query.edit_message_text(text="🔞 Взрослый режим включён. Можешь говорить откровенно.")

def handle_change_persona(update, context):
    query = update.callback_query
    choose_persona(update=Update.de_json(update.to_dict(), bot), context=context)

def handle_end_session(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    user_personas.pop(user_id, None)
    user_nsfw_status.pop(user_id, None)
    query.answer()
    query.edit_message_text(text="❌ Сессия завершена. Напиши /choose, чтобы начать заново.")

def handle_message(update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text
    prompt_base = user_personas.get(user_id, "Ты загадочный ИИ.")

    if user_nsfw_status.get(user_id):
        prompt = prompt_base + "\nГовори сексуально, флиртуй, возбуждай, но умно."
    else:
        prompt = prompt_base

    prompt += f"\nПользователь: {user_message}\nБот:"
    response = get_openrouter_response(prompt)

    keyboard = [[
        InlineKeyboardButton("🔁 Сменить персонажа", callback_data="change_persona"),
        InlineKeyboardButton("❌ Завершить", callback_data="end_session")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)

def get_openrouter_response(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0,
        "top_p": 0.9
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return response.json().get("choices", [{"message": {"content": "Что-то пошло не так."}}])[0]["message"]["content"].strip()
    except Exception as e:
        return f"Ошибка: {e}"

if __name__ == "__main__":
    app.run(port=5000)
