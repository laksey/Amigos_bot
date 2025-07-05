import csv
import logging
import datetime
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_PATH = "projects.csv"
RESPONSIBLE_TAG = "@ellobodefuego"
TIMEZONE_OFFSET = 3  # UTC+3 (Москва)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_projects():
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def is_weekday(dt):
    return dt.weekday() < 5

def adjust_to_weekday(dt):
    while not is_weekday(dt):
        dt += datetime.timedelta(days=1)
    return dt

def format_project(project):
    return f"🔹 <b>{project['Проект']}</b> — ответственный: {project['Ответственный']} — дата отчета: {project['День']} числа"

def get_today_projects(offset_days=0):
    today = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TIMEZONE_OFFSET)
    target_day = (today + datetime.timedelta(days=offset_days)).day
    return [p for p in read_projects() if int(p["День"]) == target_day]

async def send_report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_today_projects()
    if not projects:
        await update.message.reply_text("На этой неделе нет проектов с отчетами.")
        return

    text = "<b>📊 Отчет в конце недели</b>\n\n"
    for project in projects:
        text += f"• {format_project(project)}\n"
    text += f"\n{RESPONSIBLE_TAG}, подтвердите, что отчеты по этим проектам были отправлены."

    await update.message.reply_text(text, parse_mode="HTML")

async def send_report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_today_projects()
    if not projects:
        await update.message.reply_text("На этой неделе нет проектов с отчетами.")
        return

    text = "<b>📌 Предстоящие отчеты на этой неделе:</b>\n\n"
    for project in projects:
        text += f"• {format_project(project)}\n"
    text += "\nНе забудьте напомнить клиентам об оплате."

    await update.message.reply_text(text, parse_mode="HTML")

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Напоминание: до отчета по проекту осталось 5 дней.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Напоминание: сегодня день сдачи отчета по проекту.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n"
        "/report_1 — отчет о предстоящих отчетах на неделе\n"
        "/report_5 — отчет в конце недели с подтверждением\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )
    await update.message.reply_text(msg)

def schedule_jobs(app):
    async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
        today = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TIMEZONE_OFFSET)
        target_date = today + datetime.timedelta(days=5)
        target_date = adjust_to_weekday(target_date)
        if today.date() == target_date.date():
            for p in get_today_projects(5):
                text = f"⏳ Напоминание: до отчета по проекту «{p['Проект']}» осталось 5 дней. Ответственный: {p['Ответственный']}"
                await context.bot.send_message(chat_id=context.job.chat_id, text=text)

    async def notify_today(context: ContextTypes.DEFAULT_TYPE):
        today = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=TIMEZONE_OFFSET)
        target_date = adjust_to_weekday(today)
        if today.date() == target_date.date():
            for p in get_today_projects(0):
                text = f"📢 Сегодня день сдачи отчета по проекту «{p['Проект']}». Ответственный: {p['Ответственный']}"
                await context.bot.send_message(chat_id=context.job.chat_id, text=text)

    job_queue = app.job_queue
    job_queue.run_daily(notify_5days, time=datetime.time(9, 0), days=(0,))
    job_queue.run_daily(notify_today, time=datetime.time(9, 0), days=(4,))

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", send_report_1))
    app.add_handler(CommandHandler("report_5", send_report_5))

    schedule_jobs(app)
    logger.info("Запуск ClientOpsBot...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
