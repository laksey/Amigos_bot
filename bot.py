import csv
import datetime
import logging
import asyncio

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === Конфигурация ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_FILE = 'projects.csv'
TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"

# === Загрузка проектов ===
def load_projects():
    today = datetime.datetime.now(TIMEZONE).date()
    projects = []
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                name = row[0].strip()
                responsible = row[1].strip()
                day = int(row[2].strip())
                report_date = today.replace(day=1) + datetime.timedelta(days=day - 1)
                while report_date.weekday() >= 5:
                    report_date += datetime.timedelta(days=1)
                if report_date < today:
                    next_month = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
                    report_date = next_month.replace(day=day)
                    while report_date.weekday() >= 5:
                        report_date += datetime.timedelta(days=1)
                projects.append({'name': name, 'responsible': responsible, 'date': report_date})
            except Exception as e:
                logger.warning(f"Ошибка в строке {row}: {e}")
    return projects

# === Напоминания ===
async def notify(context: ContextTypes.DEFAULT_TYPE, days_before: int):
    today = datetime.datetime.now(TIMEZONE).date()
    for project in load_projects():
        delta = (project['date'] - today).days
        if delta == days_before:
            msg = (
                f"{'🔔' if days_before == 5 else '⚠️'} "
                f"{'Через 5 дней' if days_before == 5 else 'Сегодня'} нужно сдать отчет по проекту {project['name']}.\n"
                f"Ответственный: {project['responsible']}"
            )
            await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 ClientOpsBot активен.\n"
        "Команды:\n"
        "/test_5days — тест за 5 дней\n"
        "/test_today — тест на сегодня\n"
        "/report_week — отчеты на неделе\n"
        "/report_month — отчеты в месяце"
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job = type("Job", (), {"chat_id": update.message.chat_id})
    await notify(context, 5)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job = type("Job", (), {"chat_id": update.message.chat_id})
    await notify(context, 0)

async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    end = today + datetime.timedelta(days=(6 - today.weekday()))
    projects = [p for p in load_projects() if today <= p['date'] <= end]
    if projects:
        text = "📅 Отчеты на этой неделе:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].day})" for p in projects])
    else:
        text = "✅ На этой неделе ничего нет."
    await update.message.reply_text(text)

async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start = today.replace(day=1)
    end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    projects = [p for p in load_projects() if start <= p['date'] <= end]
    if projects:
        text = "📊 Отчеты в этом месяце:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].day})" for p in projects])
    else:
        text = "✅ В этом месяце проектов нет."
    await update.message.reply_text(text)

# === Главная асинхронная логика запуска ===
async def run_bot(app: Application):
    await app.initialize()
    await app.start()
    logger.info("✅ ClientOpsBot запущен.")
    await app.updater.start_polling()
    await app.updater.idle()

# === Точка входа ===
if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_week", report_week))
    app.add_handler(CommandHandler("report_month", report_month))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(notify, CronTrigger(day_of_week='mon', hour=9), kwargs={"context": app, "days_before": 5})
    scheduler.add_job(notify, CronTrigger(day_of_week='fri', hour=9), kwargs={"context": app, "days_before": 0})
    scheduler.start()

    loop.create_task(run_bot(app))
    loop.run_forever()
