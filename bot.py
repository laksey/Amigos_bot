import csv
import datetime
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_FILE = 'projects.csv'
TIMEZONE = datetime.timezone(datetime.timedelta(hours=3))  # Москва
BOT_TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"

def read_csv_rows(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        return list(csv.reader(csvfile))

def load_projects():
    today = datetime.datetime.now(TIMEZONE).date()
    projects = []
    for row in read_csv_rows(CSV_FILE):
        name = row[0].strip()
        responsible = row[1].strip()
        try:
            report_day = int(row[2].strip())
            report_date = today.replace(day=report_day)
            if report_date < today or report_date.month != today.month:
                next_month = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
                report_date = next_month.replace(day=report_day)
            projects.append({'name': name, 'responsible': responsible, 'date': report_date})
        except Exception as e:
            logger.warning(f"Ошибка в строке: {row} — {e}")
    return projects

async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    projects = [p for p in load_projects() if (p['date'] - today).days == 5]
    if projects:
        text = "Напоминание: через 5 дней нужно сдать отчет по проектам:\n"
        text += "\n".join([f"• {p['name']} — {p['responsible']}" for p in projects])
        await context.bot.send_message(chat_id=context.job.chat_id, text=text)

async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    projects = [p for p in load_projects() if p['date'] == today]
    if projects:
        text = "Сегодня день сдачи отчета по проектам:\n"
        text += "\n".join([f"• {p['name']} — {p['responsible']}" for p in projects])
        await context.bot.send_message(chat_id=context.job.chat_id, text=text)

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n"
        "/report_1 — список проектов на этой неделе, чтобы напомнить клиентам об оплате\n"
        "/report_5 — итоговый отчет в пятницу с упоминанием @ellobodefuego"
    )
    await update.message.reply_text(text)

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job = type("Job", (), {"chat_id": update.message.chat_id})
    await notify_5days(context)

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job = type("Job", (), {"chat_id": update.message.chat_id})
    await notify_today(context)

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    end = today + datetime.timedelta(days=(6 - today.weekday()))
    projects = [p for p in load_projects() if today <= p['date'] <= end]
    if projects:
        text = "📝 На этой неделе нужно сдать отчеты по проектам:\n"
        text += "\n".join([f"• {p['name']} — {p['responsible']} (до {p['date'].day})" for p in projects])
        text += "\n\nРекомендуем напомнить клиентам об оплате."
    else:
        text = "На этой неделе сдача отчетов не запланирована."
    await update.message.reply_text(text)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now(TIMEZONE).date()
    start = today.replace(day=1)
    end = (start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    projects = [p for p in load_projects() if start <= p['date'] <= end]
    if projects:
        text = "📊 Итоговый отчет по проектам в этом месяце:\n"
        text += "\n".join([f"• {p['name']} — {p['responsible']} (до {p['date'].day})" for p in projects])
        text += "\n\n@ellobodefuego, подтвердите, что отчеты отправлены."
    else:
        text = "В этом месяце нет проектов с отчетами."
    await update.message.reply_text(text)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(notify_5days, CronTrigger(day_of_week='mon', hour=9, minute=0, timezone=TIMEZONE), kwargs={"context": app})
    scheduler.add_job(notify_today, CronTrigger(day_of_week='fri', hour=9, minute=0, timezone=TIMEZONE), kwargs={"context": app})
    scheduler.start()

    logger.info("Запуск ClientOpsBot...")
    await app.initialize()
    await app.start()
    await app.run_polling()

# Обертка запуска
async def runner():
    await main()

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(runner())
    except Exception as e:
        print("Ошибка запуска:", e)
