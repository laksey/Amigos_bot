import csv
import datetime
import logging
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === Конфигурация ===
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_FILE = "projects.csv"
TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))  # Москва

# === Логгирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Загрузка данных из CSV ===
def load_projects():
    projects = []
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date = datetime.datetime.strptime(row["Дата отчета проекта"], "%d").replace(
                    year=datetime.datetime.now().year,
                    month=datetime.datetime.now().month,
                    tzinfo=TIMEZONE,
                )
                projects.append({
                    "name": row["Название проекта"],
                    "responsible": row["Ответственный"],
                    "date": date.date(),
                })
            except Exception as e:
                logger.warning(f"Ошибка в строке CSV: {row} — {e}")
    return projects

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ClientOpsBot. Используй команды /report_week или /report_month.")

async def report_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    projects = [p for p in load_projects() if start <= p["date"] <= end]
    if projects:
        text = "📌 Проекты на этой неделе:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].day})" for p in projects]
        )
    else:
        text = "✅ На этой неделе ничего нет."
    await update.message.reply_text(text)

async def report_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start = today.replace(day=1)
    end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    projects = [p for p in load_projects() if start <= p["date"] <= end]
    if projects:
        text = "📊 Отчеты в этом месяце:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].day})" for p in projects]
        )
    else:
        text = "✅ В этом месяце проектов нет."
    await update.message.reply_text(text)

# === Уведомление ===
async def notify(context: ContextTypes.DEFAULT_TYPE, days_before: int):
    today = datetime.datetime.now(TIMEZONE).date()
    target_date = today + datetime.timedelta(days=days_before)
    due_projects = [p for p in load_projects() if p["date"] == target_date]
    for p in due_projects:
        msg = f"⚠️ Сегодня необходимо отправить отчет по проекту {p['name']}.\nОтветственный: {p['responsible']}"
        await context.bot.send_message(chat_id="@your_channel_or_user", text=msg)  # Заменить на актуальный chat_id

# === Запуск ===
async def run_bot(app):
    await app.initialize()
    await app.start()
    logger.info("✅ ClientOpsBot запущен.")
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report_week", report_week))
    app.add_handler(CommandHandler("report_month", report_month))

    # Планировщик
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(notify, CronTrigger(day_of_week="mon", hour=9), kwargs={"context": app, "days_before": 5})
    scheduler.add_job(notify, CronTrigger(day_of_week="fri", hour=9), kwargs={"context": app, "days_before": 0})
    scheduler.start()

    # Запуск
    loop.create_task(run_bot(app))
    loop.run_forever()
