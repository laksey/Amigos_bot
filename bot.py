import asyncio
import datetime
import logging
import nest_asyncio


from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CHAT_ID = "-1002152973925"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def weekly_start(bot):
    await bot.send_message(chat_id=CHAT_ID, text="🟢 Начало недели. Проверьте задачи и статусы проектов.")

async def weekly_end(bot):
    await bot.send_message(chat_id=CHAT_ID, text="🔴 Конец недели. Подведите итоги и подтвердите отчеты.")

async def notify_today(bot):
    await bot.send_message(chat_id=CHAT_ID, text="📌 Сегодня день сдачи отчета. Пожалуйста, отметьтесь.")

async def notify_5days(bot):
    await bot.send_message(chat_id=CHAT_ID, text="⏳ До сдачи отчета осталось 5 дней. Готовьте информацию.")

async def scheduler_loop(app: Application):
    sent_flags = set()
    while True:
        now = datetime.datetime.now()
        key = (now.weekday(), now.hour, now.minute)

        if key not in sent_flags:
            if now.weekday() == 0 and now.hour == 9 and now.minute == 0:
                await weekly_start(app.bot)
                sent_flags.add(key)

            elif now.weekday() == 4 and now.hour == 18 and now.minute == 0:
                await weekly_end(app.bot)
                sent_flags.add(key)

            elif now.day == 10 and now.hour == 12 and now.minute == 0:
                await notify_today(app.bot)
                sent_flags.add(key)

            elif now.day == 5 and now.hour == 12 and now.minute == 0:
                await notify_5days(app.bot)
                sent_flags.add(key)

        await asyncio.sleep(30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ClientOpsBot активирован. Ожидайте автоматических уведомлений.")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    asyncio.create_task(scheduler_loop(app))
    logger.info("🚀 ClientOpsBot запущен")
    await app.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.run(main())

