import logging
import datetime
import asyncio
import calendar
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === НАСТРОЙКИ ===
BOT_TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'
DATA_PATH = './projects.csv'
ADMIN_USERNAME = '@ellobodefuego'

# === НАСТРОЙКА ЛОГГЕРА ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === УТИЛИТЫ ===
def is_weekend(date: datetime.date):
    return date.weekday() >= 5

def shift_if_weekend(date: datetime.date):
    while is_weekend(date):
        date += datetime.timedelta(days=1)
    return date

def load_projects():
    df = pd.read_csv(DATA_PATH)
    df.columns = ['project', 'manager', 'report_day']
    df['report_day'] = df['report_day'].astype(str).str.strip()
    return df

def get_today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))

# === ОСНОВНЫЕ ФУНКЦИИ ===
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    today = get_today().date()
    df = load_projects()
    upcoming = []

    for _, row in df.iterrows():
        try:
            report_day = int(row['report_day'])
            report_date = today.replace(day=1) + datetime.timedelta(days=report_day - 1)
            report_date = shift_if_weekend(report_date)
            if (report_date - today).days == 5:
                upcoming.append(f"{row['project']} — {row['manager']}")
        except:
            continue

    if upcoming:
        msg = "\u26a0\ufe0f Напоминание: через 5 дней сдача отчетов по проектам:\n\n" + "\n".join(upcoming)
        await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = get_today().date()
    df = load_projects()
    due_today = []

    for _, row in df.iterrows():
        try:
            report_day = int(row['report_day'])
            report_date = today.replace(day=1) + datetime.timedelta(days=report_day - 1)
            report_date = shift_if_weekend(report_date)
            if report_date == today:
                due_today.append(f"{row['project']} — {row['manager']}")
        except:
            continue

    if due_today:
        msg = "\u23f0 Сегодня сдача отчетов по проектам:\n\n" + "\n".join(due_today)
        await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = get_today().date()
    df = load_projects()
    this_week = today.isocalendar()[1]
    due = []

    for _, row in df.iterrows():
        try:
            report_day = int(row['report_day'])
            report_date = today.replace(day=1) + datetime.timedelta(days=report_day - 1)
            report_date = shift_if_weekend(report_date)
            if report_date.isocalendar()[1] == this_week:
                due.append(f"{row['project']} — {row['manager']}")
        except:
            continue

    msg = "\u2709\ufe0f На этой неделе отчеты по проектам:\n\n" + "\n".join(due)
    msg += "\n\nПожалуйста, напомните клиентам об оплате."
    await update.message.reply_text(msg)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = get_today().date()
    df = load_projects()
    this_week = today.isocalendar()[1]
    submitted = []

    for _, row in df.iterrows():
        try:
            report_day = int(row['report_day'])
            report_date = today.replace(day=1) + datetime.timedelta(days=report_day - 1)
            report_date = shift_if_weekend(report_date)
            if report_date.isocalendar()[1] == this_week:
                submitted.append(f"{row['project']} — {row['manager']}")
        except:
            continue

    msg = f"\ud83d\udd39 {ADMIN_USERNAME}, отчеты по следующим проектам были отправлены?\n\n" + "\n".join(submitted)
    msg += "\n\nПожалуйста, подтвердите."
    await update.message.reply_text(msg)

# === ТЕСТОВЫЕ КОМАНДЫ ===
async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_5days(context)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_today(context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "\ud83d\udc4b Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "\u2022 За 5 дней до даты сдачи\n"
        "\u2022 В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )
    await update.message.reply_text(msg)

# === ЗАПУСК ===
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(notify_5days, CronTrigger(hour=9, minute=0, day='*'))
    scheduler.add_job(notify_today, CronTrigger(hour=9, minute=0, day='*'))
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    logger.info("Запуск ClientOpsBot...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
