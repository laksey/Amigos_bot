
import logging
import asyncio
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID чата (можно заменить на нужный)
CHAT_ID = None

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    logger.info(f"Start command received in chat: {CHAT_ID}")
    await context.bot.send_message(chat_id=CHAT_ID, text="""👋 Привет! Я — ClientOpsBot.

Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
• За 5 дней до даты сдачи
• В день сдачи отчета

Чтобы протестировать, используйте:
/test_5days — проверка напоминания за 5 дней
/test_today — проверка напоминания в день отчета

Бот активирован. Ожидайте уведомлений в соответствии с графиком.
""")

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🔔 Напоминание: отчет по проекту через 5 дней.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🚨 Сегодня день сдачи отчета по проекту!")

async def weekly_start(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        await context.bot.send_message(chat_id=CHAT_ID, text="📊 Напоминаю: новая неделя, начинаем с планирования!")

async def weekly_end(context: ContextTypes.DEFAULT_TYPE):
    if CHAT_ID:
        await context.bot.send_message(chat_id=CHAT_ID, text="✅ Итоги недели: не забудьте отчитаться!")

async def main():
    app = ApplicationBuilder().token("8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))

    # Удаление webhook
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(weekly_start, "cron", hour=9, day_of_week="mon", args=[app])
    scheduler.add_job(weekly_end, "cron", hour=18, day_of_week="fri", args=[app])
    scheduler.start()

    logger.info("Bot is starting polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
