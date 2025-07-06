import csv
import logging
from datetime import datetime, timedelta
import asyncio
import pytz

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.daily import DailyTrigger

TOKEN = "YOUR_BOT_TOKEN"
CSV_FILE = "projects.csv"
TIMEZONE = pytz.timezone("Europe/Moscow")
TELEGRAM_ADMIN = "ellobodefuego"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_projects():
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [
                {
                    "project": row["project"],
                    "username": row["username"],
                    "date": int(row["date"])
                }
                for row in reader
                if row["project"] and row["username"] and row["date"].isdigit()
            ]
    except Exception as e:
        logging.error(f"Ошибка чтения CSV: {e}")
        return []

def get_projects_by_day(target_day: int) -> list:
    today = datetime.now(TIMEZONE)
    return [
        p for p in load_projects()
        if p["date"] == target_day
    ]

def get_projects_by_day_diff(diff_days: int) -> list:
    today = datetime.now(TIMEZONE)
    target_day = (today + timedelta(days=diff_days)).day
    return get_projects_by_day(target_day)

def format_projects(projects: list) -> str:
    if not projects:
        return "Нет подходящих проектов."
    return "\n".join([f"• {p['project']} — @{p['username']}" for p in projects])

async def notify_projects(context: ContextTypes.DEFAULT_TYPE, diff_days: int):
    projects = get_projects_by_day_diff(diff_days)
    if projects:
        message = (
            f"⏰ Напоминание об отчётах за {diff_days} дней:\n\n"
            f"{format_projects(projects)}"
        )
        await context.bot.send_message(chat_id=context.job.chat_id, text=message)

async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE).day
    projects = get_projects_by_day(today)
    if projects:
        message = (
            f"📤 Сегодня день отчёта по проектам:\n\n"
            f"{format_projects(projects)}"
        )
        await context.bot.send_message(chat_id=context.job.chat_id, text=message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )
    await update.message.reply_text(text)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_projects_by_day_diff(5)
    await update.message.reply_text(
        f"✅ Тест напоминания за 5 дней выполнен.\n\n{format_projects(projects)}"
    )

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE).day
    projects = get_projects_by_day(today)
    await update.message.reply_text(
        f"✅ Тест напоминания на сегодня выполнен.\n\n{format_projects(projects)}"
    )

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE)
    end_date = today + timedelta(days=6 - today.weekday())  # до конца недели
    projects = load_projects()
    result = [
        p for p in projects
        if today.day <= p["date"] <= end_date.day
    ]
    await update.message.reply_text(
        f"📅 Предстоящие отчёты на этой неделе:\n{format_projects(result)}\n\n"
        "💸 Пожалуйста, напомните клиентам об оплате."
    )

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(TIMEZONE)
    start_date = today - timedelta(days=today.weekday())  # понедельник
    projects = load_projects()
    result = [
        p for p in projects
        if start_date.day <= p["date"] <= today.day
    ]
    await update.message.reply_text(
        f"📊 Итог по отчётам за неделю:\n{format_projects(result)}\n\n"
        f"@ellobodefuego, пожалуйста, подтвердите, что отчёты отправлены клиентам."
    )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        notify_projects,
        trigger=DailyTrigger(hour=9, minute=0),
        kwargs={"context": app.bot, "diff_days": 5},
        name="notify_5days"
    )
    scheduler.add_job(
        notify_today,
        trigger=DailyTrigger(hour=9, minute=0),
        kwargs={"context": app.bot},
        name="notify_today"
    )
    scheduler.start()

    logging.info("✅ ClientOpsBot запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
