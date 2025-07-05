import logging
import datetime
import asyncio
import nest_asyncio

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"

# Пример данных
projects = [
    {"name": "Проект А", "owner": "@username1", "report_day": "2025-07-10"},
    {"name": "Проект B", "owner": "@username2", "report_day": "2025-07-12"},
]

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ClientOpsBot запущен и готов к работе.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы написали: {update.message.text}")

# Уведомления
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    for project in projects:
        report_day = datetime.datetime.strptime(project["report_day"], "%Y-%m-%d").date()
        if (report_day - today).days == 5:
            await context.bot.send_message(
                chat_id=project["owner"],
                text=f"🔔 Через 5 дней по проекту «{project['name']}» дедлайн отчёта!"
            )

async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    for project in projects:
        report_day = datetime.datetime.strptime(project["report_day"], "%Y-%m-%d").date()
        if report_day == today:
            await context.bot.send_message(
                chat_id=project["owner"],
                text=f"📅 Сегодня отчёт по проекту «{project['name']}»!"
            )

# Основная функция
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_5days, CronTrigger(day_of_week="mon", hour=9, minute=0), args=[app])
    scheduler.add_job(notify_today, CronTrigger(day_of_week="fri", hour=9, minute=0), args=[app])
    scheduler.start()

    logger.info("Запуск ClientOpsBot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Запуск без конфликта с уже запущенным loop
if __name__ == "__main__":
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
