import csv
import datetime
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"
CSV_FILE = "projects.csv"
ADMIN_NICK = "@ellobodefuego"
CHAT_ID_FILE = "chat_id.txt"

# Чтение данных из таблицы
def read_projects():
    projects = []
    if not os.path.exists(CSV_FILE):
        return projects
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Название проекта")
            owner = row.get("Ответственный (ник в ТГ)")
            due_day = row.get("Дата отчета проекта")
            if name and owner and due_day:
                try:
                    projects.append((name.strip(), owner.strip(), int(due_day)))
                except ValueError:
                    continue
    return projects

# Получить список проектов по числу
def get_projects_by_day(day):
    return [(name, owner) for (name, owner, due_day) in read_projects() if due_day == day]

# Получить список проектов за прошедшую неделю (для оплаты)
def get_projects_last_week(today):
    last_week = []
    for name, owner, due_day in read_projects():
        delta = (today.day - due_day) % 31
        if 1 <= delta <= 7:
            last_week.append((name, owner))
    return last_week

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(CHAT_ID_FILE, "w") as f:
        f.write(str(update.effective_chat.id))
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n"
        "/weekly_start — понедельничный отчет\n"
        "/weekly_end — пятничное подтверждение отчетов"
    )

# Уведомление в день отчета
async def notify_today(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now().day
    chat_id = get_chat_id()
    projects = get_projects_by_day(today)
    for name, owner in projects:
        msg = f"📢 Сегодня сдаётся отчет по проекту *{name}*. {owner}, не забудь!"
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

# Напоминание за 5 дней
async def notify_5days(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.datetime.now()
    in_5_days = (today.day + 5 - 1) % 31 + 1
    chat_id = get_chat_id()
    projects = get_projects_by_day(in_5_days)
    for name, owner in projects:
        msg = f"⏰ Через 5 дней нужно сдать отчет по проекту *{name}*. {owner}, подготовься!"
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

# Команда /test_today
async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_today(context)

# Команда /test_5days
async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await notify_5days(context)

# /weekly_start — Понедельник 9:00
async def weekly_start(context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_chat_id()
    today = datetime.datetime.now()
    msg = "📝 *На этой неделе нужно сдать отчеты:*\n\n"
    upcoming = []
    for name, owner, due_day in read_projects():
        if 0 <= (due_day - today.day) % 31 <= 6:
            upcoming.append(f"• {name} — {owner} (день {due_day})")
    msg += "\n".join(upcoming) if upcoming else "Нет отчетов на этой неделе."
    # Отчеты на прошлой неделе для напоминания об оплате
    msg += "\n\n💸 *Проверьте оплату по проектам сданным на прошлой неделе:*\n\n"
    last_week = get_projects_last_week(today)
    msg += "\n".join([f"• {name} — {owner}" for name, owner in last_week]) if last_week else "Нет проектов."
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

# /weekly_end — Пятница 18:00
async def weekly_end(context: ContextTypes.DEFAULT_TYPE):
    chat_id = get_chat_id()
    projects = get_projects_last_week(datetime.datetime.now())
    msg = f"📤 Завершается неделя. {ADMIN_NICK}, подтверди пожалуйста, что отчеты сданы:\n\n"
    msg += "\n".join([f"• {name} — {owner}" for name, owner in projects]) if projects else "Нет отчетов."
    await context.bot.send_message(chat_id=chat_id, text=msg)

# Получение chat_id
def get_chat_id():
    if not os.path.exists(CHAT_ID_FILE):
        return None
    with open(CHAT_ID_FILE, "r") as f:
        return int(f.read().strip())

# Запуск бота
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Регистрация команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("weekly_start", weekly_start))
    app.add_handler(CommandHandler("weekly_end", weekly_end))

    # Планировщик задач
    scheduler = AsyncIOScheduler()
    scheduler.add_job(notify_today, "cron", hour=9)
    scheduler.add_job(notify_5days, "cron", hour=10)
    scheduler.add_job(weekly_start, "cron", day_of_week="mon", hour=9)
    scheduler.add_job(weekly_end, "cron", day_of_week="fri", hour=18)
    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

# Запуск с проверкой event loop
if __name__ == "__main__":
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(main())
    else:
        asyncio.run(main())
