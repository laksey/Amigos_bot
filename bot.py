import logging
import datetime
import asyncio

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

# Токен бота
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"

# Пользовательский список проектов (можно будет подтягивать из таблицы)
projects = [
    {"name": "Проект А", "owner": "@username1", "report_day": "2025-07-10"},
    {"name": "Проект B", "owner": "@username2", "report_day": "2025-07-12"},
]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ClientOpsBot активен. Я напомню о дедлайнах и отчётах.")

# Ответ на любое сообщение
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы написали: {update.message.text}")

# Уведомление за 5 дней до отчета
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    logger.info("Запуск уведомлений за 5 дней...")
    for project in projects:
        report_day = datetime.datetime.strptime(project["report_day"], "%Y-%m-%d").date()
        if (report_day - today).days == 5:
            await context.bot.send_message(
                chat_id=project["owner"],
                text=f"🔔 Напоминание: Через 5 дней по проекту «{project['name']}» должен быть отчёт."
            )

# Уведомление в день сдачи отчета
async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    logger.info("Запуск уведомлений на сегодня...")
    for project in projects:
        report_day = datetime.datetime.strptime(project["report_day"], "%Y-%m-%d").date()
        if report_day == today:
            await context.bot.send_message(
                chat_id=project["owner"],
                text=f"📅 Сегодня дедлайн по отчёту по проекту «{project['name']}»."
            )

# Основная функция
async def main():
    app = Application.builder().token(TOKEN).build()

    # Хендлеры команд и текста
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Планировщик задач
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_5days, CronTrigger(day_of_week="mon", hour=9, minute=0), args=[app])
    scheduler.add_job(notify_today, CronTrigger(day_of_week="fri", hour=9, minute=0), args=[app])
    scheduler.start()

    logger.info("Запуск ClientOpsBot...")
    await app.run_polling()

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
