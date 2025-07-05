import csv
import datetime
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CHAT_ID_FILE = "chat_id.txt"
CSV_FILE = "projects.csv"

async def send_message(bot: Bot, text: str):
    try:
        with open(CHAT_ID_FILE, "r") as f:
            chat_id = f.read().strip()
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error sending message: {e}")

def load_projects():
    today = datetime.date.today()
    projects_today = []
    projects_5days = []
    projects_week = []
    projects_lastweek = []

    with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            project = row['название проекта']
            user = row['ответственный (ник тг)']
            date_str = row['дата сдачи']
            try:
                day = int(date_str)
                report_date = datetime.date(today.year, today.month, min(day, 28))
            except:
                continue

            delta = (report_date - today).days

            if delta == 0:
                projects_today.append((project, user))
            if delta == 5:
                projects_5days.append((project, user))
            if 0 <= delta <= 6:
                projects_week.append((project, user))
            if -7 <= delta < 0:
                projects_lastweek.append((project, user))

    return projects_today, projects_5days, projects_week, projects_lastweek

async def weekly_start(app):
    bot = app.bot
    _, _, week, unpaid = load_projects()
    msg = "📝 *На этой неделе нужно сдать отчеты:*
" + "\n".join([f"- *{p}* (@{u})" for p, u in week])
    if unpaid:
        msg += "\n\n💰 *Необходимо напомнить об оплате по проектам:*\n" + "\n".join([f"- *{p}* (@{u})" for p, u in unpaid])
    await send_message(bot, msg)

async def weekly_end(app):
    bot = app.bot
    _, _, _, unpaid = load_projects()
    msg = "📌 Завершается неделя. @ellobodefuego, подтвердите, пожалуйста, что следующие отчеты были отправлены:\n"
    msg += "\n".join([f"- *{p}* (@{u})" for p, u in unpaid])
    await send_message(bot, msg)

async def test_start(update, context):
    await weekly_start(context.application)

async def test_end(update, context):
    await weekly_end(context.application)

async def start(update, context):
    chat_id = str(update.effective_chat.id)
    with open(CHAT_ID_FILE, "w") as f:
        f.write(chat_id)
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n"
        "• Автоматический отчет по понедельникам и пятницам\n\n"
        "Для теста используйте:\n"
        "/test_start — понедельник\n"
        "/test_end — пятница"
    )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_start", test_start))
    app.add_handler(CommandHandler("test_end", test_end))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(weekly_start(app)), CronTrigger(day_of_week='mon', hour=9))
    scheduler.add_job(lambda: asyncio.create_task(weekly_end(app)), CronTrigger(day_of_week='fri', hour=18))
    scheduler.start()

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
