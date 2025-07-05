import datetime
import random
import csv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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


def get_reports_by_day(target_day: int):
    return [p for p in get_projects() if int(p["Дата"]) == target_day]


async def send_monday_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    this_week = get_reports_by_day(today.day)
    last_week = get_reports_by_day((today - datetime.timedelta(days=7)).day)

    msg = "📝 На этой неделе нужно сдать отчеты:\n"
    for p in this_week:
        msg += f"— *{p['Проект']}* ({p['Ответственный']})\n"

    msg += "\n💸 Напоминание об оплате по проектам с отчетами на прошлой неделе:\n"
    for p in last_week:
        msg += f"— *{p['Проект']}* ({p['Ответственный']})\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def send_confirmation_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_week = get_reports_by_day((datetime.date.today() - datetime.timedelta(days=7)).day)

    msg = f"🔁 Завершается неделя. {ADMIN_NICK}, подтверди, пожалуйста, что отчеты сданы:\n"
    for p in last_week:
        msg += f"— *{p['Проект']}* ({p['Ответственный']})\n"

    await update.message.reply_text(msg, parse_mode="Markdown")


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


def run_bot():
    test_random_data()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", send_monday_report))
    app.add_handler(CommandHandler("confirm", send_confirmation_request))
    app.run_polling()


if __name__ == "__main__":
    run_bot()
