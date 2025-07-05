import logging
import asyncio
import csv
import datetime
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_FILE = "projects.csv"
ADMIN_MENTION = "@ellobodefuego"
CHAT_ID_FILE = "chat_id.txt"

logging.basicConfig(level=logging.INFO)

def read_projects():
    projects = []
    try:
        with open(CSV_FILE, encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                projects.append({
                    "name": row.get("Название проекта", "").strip(),
                    "tg_nick": row.get("Ответственный (телеграм ник)", "").strip(),
                    "report_date": row.get("Дата отчета проекта", "").strip(),
                })
    except Exception as e:
        logging.error(f"Ошибка при чтении CSV: {e}")
    return projects

def get_weekly_report():
    today = datetime.date.today()
    projects = read_projects()
    this_week = []
    for project in projects:
        try:
            date = datetime.datetime.strptime(project["report_date"], "%d.%m.%Y").date()
            if today <= date <= today + datetime.timedelta(days=6):
                this_week.append(f"- {project['name']} ({project['tg_nick']}) — {project['report_date']}")
        except:
            continue
    if not this_week:
        return "На этой неделе нет запланированных отчетов."
    return "📝 На этой неделе нужно сдать отчеты:
" + "
".join(this_week)

def get_payment_reminders():
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)
    projects = read_projects()
    unpaid = []
    for project in projects:
        try:
            date = datetime.datetime.strptime(project["report_date"], "%d.%m.%Y").date()
            if last_week <= date < today:
                unpaid.append(f"- {project['name']} ({project['tg_nick']}) — {project['report_date']}")
        except:
            continue
    if not unpaid:
        return "Нет проектов, по которым требуется напоминание об оплате."
    return "💰 Напоминание об оплате по отчетам прошлой недели:
" + "
".join(unpaid)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(CHAT_ID_FILE, "w") as f:
        f.write(str(update.effective_chat.id))
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.

"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:
"
        "• За 5 дней до даты сдачи
"
        "• В день сдачи отчета

"
        "Чтобы протестировать, используйте:
"
        "/test_5days — проверка напоминания за 5 дней
"
        "/test_today — проверка напоминания в день отчета
"
        "/weekly_start — тест недельного старта
"
        "/weekly_end — тест завершающего отчета

"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )

async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Тестовое напоминание: до отчета 5 дней.")

async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Тестовое напоминание: отчет по проекту нужно сдать сегодня!")

async def weekly_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_weekly_report() + "

" + get_payment_reminders()
    await update.message.reply_text(msg)

async def weekly_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = read_projects()
    msg = f"📌 Завершается неделя. {ADMIN_MENTION}, подтвердите, пожалуйста, что отчеты сданы по следующим проектам:
"
    for p in projects:
        try:
            date = datetime.datetime.strptime(p['report_date'], "%d.%m.%Y").date()
            if datetime.date.today() - datetime.timedelta(days=6) <= date <= datetime.date.today():
                msg += f"- {p['name']} ({p['tg_nick']}) — {p['report_date']}
"
        except:
            continue
    await update.message.reply_text(msg)

async def scheduled_tasks(application):
    chat_id = None
    try:
        with open(CHAT_ID_FILE) as f:
            chat_id = int(f.read().strip())
    except Exception as e:
        logging.error("Файл chat_id.txt не найден. Используйте команду /start в чате с ботом.")
        return

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(lambda: application.bot.send_message(chat_id, get_weekly_report() + "

" + get_payment_reminders()), CronTrigger(day_of_week="mon", hour=9, minute=0))
    scheduler.add_job(lambda: application.bot.send_message(chat_id, f"📌 Завершается неделя. {ADMIN_MENTION}, подтвердите, пожалуйста, что отчеты сданы."), CronTrigger(day_of_week="fri", hour=18, minute=0))

    # уведомления за 5 дней и в день отчета
    async def report_notifications():
        today = datetime.date.today()
        projects = read_projects()
        for p in projects:
            try:
                date = datetime.datetime.strptime(p['report_date'], "%d.%m.%Y").date()
                if date == today + datetime.timedelta(days=5):
                    await application.bot.send_message(chat_id, f"🔔 Через 5 дней сдача отчета: {p['name']} ({p['tg_nick']}) — {p['report_date']}")
                elif date == today:
                    await application.bot.send_message(chat_id, f"📢 Сегодня сдача отчета: {p['name']} ({p['tg_nick']}) — {p['report_date']}")
            except:
                continue

    scheduler.add_job(lambda: asyncio.create_task(report_notifications()), CronTrigger(hour=10, minute=0))
    scheduler.start()

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test_5days", test_5days))
    application.add_handler(CommandHandler("test_today", test_today))
    application.add_handler(CommandHandler("weekly_start", weekly_start))
    application.add_handler(CommandHandler("weekly_end", weekly_end))

    await scheduled_tasks(application)
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())