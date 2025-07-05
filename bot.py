from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import nest_asyncio
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Стартовое сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5 дней до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Чтобы протестировать, используйте:\n"
        "/test_5days — проверка напоминания за 5 дней\n"
        "/test_today — проверка напоминания в день отчета\n"
        "/report_1 — отчет по предстоящим отчетам на этой неделе\n"
        "/report_5 — отчет в конце недели с подтверждением\n\n"
        "Бот активирован. Ожидайте уведомлений в соответствии с графиком."
    )
    await update.message.reply_text(message)

# Тестовая команда: за 5 дней
async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔔 Тест: Через 5 дней дедлайн отчета по проекту «Проект X»!")

# Тестовая команда: в день сдачи
async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Тест: Сегодня необходимо отправить отчет по проекту «Проект Y»!")

# Отчет на неделе
async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Отчет по предстоящим сдачам отчетов на неделе:\n"
        "— Проект X — 10.07\n"
        "— Проект Y — 12.07\n\n"
        "Пожалуйста, напомните клиентам об оплате."
    )

# Финальный отчет недели
async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Все отчеты за неделю отправлены?\n"
        "Пожалуйста, подтвердите отправку.\n"
        "Ответственный: @admin"
    )

# Запуск бота
async def main():
    app = ApplicationBuilder().token("8095206946:AAFlOJi0BoRr9Z-MJMigWkk6arT9Ck-uhRk").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    logger.info("Запуск ClientOpsBot...")
    await app.run_polling()

# Инициализация
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
