import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
import requests

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

# Переменные состояний пользователей
user_personas = {}
user_nsfw_status = {}

# Твои персонажи (ВСТАВЛЯЕМ ВСЕ ТВОИ, как ты давал!)
personas = {
    "yulia": {
        "name": "Юля — политическая любовница",
        "prompt": "Я — Юля. ..."
    },
    # ... вставляешь ВСЕ персонажи как у тебя в коде
    "hina": {
        "name": "Хина — японская школьница",
        "prompt": "Я… Хина. ..."
    }
}

# --- Хэндлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши /choose чтобы выбрать персонажа.")

async def choose_persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(p["name"], callback_data=key)] for key, p in personas.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выбери персонажа:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text("Выбери персонажа:", reply_markup=reply_markup)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data
    user_personas[user_id] = personas[choice]["prompt"]
    user_nsfw_status[user_id] = False
    keyboard = [[
        InlineKeyboardButton("🔁 Сменить персонажа", callback_data="change_persona"),
        InlineKeyboardButton("🔓 Включить 18+", callback_data="enable_nsfw"),
        InlineKeyboardButton("❌ Завершить", callback_data="end_session")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await context.bot.send_message(chat_id=query.message.chat_id, text=f"Ты выбрал: {personas[choice]['name']}", reply_markup=reply_markup)

async def handle_enable_nsfw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_nsfw_status[query.from_user.id] = True
    await query.answer()
    await query.edit_message_text(text="🔞 Взрослый режим включён.")

async def handle_change_persona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await choose_persona(update, context)

async def handle_end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_personas.pop(user_id, None)
    user_nsfw_status.pop(user_id, None)
    await query.answer()
    await query.edit_message_text(text="❌ Сессия завершена. Напиши /choose, чтобы начать заново.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_message = update.message.text
    prompt_base = user_personas.get(user_id, "Ты загадочный ИИ.")
    prompt = prompt_base + ("\nГовори сексуально..." if user_nsfw_status.get(user_id) else "")
    prompt += f"\nПользователь: {user_message}\nБот:"
    response = get_openrouter_response(prompt)
    keyboard = [[
        InlineKeyboardButton("🔁 Сменить персонажа", callback_data="change_persona"),
        InlineKeyboardButton("❌ Завершить", callback_data="end_session")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response, reply_markup=reply_markup)

def get_openrouter_response(prompt):
    print("Отправляю запрос в OpenRouter с промптом:", prompt)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3-8b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0,
        "top_p": 0.9
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        print("OpenRouter response:", response.status_code, response.text)
        return response.json().get("choices", [{"message": {"content": "Что-то пошло не так."}}])[0]["message"]["content"].strip()
    except Exception as e:
        print("Exception in get_openrouter_response:", e)
        return f"Ошибка: {e}"

# --- Main запуск ---

if __name__ == "__main__":
    from telegram.ext import Application

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Регистрируем хэндлеры
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("choose", choose_persona))

    pattern_personas = "^(" + "|".join(personas.keys()) + ")$"
    application.add_handler(CallbackQueryHandler(handle_choice, pattern=pattern_personas))
    application.add_handler(CallbackQueryHandler(handle_enable_nsfw, pattern="^enable_nsfw$"))
    application.add_handler(CallbackQueryHandler(handle_change_persona, pattern="^change_persona$"))
    application.add_handler(CallbackQueryHandler(handle_end_session, pattern="^end_session$"))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск по Webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    )
