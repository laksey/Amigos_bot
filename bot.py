import logging
import pandas as pd
import datetime
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Конфигурация ---
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_FILE = "projects.csv"
ADMIN_NICK = "@ellobodefuego"

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Загрузка проектов ---
def load_projects():
    df = pd.read_csv(CSV_FILE)
    df["Дата отчета проекта"] = pd.to_datetime(df["Дата отчета проекта"], errors='coerce', dayfirst=True)
    return df.dropna(subset=["Дата отчета проекта"])

# --- Формирование сообщений ---
def get_weekly_start_message():
    df = load_projects()
    today = datetime.date.today()
    start_of_week = today
    end_of_week = today + datetime.timedelta(days=6 - today.weekday())

    upcoming = df[
        (df["Дата отчета проекта"].dt.date >= start_of_week) &
        (df["Дата отчета проекта"].dt.date <= end_of_week)
    ]

    if upcoming.empty:
        return "📝 На этой неделе нет отчетов для сдачи."

    lines = [f"📝 *На этой неделе нужно сдать отчеты:*"]
    for _, row in upcoming.iterrows():
        lines.append(f"— {row['Название проекта']} — {row['Ответственный (ник Telegram)']} — {row['Дата отчета проекта'].date()}")

    return "\n".join(lines)

def get_weekly_end_message():
    df = load_projects()
    today = datetime.date.today()
    end_of_last_week = today - datetime.timedelta(days=today.weekday() + 1)
    start_of_last_week = end_of_last_week - datetime.timedelta(days=6)

    closed = df[
        (df["Дата отчета проекта"].dt.date >= start_of_last_week) &
        (df["Дата отчета проекта"].dt.date <= end_of_last_week)
    ]

    if closed.empty:
        return "📌 За прошлую неделю не было отчетов."

    lines = [f"📌 *{ADMIN_NICK}, подтвердите отправку отчетов по проектам:*"]
    for _, row in closed.iterrows():
        lines.append(f"— {row['Название проекта']} — {row['Ответственный (ник Telegram)']} — {row['Дата отчета проекта'].date()}")

    return "\n".join(lines)

def get_today_reminders():
    df = load_projects()
    today = datetime.date.today()

    due_today = df[df["Дата отчета проекта"].dt.date == today]

    messages = []
    for _, row in due_today.iterrows():
        messages.append(f"📍 Сегодня срок сдачи отчета по проекту *{row['Название проекта']}* — {row['Ответственный (ник Telegram)']}")

    return messages

def get_5days_reminders():
    df = load_projects()
    target_date = datetime.date.today() + datetime.timedelta(days=5)

    due_soon = df[df["Дата отчета проекта"].dt.date == target_date]

    messages = []
    for _, row in due_soon.iterrows():
        messages.append(f"⏳ Через 5 дней отчет по проекту *{row['Название проекта']}* — {row['Ответственный (ник Telegram)']}")

    return messages

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """👋 Привет! Я — ClientOpsBot.

Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
• За 5 дней до даты сдачи
• В день сдачи отчета

Чтобы протестировать, используйте:
/test_5days — проверка напоминания за 5 дней
/test_today — проверка напоминания в день отчета
/weekly_start — список отчетов на неделю
/weekly_end — отчет для подтверждения сдачи

Бот активирован. Ожидайте уведомлений в соответствии с графиком."""
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msgs = get_5days_reminders()
    if msgs:
        for msg in msgs:
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Нет отчетов через 5 дней.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msgs = get_today_reminders()
    if msgs:
        for msg in msgs:
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Сегодня нет отчетов.")

async def weekly_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_weekly_start_message(), parse_mode="Markdown")

async def weekly_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_weekly_end_message(), parse_mode="Markdown")

# --- Основной запуск ---
async def scheduled_tasks(application):
    async def job_5days():
        messages = get_5days_reminders()
        for msg in messages:
            await application.bot.send_message(chat_id=context.bot_data["chat_id"], text=msg)

    async def job_today():
        messages = get_today_reminders()
        for msg in messages:
            await application.bot.send_message(chat_id=context.bot_data["chat_id"], text=msg)

    async def job_weekly_start():
        await application.bot.send_message(chat_id=context.bot_data["chat_id"], text=get_weekly_start_message(), parse_mode="Markdown")

    async def job_weekly_end():
        await application.bot.send_message(chat_id=context.bot_data["chat_id"], text=get_weekly_end_message(), parse_mode="Markdown")

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(job_5days, CronTrigger(hour=9, minute=0))
    scheduler.add_job(job_today, CronTrigger(hour=9, minute=0))
    scheduler.add_job(job_weekly_start, CronTrigger(day_of_week="mon", hour=9, minute=0))
    scheduler.add_job(job_weekly_end, CronTrigger(day_of_week="fri", hour=18, minute=0))
    scheduler.start()

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot_data["chat_id"] = -1000000000000  # замените на актуальный chat_id

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("weekly_start", weekly_start))
    app.add_handler(CommandHandler("weekly_end", weekly_end))

    await scheduled_tasks(app)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
