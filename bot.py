import logging
import datetime
import csv
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"

# Путь к CSV-файлу
CSV_PATH = "projects.csv"

# Чат, куда слать уведомления (замени при необходимости)
TARGET_CHAT_ID = None  # будет определён в /start

def read_projects():
    try:
        with open(CSV_PATH, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except Exception as e:
        logger.error(f"Ошибка чтения CSV: {e}")
        return []

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TARGET_CHAT_ID
    TARGET_CHAT_ID = update.effective_chat.id
    logger.info(f"/start от {TARGET_CHAT_ID}")
    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n"
        "Я буду напоминать об отчетах по проектам:\n"
        "• За 5 дней до сдачи\n"
        "• В день сдачи\n\n"
        "Тестовые команды:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день сдачи\n"
        "/weekly_start — тест еженедельного старта\n"
        "/weekly_end — тест завершения недели"
    )

# Проверка 5-дневного напоминания
async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/test_5days вызван")
    await update.message.reply_text("🔔 Тест: напоминание за 5 дней до отчета")

# Проверка напоминания в день сдачи
async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/test_today вызван")
    await update.message.reply_text("📣 Тест: отчет нужно сдать сегодня!")

# Еженедельный старт — понедельник
async def weekly_start(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Еженедельный старт — отправка списка отчетов")
    projects = read_projects()
    today = datetime.date.today()
    msg_lines = ["📝 *На этой неделе нужно сдать отчеты:*"]
    for proj in projects:
        try:
            due_day = int(proj.get("Дата отчета проекта", "").strip())
            if due_day >= today.day:
                msg_lines.append(f"- {proj['Название проекта']} — @{proj['Ответственный']}")
        except Exception as e:
            logger.warning(f"Ошибка обработки строки: {e}")
    msg = "\n".join(msg_lines)
    await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=msg, parse_mode="Markdown")

# Еженедельное завершение — пятница
async def weekly_end(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Еженедельное завершение — подтверждение отчетов")
    projects = read_projects()
    today = datetime.date.today()
    msg_lines = ["📤 *Подтвердите отправку следующих отчетов:*"]
    for proj in projects:
        try:
            due_day = int(proj.get("Дата отчета проекта", "").strip())
            if due_day <= today.day:
                msg_lines.append(f"- {proj['Название проекта']} — @{proj['Ответственный']}")
        except Exception as e:
            logger.warning(f"Ошибка обработки строки: {e}")
    msg = "\n".join(msg_lines)
    await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=msg, parse_mode="Markdown")

# Команды для ручного запуска
async def weekly_start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/weekly_start вызван вручную")
    await weekly_start(context)

async def weekly_end_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("/weekly_end вызван вручную")
    await weekly_end(context)

# Основной запуск
async def main():
    app = Application.builder().token(TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("weekly_start", weekly_start_cmd))
    app.add_handler(CommandHandler("weekly_end", weekly_end_cmd))

    # Планировщик задач
    app.job_queue.run_daily(weekly_start, time=datetime.time(9, 0), days=(0,))  # Пн
    app.job_queue.run_daily(weekly_end, time=datetime.time(18, 0), days=(4,))   # Пт

    logger.info("Бот запускается…")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
