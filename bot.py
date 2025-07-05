import logging
import datetime
import asyncio
import nest_asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройки логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID чата, куда будут приходить уведомления
CHAT_ID = "YOUR_CHAT_ID"  # замените на ID вашего чата
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"  # вставьте сюда токен бота

# Пример данных (эмуляция таблицы)
projects = [
    {"название": "Проект А", "дата_отчета": 5, "ник": "@user1"},
    {"название": "Проект B", "дата_отчета": 10, "ник": "@user2"},
    {"название": "Проект C", "дата_отчета": 15, "ник": "@user3"},
    {"название": "Проект D", "дата_отчета": 25, "ник": "@user4"},
]

# Уведомление за 5 дней до даты отчета
async def notify_5days():
    today = datetime.datetime.today().day
    upcoming = [p for p in projects if (p["дата_отчета"] - today) == 5]
    if upcoming:
        msg = "📢 Через 5 дней отчет по:\n"
        for p in upcoming:
            msg += f"- {p['название']} ({p['ник']})\n"
        await app.bot.send_message(chat_id=CHAT_ID, text=msg)

# Уведомление в день отчета
async def notify_today():
    today = datetime.datetime.today().day
    current = [p for p in projects if p["дата_отчета"] == today]
    if current:
        msg = "📅 Сегодня нужно сдать отчет:\n"
        for p in current:
            msg += f"- {p['название']} ({p['ник']})\n"
        await app.bot.send_message(chat_id=CHAT_ID, text=msg)

# Команды для ручного запуска
async def weekly_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Неделя началась. Погнали!")

async def weekly_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Неделя закрыта. Жду отчетов.")

# Главная асинхронная функция
async def main():
    global app
    app = ApplicationBuilder().token(TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("weekly_start", weekly_start))
    app.add_handler(CommandHandler("weekly_end", weekly_end))

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_5days, "cron", hour=9)
    scheduler.add_job(notify_today, "cron", hour=9)
    scheduler.add_job(lambda: asyncio.create_task(weekly_start_msg()), "cron", day_of_week="mon", hour=9)
    scheduler.add_job(lambda: asyncio.create_task(weekly_end_msg()), "cron", day_of_week="fri", hour=18)
    scheduler.start()

    logger.info("Запуск ClientOpsBot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Автоматические сообщения в чат
async def weekly_start_msg():
    await app.bot.send_message(chat_id=CHAT_ID, text="🔔 *Начало недели!* Не забудьте о задачах.", parse_mode="Markdown")

async def weekly_end_msg():
    await app.bot.send_message(chat_id=CHAT_ID, text="✅ *Конец недели!* Отчеты, пожалуйста.", parse_mode="Markdown")

# Запуск
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
