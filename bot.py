
import csv
import logging
import asyncio
import datetime
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_FILE = "projects.csv"
ADMIN_USERNAME = "@ellobodefuego"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)

async def send_message(text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

def read_projects():
    with open(CSV_FILE, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def get_due_projects(offset_days=0):
    today = datetime.date.today() + datetime.timedelta(days=offset_days)
    return [p for p in read_projects() if parse_date(p["Дата отчета проекта"]) == today]

def parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except Exception:
        return None

async def weekly_start_handler(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None):
    projects = read_projects()
    msg = "📝 На этой неделе нужно сдать отчеты:
"
    for p in projects:
        report_date = parse_date(p["Дата отчета проекта"])
        if report_date and report_date.isocalendar()[1] == datetime.date.today().isocalendar()[1]:
            msg += f"• {p['Проект']} — @{p['Ответственный']}
"
    await send_message(msg)

async def weekly_end_handler(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None):
    projects = read_projects()
    msg = f"✅ {ADMIN_USERNAME}, подтвердите, что отчеты сданы:
"
    for p in projects:
        report_date = parse_date(p["Дата отчета проекта"])
        if report_date and report_date.isocalendar()[1] == (datetime.date.today().isocalendar()[1] - 1):
            msg += f"• {p['Проект']} — @{p['Ответственный']}
"
    await send_message(msg)

async def daily_check():
    projects = get_due_projects()
    if projects:
        msg = "📢 Сегодня нужно сдать отчеты:
"
        for p in projects:
            msg += f"• {p['Проект']} — @{p['Ответственный']}
"
        await send_message(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.

"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
"
        "• За 5 дней до даты сдачи
"
        "• В день сдачи отчета

"
        "Доступные команды:
"
        "/weekly_start — список отчетов на неделю
"
        "/weekly_end — напоминание о подтверждении отчетов
"
        "/test_5days — тест 5-дневного напоминания
"
        "/test_today — тест напоминания в день сдачи"
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Тест: напоминание за 5 дней до отчета.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Тест: напоминание в день сдачи отчета.")

async def main():
    global chat_id
    application = ApplicationBuilder().token(TOKEN).build()
    updates = await application.bot.get_updates()
    if updates:
        chat_id = updates[-1].message.chat_id
    else:
        chat_id = (await application.bot.get_me()).id

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_5days", test_5days))
    application.add_handler(CommandHandler("test_today", test_today))
    application.add_handler(CommandHandler("weekly_start", weekly_start_handler))
    application.add_handler(CommandHandler("weekly_end", weekly_end_handler))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(weekly_start_handler()), CronTrigger(day_of_week="mon", hour=9, minute=0))
    scheduler.add_job(lambda: asyncio.create_task(weekly_end_handler()), CronTrigger(day_of_week="fri", hour=18, minute=0))
    scheduler.add_job(lambda: asyncio.create_task(daily_check()), CronTrigger(hour=9, minute=0))
    scheduler.start()

    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
