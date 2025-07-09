import nest_asyncio
nest_asyncio.apply()

import logging
import pandas as pd
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import pytz
import random

# Настройки
TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'
CSV_FILE = 'projects.csv'
CHAT_ID_FILE = 'chat_id.txt'
TIMEZONE = 'Europe/Moscow'
tz = pytz.timezone(TIMEZONE)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Работа с chat_id
def save_chat_id(chat_id: int):
    with open(CHAT_ID_FILE, 'w') as f:
        f.write(str(chat_id))

def load_chat_id() -> int | None:
    try:
        with open(CHAT_ID_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        logging.error(f"Не удалось загрузить chat_id: {e}")
        return None


# Чтение CSV
def load_projects():
    try:
        df = pd.read_csv(CSV_FILE)
        df['report_date'] = pd.to_datetime(df['report_date'], format='%d').apply(
            lambda d: datetime(datetime.now().year, datetime.now().month, d.day, tzinfo=tz).date()
        )
        return df
    except Exception as e:
        logging.error(f"Ошибка чтения CSV: {e}")
        return pd.DataFrame(columns=['project', 'responsible', 'report_date'])


# Генерация напоминаний
def generate_reminders(days_before: int) -> list[str]:
    today = datetime.now(tz).date()
    df = load_projects()

    messages = []

    for _, row in df.iterrows():
        report_date = row['report_date']

        if report_date < today:
            continue

        days_until = (report_date - today).days

        if days_before == 0 and days_until == 0:
            messages.append(f"• {row['project']} — сегодня. Ответственный: {row['responsible']}")
        elif days_before > 0 and days_until == days_before:
            messages.append(f"• {row['project']} — {report_date.day} числа. Ответственный: {row['responsible']}")

    if not messages:
        return ["✅ Сегодня нет отчётов."]
    return messages


# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)

    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5, 3, 1 день до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Для проверки используйте:\n"
        "/test_5days — проверка за 5 дней\n"
        "/test_3days — проверка за 3 дня\n"
        "/test_1day — проверка за 1 день\n"
        "/test_today — проверка в день сдачи\n"
        "/report_1 — предстоящие отчёты\n"
        "/report_5 — отчёты прошлой недели\n"
        "/test_random — случайный проект"
    )


async def test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    msgs = generate_reminders(days)
    for msg in msgs:
        await update.message.reply_text(msg)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 5)

async def test_3days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 3)

async def test_1day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 1)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 0)


async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(tz)
    df = load_projects()
    week = today + timedelta(days=7)
    upcoming = df[df['report_date'] <= week.date()]

    if not upcoming.empty:
        message = "📅 Предстоящие отчёты на неделе:\n"
        for _, row in upcoming.iterrows():
            message += f"• {row['project']} — {row['report_date'].day} числа. Ответственный: {row['responsible']}\n"
    else:
        message = "На этой неделе нет предстоящих отчетов."

    await update.message.reply_text(message)


async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(tz).date()
    df = load_projects()

    # Фильтрация проектов, у которых дата сдачи прошла (но в этом месяце)
    filtered = df[(df['report_date'].month == today.month) & (df['report_date'] < today)]

    if filtered.empty:
        await update.message.reply_text("❎ Проектов с отчётом, сданным на прошлой неделе, нет.")
        return

    message = "🗂️ Отчёты, сданные ранее в этом месяце:\n\n"
    for _, row in filtered.iterrows():
        message += f"• {row['project']} — {row['report_date'].day} числа. Ответственный: {row['responsible']}\n"

    await update.message.reply_text(message)


async def test_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_projects()
    if df.empty:
        await update.message.reply_text("📭 Нет данных.")
        return
    sample = df.sample(1).iloc[0]
    await update.message.reply_text(
        f"🎲 Случайный проект:\n• {sample['project']} — {sample['report_date'].day} числа. Ответственный: {sample['responsible']}"
    )


# Уведомления
async def send_scheduled_notifications(app, days_before):
    msgs = generate_reminders(days_before)
    chat_id = load_chat_id()
    if not chat_id:
        logging.warning("❗ chat_id не найден, уведомления не отправлены.")
        return

    for msg in msgs:
        await app.bot.send_message(chat_id=chat_id, text=msg)


# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_3days", test_3days))
    app.add_handler(CommandHandler("test_1day", test_1day))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))
    app.add_handler(CommandHandler("test_random", test_random))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 5)), 'cron', hour=9, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 3)), 'cron', hour=9, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 1)), 'cron', hour=9, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 0)), 'cron', hour=9, minute=0)
    scheduler.start()

    logging.info("✅ ClientOpsBot запущен.")
    await app.run_polling()

# Запуск
asyncio.run(main())
