import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ParseMode
import datetime
import csv
import random

# Настройки
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_FILE = "projects.csv"
ADMIN_NICK = "@ellobodefuego"

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Чтение CSV
def load_projects():
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

# Получение проектов по дню
def get_projects_by_day(day: int):
    projects = load_projects()
    today_projects = [p for p in projects if p["Дата отчета проекта"].isdigit() and int(p["Дата отчета проекта"]) == day]
    return today_projects

# Получение проектов за 5 дней до дедлайна
def get_projects_in_5_days():
    today = datetime.date.today()
    target_day = (today + datetime.timedelta(days=5)).day
    projects = load_projects()
    return [p for p in projects if p["Дата отчета проекта"].isdigit() and int(p["Дата отчета проекта"]) == target_day]

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
👋 Привет! Я — ClientOpsBot.

Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
• За 5 дней до даты сдачи
• В день сдачи отчета
• В понедельник — список проектов, у которых на этой неделе дедлайн
• В пятницу — список проектов, по которым нужно подтвердить сдачу

Тестовые команды:
/test_5days — проверка напоминания за 5 дней
/test_today — проверка напоминания в день отчета
/weekly_start — ручной запуск понедельничного напоминания
/weekly_end — ручной запуск пятничного напоминания
"""
    await update.message.reply_text(msg)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_today(context)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_5days(context)

# Уведомление в день отчета
async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today().day
    projects = get_projects_by_day(today)
    if not projects:
        return

    msg = "📍 *Сегодня крайний срок сдачи отчетов по проектам:*\n"
    for p in projects:
        msg += f"- {p['Название проекта']} ({p['Ответственный']})\n"

    await context.bot.send_message(chat_id=context._chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

# Уведомление за 5 дней
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    projects = get_projects_in_5_days()
    if not projects:
        return

    msg = "⏳ *Через 5 дней нужно сдать отчеты по проектам:*\n"
    for p in projects:
        msg += f"- {p['Название проекта']} ({p['Ответственный']})\n"

    await context.bot.send_message(chat_id=context._chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

# Еженедельное начало (понедельник)
async def weekly_start(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None):
    projects = load_projects()
    today = datetime.date.today()
    week_days = [(today + datetime.timedelta(days=i)).day for i in range(7)]
    weekly_projects = [p for p in projects if p["Дата отчета проекта"].isdigit() and int(p["Дата отчета проекта"]) in week_days]

    if not weekly_projects:
        return

    msg = "🗓 *На этой неделе нужно сдать отчеты по проектам:*\n"
    for p in weekly_projects:
        msg += f"- {p['Название проекта']} ({p['Ответственный']}) — {p['Дата отчета проекта']} числа\n"

    await context.bot.send_message(chat_id=context._chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

# Еженедельное завершение (пятница)
async def weekly_end(update: Update = None, context: ContextTypes.DEFAULT_TYPE = None):
    projects = load_projects()
    today = datetime.date.today()
    week_days = [(today - datetime.timedelta(days=i)).day for i in range(7)]
    reported_projects = [p for p in projects if p["Дата отчета проекта"].isdigit() and int(p["Дата отчета проекта"]) in week_days]

    if not reported_projects:
        return

    msg = f"🔔 *Завершается неделя.* {ADMIN_NICK}, подтвердите, что отчеты сданы по проектам:\n"
    for p in reported_projects:
        msg += f"- {p['Название проекта']} ({p['Ответственный']}) — {p['Дата отчета проекта']} числа\n"

    await context.bot.send_message(chat_id=context._chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("weekly_start", weekly_start))
    app.add_handler(CommandHandler("weekly_end", weekly_end))

    # Планировщик
    app.job_queue.run_daily(notify_today, time=datetime.time(9, 0))
    app.job_queue.run_daily(notify_5days, time=datetime.time(10, 0))
    app.job_queue.run_daily(weekly_start, time=datetime.time(9, 0), days=(0,))
    app.job_queue.run_daily(weekly_end, time=datetime.time(18, 0), days=(4,))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
