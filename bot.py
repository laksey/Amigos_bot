import csv
import datetime
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext

TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'
CSV_FILE = 'projects.csv'
MENTION = '@ellobodefuego'

logging.basicConfig(level=logging.INFO)

def read_projects():
    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def is_due_today(project_day: int):
    today = datetime.date.today()
    try:
        return today.day == project_day
    except:
        return False

def is_due_in_days(project_day: int, days_before: int):
    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=days_before)
    try:
        return due_date.day == project_day
    except:
        return False

def format_projects(projects):
    return '\n'.join([f"• {p['Название проекта']} — {p['Ответственный (ник в TG)']}" for p in projects])

async def send_today_reports(context: CallbackContext):
    projects = read_projects()
    today = datetime.date.today()
    due_today = [p for p in projects if int(p['Дата отчета проекта']) == today.day]
    if due_today:
        msg = f"📌 Сегодня сдаём отчёты:\n{format_projects(due_today)}"
        await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def send_5day_reminders(context: CallbackContext):
    projects = read_projects()
    future = datetime.date.today() + datetime.timedelta(days=5)
    reminder = [p for p in projects if int(p['Дата отчета проекта']) == future.day]
    if reminder:
        msg = f"⏰ Через 5 дней сдаём отчёты:\n{format_projects(reminder)}"
        await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def weekly_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = read_projects()
    today = datetime.date.today()
    msg = f"""📝 *На этой неделе нужно сдать отчёты:*\n"""
    for p in projects:
        report_day = int(p['Дата отчета проекта'])
        if today.day <= report_day <= 31:
            msg += f"• {p['Название проекта']} — {p['Ответственный (ник в TG)']} (день: {report_day})\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def weekly_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = read_projects()
    msg = f"✅ Неделя завершается. {MENTION}, подтверди, пожалуйста, что были сданы отчёты по:\n"
    msg += format_projects(projects)
    await update.message.reply_text(msg)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_5day_reminders(context)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_today_reports(context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
👋 Привет! Я — ClientOpsBot.

Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
• За 5 дней до даты сдачи
• В день сдачи отчета

Команды для тестирования:
/test_5days — проверка напоминания за 5 дней
/test_today — проверка напоминания в день сдачи
/weekly_start — еженедельный стартовый отчет
/weekly_end — финальный отчет с подтверждением
""")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("weekly_start", weekly_start))
    app.add_handler(CommandHandler("weekly_end", weekly_end))

    # Автоматические задачи
    app.job_queue.run_daily(send_5day_reminders, time=datetime.time(9, 0))
    app.job_queue.run_daily(send_today_reports, time=datetime.time(9, 0))
    app.job_queue.run_daily(weekly_start, time=datetime.time(9, 0), days=(0,))
    app.job_queue.run_daily(weekly_end, time=datetime.time(18, 0), days=(4,))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
