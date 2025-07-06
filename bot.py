import asyncio
import datetime
import logging
import csv
from pytz import timezone

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === Конфигурация ===
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
TIMEZONE = timezone("Europe/Moscow")
PROJECTS_CSV = "projects.csv"

# === Логирование ===
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Загрузка CSV ===
def load_projects():
    projects = []
    try:
        with open(PROJECTS_CSV, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = datetime.datetime.strptime(row['date'], "%Y-%m-%d").date()
                projects.append({
                    "name": row['name'],
                    "responsible": row['responsible'],
                    "date": date
                })
    except Exception as e:
        logger.error(f"Ошибка чтения CSV: {e}")
    return projects

# === Напоминание ===
async def notify(context: ContextTypes.DEFAULT_TYPE, days_before: int):
    today = datetime.datetime.now(TIMEZONE).date()
    projects = [p for p in load_projects() if (p['date'] - today).days == days_before]
    for p in projects:
        text = f"⚠️ Напоминание: отчет по проекту {p['name']}\nОтветственный: {p['responsible']}"
        await context.bot.send_message(chat_id=context.bot_data["chat_id"], text=text)

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["chat_id"] = update.effective_chat.id
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
    await notify(context=context, days_before=5)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify(context=context, days_before=0)

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    end = today + datetime.timedelta(days=7)
    projects = [p for p in load_projects() if today <= p['date'] <= end]
    if projects:
        text = "📌 Отчеты на этой неделе:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].strftime('%d.%m')})" for p in projects])
        text += "\n\n🟡 Не забудьте напомнить клиентам об оплате."
    else:
        text = "✅ На этой неделе отчетов нет."
    await update.message.reply_text(text)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start = today - datetime.timedelta(days=6)
    projects = [p for p in load_projects() if start <= p['date'] <= today]
    if projects:
        text = "📤 Подтвердите, что отчеты отправлены по этим проектам:\n" + "\n".join(
            [f"• {p['name']} — {p['responsible']} (до {p['date'].strftime('%d.%m')})" for p in projects])
    else:
        text = "✅ За эту неделю отчетов не было."
    await update.message.reply_text(text)

# === Главная точка входа ===
def main():
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
    app.run_polling()

if __name__ == "__main__":
    main()
