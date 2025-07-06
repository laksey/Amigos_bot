import nest_asyncio
nest_asyncio.apply()

import logging
import pandas as pd
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# Настройки
TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'
CSV_FILE = 'projects.csv'
TIMEZONE = 'Europe/Moscow'

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Чтение CSV
def load_projects():
    try:
        df = pd.read_csv(CSV_FILE)
        df['report_date'] = pd.to_datetime(df['report_date'], format='%d')  # только число
        return df
    except Exception as e:
        logging.error(f"Ошибка чтения CSV: {e}")
        return pd.DataFrame(columns=['project', 'responsible', 'report_date'])

# Генерация сообщений
def generate_reminders(days_before: int) -> list[str]:
    today = datetime.now(tz).date()
    try:
        df = pd.read_csv(CSV_PATH)
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d').dt.date
    except Exception as e:
        logging.error(f"Ошибка чтения CSV: {e}")
        return [f"❌ Ошибка чтения CSV: {e}"]

    messages = []

    for _, row in df.iterrows():
        report_date = row['date']
        if report_date.month != today.month:
            continue  # Пропускаем другие месяцы

        # ⚠️ Исключаем отчёты, которые уже прошли
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
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n"
        "/report_1 — отчёт по предстоящим отчетам\n"
        "/report_5 — итоговый отчет недели"
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msgs = generate_reminders(5)
    if msgs:
        for msg in msgs:
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("На сегодня напоминаний за 5 дней нет.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msgs = generate_reminders(0)
    if msgs:
        for msg in msgs:
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Сегодня нет отчетов.")

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now()
    df = load_projects()
    df['report_date'] = df['report_date'].apply(lambda d: datetime(today.year, today.month, d.day))
    week = today + timedelta(days=7)

    upcoming = df[df['report_date'] <= week]
    if not upcoming.empty:
        message = "📅 Предстоящие отчёты на неделе:\n"
        for _, row in upcoming.iterrows():
            message += f"• {row['project']} — {row['report_date'].day} числа. Ответственный: {row['responsible']}\n"
        message += "\n🧾 Напомните клиентам об оплате!"
    else:
        message = "На этой неделе нет предстоящих отчетов."

    await update.message.reply_text(message)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_projects()
    message = "📤 Отчёты, отправленные на этой неделе:\n"
    for _, row in df.iterrows():
        message += f"• {row['project']} — {row['responsible']}\n"
    message += "\nПожалуйста, подтвердите, что все отчеты были отправлены."
    await update.message.reply_text(message)

# Задачи
async def send_scheduled_notifications(app, days_before):
    msgs = generate_reminders(days_before)
    for msg in msgs:
        await app.bot.send_message(chat_id='@your_channel_or_chat_id', text=msg)

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 5)), 'cron', hour=9, minute=0)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 0)), 'cron', hour=9, minute=0)
    scheduler.start()

    logging.info("✅ ClientOpsBot запущен.")
    await app.run_polling()

# Запуск
asyncio.run(main())
