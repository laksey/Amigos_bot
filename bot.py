import logging
import asyncio
import datetime
import nest_asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === Настройки ===
TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'

# === Логгирование ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен. Добро пожаловать!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Доступные команды: /start, /help")


# === Напоминания ===
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Отправка уведомлений за 5 дней до отчета")
    # Добавь сюда свою бизнес-логику

async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Отправка уведомлений в день отчета")
    # Добавь сюда свою бизнес-логику


# === Главная функция ===
async def main():
    logger.info("Запуск ClientOpsBot...")

    app = Application.builder().token(TOKEN).build()

    # Хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Планировщик
    job_queue = app.job_queue
    job_queue.run_daily(notify_5days, time=datetime.time(9, 0), days=(0,))  # Пн
    job_queue.run_daily(notify_today, time=datetime.time(9, 0), days=(4,))  # Пт

    # Пример лямбда-задач (если нужны)
    job_queue.run_daily(lambda _: logger.info("Start недели"), time=datetime.time(9, 0), days=(0,))
    job_queue.run_daily(lambda _: logger.info("Конец недели"), time=datetime.time(18, 0), days=(4,))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.wait_until_shutdown()


# === Запуск ===
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
