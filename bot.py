import logging
import asyncio
import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === Конфигурация ===
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CHAT_ID = -1002092121566  # ID общего чата

# === Логирование ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# === Основная команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("ClientOpsBot активен и готов к работе.")

# === Напоминание за 5 дней до отчета ===
async def notify_5days(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=CHAT_ID, text="Напоминание: через 5 дней должен быть сдан отчет по проекту.")

# === Напоминание в день сдачи отчета ===
async def notify_today(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=CHAT_ID, text="Сегодня день сдачи отчета по проекту. Отправьте отчет, пожалуйста.")

# === Основная функция ===
async def main():
    app = Application.builder().token(TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))

    # Планировщик задач (через JobQueue)
    job_queue = app.job_queue

    # Добавление задач
    job_queue.run_daily(notify_5days, time=datetime.time(9, 0), days=(0,))  # Пн
    job_queue.run_daily(notify_today, time=datetime.time(9, 0), days=(4,))  # Пт
    job_queue.run_daily(lambda _: logger.info("Start недели"), time=datetime.time(9, 0), days=(0,))
    job_queue.run_daily(lambda _: logger.info("Конец недели"), time=datetime.time(18, 0), days=(4,))

    logger.info("Запуск ClientOpsBot...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
