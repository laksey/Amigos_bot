import asyncio
import logging
import datetime
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === Настройки ===
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
TIMEZONE = pytz.timezone("Europe/Moscow")

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Заглушки для демонстрации ===
def load_projects():
    return [
        {"name": "Перемена", "responsible": "@a1exeyy", "date": datetime.date.today()}
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ClientOpsBot активен.")

async def notify(context: ContextTypes.DEFAULT_TYPE, days_before: int):
    today = datetime.datetime.now(TIMEZONE).date()
    delta = datetime.timedelta(days=days_before)
    target = today + delta
    projects = [p for p in load_projects() if p["date"].day == target.day]
    for p in projects:
        text = f"⚠️ Сегодня необходимо отправить отчет по проекту {p['name']}.\nОтветственный: {p['responsible']}"
        await context.bot.send_message(chat_id=context.job.chat_id, text=text)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    scheduler = AsyncIOScheduler(timezone=TIMEZON
