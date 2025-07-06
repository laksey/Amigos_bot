import asyncio
import logging
import pandas as pd
import datetime
from pytz import timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler
)

# === Константы ===
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
TIMEZONE = timezone("Europe/Moscow")

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# === Загрузка проектов ===
def load_projects():
    try:
        df = pd.read_csv("projects.csv")
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Ошибка чтения CSV: {e}")
        return []

# === Напоминание ===
async def notify(context: ContextTypes.DEFAULT_TYPE, days_before: int):
    projects = load_projects()
    today = datetime.datetime.now(TIMEZONE).date()
    target_date = today + datetime.timedelta(days=days_before)

    for p in projects:
        if p['date'].date() == target_date:
            message = f"⚠️ {'Через 5 дней' if days_before == 5 else 'Сегодня'} необходимо отправить отчет по проекту {p['name']}.\nОтветственный: {p['responsible']}"
            await context.bot.send_message(chat_id=context.application.bot.id, text=message)

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify(context, days_before=5)
    await update.message.reply_text("✅ Тест напоминания за 5 дней выполнен.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify(context, days_before=0)
    await update.message.reply_text("✅ Тест напоминания на сегодня выполнен.")

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    end = today + datetime.timedelta(days=7)
    projects = [p for p in load_projects() if today <= p['date'].date() <= end]

    if projects:
        text = "📌 Проекты на этой неделе:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].strftime('%d.%m')})" for p in projects]
        ) + "\n\nНапомните клиентам об оплате."
    else:
        text = "✅ На этой неделе отчетов нет."

    await update.message.reply_text(text)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start = today - datetime.timedelta(days=6)
    end = today
    projects = [p for p in load_projects() if start <= p['date'].date() <= end]

    if projects:
        text = "📤 Отчеты за неделю:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (от {p['date'].strftime('%d.%m')})" for p in projects]
        ) + "\n\nПожалуйста, подтвердите отправку отчетов."
    else:
        text = "✅ На этой неделе не было отчетов."

    await update.message.reply_text(text)

# === Инициализация ===
async def main_async():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(notify, CronTrigger(day_of_week='mon', hour=9), kwargs={"context": app, "days_before": 5})
    scheduler.add_job(notify, CronTrigger(day_of_week='fri', hour=9), kwargs={"context": app, "days_before": 0})
    scheduler.start()

    logger.info("✅ ClientOpsBot запущен.")
    await app.run_polling()

# === Запуск без asyncio.run ===
import nest_asyncio
nest_asyncio.apply()

asyncio.get_event_loop().run_until_complete(main_async())
