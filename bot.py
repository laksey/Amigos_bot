
import csv
import datetime
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = "YOUR_BOT_TOKEN"  # Подставь реальный токен
CHAT_USERNAME = "@ellobodefuego"
CSV_PATH = "projects.csv"

def read_projects():
    projects = []
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            projects.append(row)
    return projects

def get_upcoming_reports(projects):
    today = datetime.date.today()
    week_end = today + datetime.timedelta(days=(6 - today.weekday()))
    return [p for p in projects if get_date(p['Дата сдачи']) and today <= get_date(p['Дата сдачи']) <= week_end]

def get_last_week_reports(projects):
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday() + 7)
    week_end = week_start + datetime.timedelta(days=6)
    return [p for p in projects if get_date(p['Дата сдачи']) and week_start <= get_date(p['Дата сдачи']) <= week_end]

def get_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
    except:
        return None

async def send_start_of_week(context):
    projects = read_projects()
    upcoming = get_upcoming_reports(projects)
    past = get_last_week_reports(projects)

    msg = "📝 На этой неделе нужно сдать отчеты:
"
    for p in upcoming:
        msg += f"- {p['Название проекта']} (ответственный {p['Ответственный']}, до {p['Дата сдачи']})
"

    msg += "
💰 Напомни клиенту об оплате по проектам:
"
    for p in past:
        msg += f"- {p['Название проекта']} (ответственный {p['Ответственный']})
"

    await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def send_end_of_week(context):
    projects = read_projects()
    msg = f"📅 Завершается неделя. {CHAT_USERNAME}, подтверди пожалуйста, что отчеты сданы:
"
    for p in get_upcoming_reports(projects):
        msg += f"- {p['Название проекта']} (ответственный {p['Ответственный']})
"

    await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

async def start(update, context):
    await update.message.reply_text("Бот активирован. Отчеты будут отправляться автоматически.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
