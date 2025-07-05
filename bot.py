
import logging
import datetime
import csv
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_PATH = "projects.csv"
ADMIN_USERNAME = "@ellobodefuego"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_projects_csv(filepath):
    projects = []
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                project = {
                    "project_name": row["Проект"].strip(),
                    "responsible": row["Аккауннт "].strip(),
                    "report_day": int(row["Дата отчета проекта "].strip())
                }
                projects.append(project)
            except Exception as e:
                logger.error(f"Ошибка чтения строки: {row}, {e}")
    return projects

def is_working_day(date):
    return date.weekday() < 5

def get_next_working_day(date):
    while not is_working_day(date):
        date += datetime.timedelta(days=1)
    return date

def get_today_projects(days_delta=0):
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).date()
    target_date = today + datetime.timedelta(days=days_delta)
    day = target_date.day
    return [p for p in read_projects_csv(CSV_PATH) if p["report_day"] == day]

async def notify_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_today_projects(5)
    if not projects:
        await update.message.reply_text("Нет проектов с отчетом через 5 дней.")
        return
    text = "Напоминание: через 5 дней нужно сдать отчет по проектам:
"
    text += "
".join(f"• {p['project_name']} — {p['responsible']}" for p in projects)
    await update.message.reply_text(text)

async def notify_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_today_projects(0)
    if not projects:
        await update.message.reply_text("Нет проектов с отчетом сегодня.")
        return
    text = "Сегодня день сдачи отчета по проектам:
"
    text += "
".join(f"• {p['project_name']} — {p['responsible']}" for p in projects)
    await update.message.reply_text(text)

async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_today_projects(0)
    if not projects:
        await update.message.reply_text("Нет отчетов на этой неделе.")
        return
    text = "📋 Предстоящие отчеты на этой неделе:
"
    text += "
".join(f"• {p['project_name']} — {p['responsible']}" for p in projects)
    text += "

Пожалуйста, напомните клиентам об оплате."
    await update.message.reply_text(text)

async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_today_projects(0)
    if not projects:
        await update.message.reply_text("Нет отчетов в этом цикле.")
        return
    text = f"@{ADMIN_USERNAME}
"
    text += "📤 Подтверди, что отчеты по этим проектам отправлены:
"
    text += "
".join(f"• {p['project_name']} — {p['responsible']}" for p in projects)
    await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", notify_5days))
    app.add_handler(CommandHandler("test_today", notify_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    await app.run_polling()

# Обертка для запуска в уже работающем event loop
async def runner():
    await main()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(runner())
        else:
            loop.run_until_complete(runner())
    except Exception as e:
        print("Ошибка запуска:", e)
