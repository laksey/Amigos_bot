import logging
import csv
import datetime
import asyncio
import pytz
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Константы
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
TIMEZONE = pytz.timezone("Europe/Moscow")
CSV_PATH = "projects.csv"

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка проектов из CSV
def load_projects():
    projects = []
    try:
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    day = int(row['date'])
                    report_date = datetime.datetime.now(TIMEZONE).replace(day=1).replace(day=day).date()
                    projects.append({
                        "name": row['project'],
                        "responsible": row['responsible'],
                        "date": report_date,
                    })
                except Exception as e:
                    logger.error(f"Ошибка разбора даты: {e}")
    except Exception as e:
        logger.error(f"Ошибка чтения CSV: {e}")
    return projects

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n"
        "/report_1 — отчет о задачах на неделю\n"
        "/report_5 — финальный отчет с подтверждением\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )
    await update.message.reply_text(text)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify(context, days_before=5, test_chat_id=update.message.chat_id)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify(context, days_before=0, test_chat_id=update.message.chat_id)

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
    projects = [
        p for p in load_projects()
        if today <= p['date'] <= end_of_week
    ]
    if projects:
        text = "📅 Отчеты на этой неделе:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].strftime('%d.%m')})" for p in projects]
        ) + "\n\n⚠️ Не забудьте напомнить клиентам об оплате!"
    else:
        text = "✅ На этой неделе сдача отчетов не запланирована."
    await update.message.reply_text(text)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    projects = [
        p for p in load_projects()
        if start_of_week <= p['date'] <= today
    ]
    if projects:
        text = "📥 Отчеты на этой неделе:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].strftime('%d.%m')})" for p in projects]
        ) + "\n\n@ellobodefuego, пожалуйста, подтверди, что все отчеты отправлены."
    else:
        text = "✅ За эту неделю отчеты не сдавались."
    await update.message.reply_text(text)

# Уведомления
async def notify(context: ContextTypes.DEFAULT_TYPE, days_before=5, test_chat_id=None):
    today = datetime.datetime.now(TIMEZONE).date()
    target_date = today + datetime.timedelta(days=days_before)
    projects = [
        p for p in load_projects()
        if p['date'] == target_date
    ]
    if not projects:
        return
    for p in projects:
        msg = (
            f"⚠️ {'Сегодня' if days_before == 0 else f'Через {days_before} дней'} необходимо отправить отчет по проекту *{p['name']}*.\n"
            f"Ответственный: {p['responsible']}"
        )
        await context.bot.send_message(
            chat_id=test_chat_id or context.bot_data.get("group_chat_id", p['responsible']),
            text=msg,
            parse_mode='Markdown'
        )

# Главный запуск
async def main():
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

if __name__ == "__main__":
    asyncio.run(main())
