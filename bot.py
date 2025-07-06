import logging
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Конфигурация
BOT_TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'
TIMEZONE = pytz.timezone("Europe/Moscow")
CSV_FILE = "projects.csv"
ADMIN_TELEGRAM = "@ellobodefuego"

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Загрузка данных
def load_projects():
    try:
        df = pd.read_csv(CSV_FILE)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df.dropna(subset=['date'], inplace=True)
        return df
    except Exception as e:
        logging.error(f"Ошибка чтения CSV: {e}")
        return pd.DataFrame()

# Уведомления
async def notify_projects(context: ContextTypes.DEFAULT_TYPE, diff_days=5):
    df = load_projects()
    today = datetime.now(TIMEZONE).date()
    target_date = today + timedelta(days=diff_days)

    for _, row in df.iterrows():
        if row['date'].date() == target_date:
            await context.bot.send_message(chat_id=row['chat_id'],
                text=f"⏰ Напоминание: через {diff_days} дней сдача отчета по проекту: *{row['project']}*",
                parse_mode="Markdown")

async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    df = load_projects()
    today = datetime.now(TIMEZONE).date()

    for _, row in df.iterrows():
        if row['date'].date() == today:
            await context.bot.send_message(chat_id=row['chat_id'],
                text=f"📅 Сегодня день сдачи отчета по проекту: *{row['project']}*",
                parse_mode="Markdown")

async def report_1(context: ContextTypes.DEFAULT_TYPE):
    df = load_projects()
    today = datetime.now(TIMEZONE).date()
    end = today + timedelta(days=7)
    upcoming = df[(df['date'].dt.date >= today) & (df['date'].dt.date <= end)]

    if upcoming.empty:
        text = "🔍 На этой неделе отчеты не запланированы."
    else:
        lines = ["📌 Отчеты на этой неделе:"]
        for _, row in upcoming.iterrows():
            lines.append(f"• {row['project']} — {row['date'].date()}")
        lines.append("\n❗ Не забудьте напомнить клиентам об оплате.")

        text = "\n".join(lines)

    await context.bot.send_message(chat_id=ADMIN_TELEGRAM, text=text)

async def report_5(context: ContextTypes.DEFAULT_TYPE):
    df = load_projects()
    today = datetime.now(TIMEZONE).date()
    sent = df[df['date'].dt.date <= today]

    if sent.empty:
        text = "ℹ️ На этой неделе отчеты не отправлялись."
    else:
        lines = ["✅ На этой неделе были сданы отчеты по:"]
        for _, row in sent.iterrows():
            lines.append(f"• {row['project']} — {row['date'].date()}")
        lines.append(f"\n{ADMIN_TELEGRAM}, подтвердите, что все отчеты были отправлены.")

        text = "\n".join(lines)

    await context.bot.send_message(chat_id=ADMIN_TELEGRAM, text=text)

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Тест напоминания за 5 дней выполнен.")
    await notify_projects(context, diff_days=5)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Тест напоминания на сегодня выполнен.")
    await notify_today(context)

async def test_report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await report_1(context)

async def test_report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await report_5(context)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", test_report_1))
    app.add_handler(CommandHandler("report_5", test_report_5))

    # Планировщик
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(notify_projects, trigger=CronTrigger(hour=9, minute=0), kwargs={"context": app.bot, "diff_days": 5}, name="notify_5days")
    scheduler.add_job(notify_today, trigger=CronTrigger(hour=9, minute=0), kwargs={"context": app.bot}, name="notify_today")
    scheduler.start()

    logging.info("✅ ClientOpsBot запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
