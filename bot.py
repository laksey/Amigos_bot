import os
import datetime
import random
from telegram import Bot
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
PROJECTS_FILE = "projects.csv"

def load_projects():
    with open(PROJECTS_FILE, encoding="utf-8") as f:
        lines = f.readlines()[1:]
    projects = []
    for line in lines:
        name, username, due = line.strip().split(",")
        projects.append({
            "name": name,
            "username": username,
            "due": int(due)
        })
    return projects

def get_weekly_report():
    projects = load_projects()
    today = datetime.date.today()
    last_monday = today - datetime.timedelta(days=today.weekday() + 7)
    this_monday = today - datetime.timedelta(days=today.weekday())
    due_this_week = [p for p in projects if this_monday.day <= p['due'] <= this_monday.day + 6]
    due_last_week = [p for p in projects if last_monday.day <= p['due'] <= last_monday.day + 6]
    msg = "📝 На этой неделе нужно сдать отчеты:
"
    for p in due_this_week:
        msg += f"• {p['name']} – @{p['username']} (до {p['due']})
"
    msg += "
💰 Напоминание клиентам об оплате за прошлую неделю:
"
    for p in due_last_week:
        msg += f"• {p['name']} – @{p['username']}
"
    return msg

def get_confirmation_request():
    projects = load_projects()
    today = datetime.date.today()
    this_monday = today - datetime.timedelta(days=today.weekday())
    due_this_week = [p for p in projects if this_monday.day <= p['due'] <= this_monday.day + 6]
    msg = "Завершается неделя. @ellobodefuego, подтверди пожалуйста, что отчеты сданы:
"
    for p in due_this_week:
        msg += f"• {p['name']} – @{p['username']}
"
    return msg

async def weekly_start(update, context):
    msg = get_weekly_report()
    await update.message.reply_text(msg)

async def weekly_end(update, context):
    msg = get_confirmation_request()
    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start_week", weekly_start))
    app.add_handler(CommandHandler("end_week", weekly_end))
    app.run_polling()

if __name__ == "__main__":
    main()
