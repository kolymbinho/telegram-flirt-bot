import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Загружаем переменные из .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # <-- Берем TELEGRAM TOKEN из переменных окружения

# Функция для получения ответа от GPT-4o
def get_openai_response(prompt):
    api_key = (OPENAI_API_KEY or "").strip()

    if not api_key:
        print("OpenAI API key is not set")
        return "Ошибка: API KEY не задан."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o",
        "messages": [
            { "role": "user", "content": prompt }
        ]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        print(f"Ошибка OpenAI: {response.status_code} {response.text}")
        return f"Ошибка OpenAI: {response.status_code}"

    result = response.json()
    print(f"Ответ OpenAI: {result}")

    return result["choices"][0]["message"]["content"]

# Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я GPT-4o бот. Напиши мне что-нибудь.")

# Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    bot_response = get_openai_response(user_message)
    await update.message.reply_text(bot_response)

# Запуск бота
if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("Ошибка: TELEGRAM_TOKEN не задан!")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()
