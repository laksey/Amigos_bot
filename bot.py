import logging
import random
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk"

# Примеры проектов
EXAMPLE_PROJECTS = [
    ("Проект Альфа", "@user1", "2025-07-08"),
    ("Проект Бета", "@user2", "2025-07-10"),
    ("Проект Гамма", "@user3", "2025-07-12"),
    ("Проект Дельта", "@user4", "2025-07-14"),
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_random_projects(n=3):
    return random.sample(EXAMPLE_PROJECTS, n)


def format_projects(projects):
    return "\n".join(
        [f"• {name} — {user}, дедлайн {date}" for name, user, date in projects]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Доступные команды:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день сдачи\n"
        "/weekly_start — старт недели, список задач на эту неделю\n"
        "/weekly_end — завершение недели, подтверждение сдачи\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_random_projects()
    msg = "⏰ Напоминание: через 5 дней сдача отчетов по проектам:\n\n"
    msg += format_projects(projects)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_random_projects()
    msg = "🚨 Напоминание: сегодня нужно сдать отчеты по проектам:\n\n"
    msg += format_projects(projects)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


async def weekly_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_random_projects()
    payments = get_random_projects(2)
    msg = "📝 На этой неделе нужно сдать отчеты:\n\n"
    msg += format_projects(projects)
    msg += "\n\n💰 Напоминаем про оплату по отчетам прошлой недели:\n\n"
    msg += format_projects(payments)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


async def weekly_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    projects = get_random_projects()
    msg = (
        "📩 Завершается неделя. @ellobodefuego, подтвердите, пожалуйста, что отчеты сданы:\n\n"
    )
    msg += format_projects(projects)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("weekly_start", weekly_start))
    app.add_handler(CommandHandler("weekly_end", weekly_end))

    app.run_polling()
