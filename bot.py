import datetime
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler
import csv
import random

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
PROJECTS_CSV = "projects.csv"
ADMIN_NICK = "@ellobodefuego"


def get_projects():
    projects = []
    with open(PROJECTS_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            projects.append({
                "Проект": row["название проекта"],
                "Ответственный": row["ответственный (ник тг)"],
                "Дата": row["дата сдачи"]
            })
    return projects


def get_this_week_reports():
    today = datetime.date.today()
    return [p for p in get_projects() if int(p["Дата"]) == today.day]


def get_last_week_reports():
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)
    return [p for p in get_projects() if int(p["Дата"]) == last_week.day]


async def send_monday_report(update, context):
    this_week = get_this_week_reports()
    last_week = get_last_week_reports()

    msg = "📝 На этой неделе нужно сдать отчеты:\n"
    for p in this_week:
        msg += f"— *{p['Проект']}* ({p['Ответственный']})\n"

    msg += "\n💸 Напоминание об оплате по проектам с отчетами на прошлой неделе:\n"
    for p in last_week:
        msg += f"— *{p['Проект']}* ({p['Ответственный']})\n"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="Markdown"
    )


async def send_confirmation_request(update, context):
    last_week = get_last_week_reports()
    msg = f"🔁 Завершается неделя. {ADMIN_NICK}, подтверди, пожалуйста, что отчеты сданы:\n"
    for p in last_week:
        msg += f"— *{p['Проект']}* ({p['Ответственный']})\n"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg,
        parse_mode="Markdown"
    )


def test_random_data():
    with open(PROJECTS_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["название проекта", "ответственный (ник тг)", "дата сдачи"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(5):
            writer.writerow({
                "название проекта": f"Проект {i+1}",
                "ответственный (ник тг)": f"@user{i+1}",
                "дата сдачи": str(random.randint(1, 31))
            })


async def main():
    test_random_data()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", send_monday_report))
    application.add_handler(CommandHandler("confirm", send_confirmation_request))
    await application.run_polling()


# Проверка окружения
if __name__ == "__main__":
    try:
        asyncio.get_running_loop().create_task(main())
    except RuntimeError:
        asyncio.run(main())
