import logging
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue
import csv

# === НАСТРОЙКИ ===
TOKEN = '8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk'
CHAT_ID = 'YOUR_CHAT_ID'  # укажи ID чата или сделай динамическое получение

CSV_FILE = 'projects.csv'

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ЧТЕНИЕ CSV ===
def read_projects():
    projects = []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Дата отчета проекта') and row.get('Ответственный'):
                projects.append({
                    'name': row['Название проекта'],
                    'report_day': int(row['Дата отчета проекта']),
                    'owner': row['Ответственный']
                })
    return projects

# === НАПОМИНАНИЕ ЗА 5 ДНЕЙ ===
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now()
    day = today.day
    month_days = (today.replace(month=today.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
    target_day = (day + 5) if day + 5 <= month_days else (day + 5 - month_days)
    projects = read_projects()

    msg = "⏳ *Напоминание за 5 дней до отчета:*\n"
    found = False
    for p in projects:
        if p['report_day'] == target_day:
            msg += f"— {p['name']} (отв. @{p['owner']})\n"
            found = True

    if found:
        await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

# === НАПОМИНАНИЕ В ДЕНЬ ОТЧЕТА ===
async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today_day = datetime.datetime.now().day
    projects = read_projects()

    msg = "📢 *Сегодня сдача отчета по проектам:*\n"
    found = False
    for p in projects:
        if p['report_day'] == today_day:
            msg += f"— {p['name']} (отв. @{p['owner']})\n"
            found = True

    if found:
        await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

# === WEEKLY START ===
async def weekly_start(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=CHAT_ID, text="🔔 *Начало недели — проверьте план по отчетам.*", parse_mode="Markdown")

# === WEEKLY END ===
async def weekly_end(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=CHAT_ID, text="✅ *Конец недели — убедитесь, что все отчеты отправлены.*", parse_mode="Markdown")

# === ОБРАБОТЧИКИ КОМАНД ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """👋 Привет! Я — ClientOpsBot.
Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
• За 5 дней до даты сдачи
• В день сдачи отчета

Тестовые команды:
/test_5days — проверить напоминание за 5 дней
/test_today — проверить напоминание в день сдачи
"""
    await update.message.reply_text(msg)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_5days(context)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_today(context)

async def test_weekly_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await weekly_start(context)

async def test_weekly_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await weekly_end(context)

# === ОСНОВНОЙ ЗАПУСК ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("weekly_start", test_weekly_start))
    app.add_handler(CommandHandler("weekly_end", test_weekly_end))

    # задачи
    job_queue: JobQueue = app.job_queue
    job_queue.run_daily(notify_5days, time=datetime.time(9, 0))
    job_queue.run_daily(notify_today, time=datetime.time(9, 0))
    job_queue.run_daily(weekly_start, time=datetime.time(9, 0), days=(0,))  # ПН
    job_queue.run_daily(weekly_end, time=datetime.time(18, 0), days=(4,))   # ПТ

    logger.info("Запуск ClientOpsBot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
