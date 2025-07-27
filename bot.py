import nest_asyncio
nest_asyncio.apply()

import logging
import pandas as pd
import os
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import pytz
import random

# === Настройки ===
# Получаем токен из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN')  # Токен перенесен в переменные окружения
CSV_FILE = 'projects.csv'
CHAT_ID_FILE = 'chat_id.txt'
TIMEZONE = 'Europe/Moscow'
tz = pytz.timezone(TIMEZONE)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# === Работа с chat_id ===
def save_chat_id(chat_id: int):
    with open(CHAT_ID_FILE, 'w') as f:
        f.write(str(chat_id))
    logging.info(f"💾 chat_id сохранён: {chat_id}")


def load_chat_id() -> int | None:
    try:
        with open(CHAT_ID_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception as e:
        logging.error(f"Не удалось загрузить chat_id: {e}")
        return None


# === Загрузка данных проектов ===
def load_projects():
    try:
        df = pd.read_csv(CSV_FILE)
        df['report_date'] = pd.to_datetime(df['report_date'], format='%d').apply(
            lambda d: datetime(datetime.now().year, datetime.now().month, d.day, tzinfo=tz).date()
        )
        return df
    except Exception as e:
        logging.error(f"Ошибка чтения CSV: {e}")
        return pd.DataFrame(columns=['project', 'responsible', 'report_date'])


# === Генерация напоминаний ===
def generate_reminders(days_before: int) -> list[str]:
    today = datetime.now(tz).date()
    df = load_projects()

    messages = []

    for _, row in df.iterrows():
        report_date = row['report_date']
        if report_date < today:
            continue

        days_until = (report_date - today).days

        if days_before == 0 and days_until == 0:
            messages.append(f"• {row['project']} — сегодня. Ответственный: {row['responsible']}")
        elif days_before > 0 and days_until == days_before:
            messages.append(f"• {row['project']} — {report_date.day} числа. Ответственный: {row['responsible']}")

    if not messages:
        return ["✅ Сегодня нет отчётов."]
    return messages


# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    save_chat_id(chat_id)

    await update.message.reply_text(
        "👋 Привет! Я — ClientOpsBot.\n\n"
        "Я буду напоминать аккаунт-менеджерам об отчетах по проектам:\n"
        "• За 5, 3, 1 день до даты сдачи\n"
        "• В день сдачи отчета\n\n"
        "Для проверки используйте:\n"
        "/test_3days — проверка за 3 дня\n"
        "/test_today — проверка в день сдачи\n"
        "/report_1 — предстоящие отчёты\n"
        "/report_5 — отчёты прошлой недели\n"
        "/test_random — случайный проект"
    )


async def test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int):
    msgs = generate_reminders(days)
    for msg in msgs:
        await update.message.reply_text(msg)


async def test_5days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 5)


async def test_3days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 3)


async def test_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await test_reminder(update, context, 0)


async def report_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now(tz).date()
    weekday = today.weekday()
    monday = today - timedelta(days=weekday)
    friday = monday + timedelta(days=4)

    df = load_projects()
    filtered = df[(df['report_date'] >= today) & (df['report_date'] >= monday) & (df['report_date'] <= friday)]

    if filtered.empty:
        await update.message.reply_text("📭 На этой рабочей неделе нет предстоящих отчетов.")
        return

    filtered = filtered.sort_values(by='report_date')
    message = "📅 Предстоящие отчёты на этой рабочей неделе (Пн–Пт):\n\n"
    for _, row in filtered.iterrows():
        message += f"• {row['project']} — {row['report_date'].day} числа. Ответственный: {row['responsible']}\n"
    message += "\n🔔 Напомните клиентам об оплате!"
    await update.message.reply_text(message)


async def report_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        today = datetime.now(tz)
        weekday = today.weekday()
        start_of_week = today - timedelta(days=weekday)
        end_of_week = start_of_week + timedelta(days=4)

        df = load_projects()
        df["report_date"] = pd.to_datetime(df["report_date"], errors='coerce')

        filtered = df[
            (df["report_date"].dt.date >= start_of_week.date()) &
            (df["report_date"].dt.date <= end_of_week.date())
        ]

        if filtered.empty:
            await update.message.reply_text("❌ Нет отчетов на этой рабочей неделе (Пн–Пт).")
            return

        message = "@ellobodefuego Отчёты, сданные на текущей рабочей неделе:\n\n"
        for _, row in filtered.iterrows():
            date_str = row['report_date'].strftime("%d.%m")
            message += f"• {row['project']} — {date_str}, ответственный: {row['responsible']}\n"

        await update.message.reply_text(message)
    except Exception as e:
        logging.error(f"Ошибка в report_5: {e}")
        await update.message.reply_text("❌ Произошла ошибка при формировании отчёта.")


async def test_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = load_projects()
    if df.empty:
        await update.message.reply_text("📭 Нет данных.")
        return
    sample = df.sample(1).iloc[0]
    await update.message.reply_text(
        f"🎲 Случайный проект:\n• {sample['project']} — {sample['report_date'].day} числа. Ответственный: {sample['responsible']}"
    )


# === Автоматическая отправка уведомлений ===
async def send_scheduled_notifications(app, days_before):
    logging.info(f"🚀 Отправка напоминаний за {days_before} дней")
    msgs = generate_reminders(days_before)
    chat_id = load_chat_id()

    if not chat_id:
        logging.warning("❗ chat_id не найден, уведомления не отправлены.")
        return

    for msg in msgs:
        if "Сегодня нет отчётов" not in msg:  # Не отправляем пустые сообщения
            logging.info(f"📤 Отправка: {msg}")
            await app.bot.send_message(chat_id=chat_id, text=msg)


# === Новые функции для планировщика ===
async def scheduled_report_1(app):
    logging.info("🔔 Запуск запланированного отчета по предстоящим задачам")
    chat_id = load_chat_id()
    if not chat_id:
        logging.warning("❗ chat_id не найден, уведомления не отправлены.")
        return
    
    today = datetime.now(tz).date()
    weekday = today.weekday()
    monday = today - timedelta(days=weekday)
    friday = monday + timedelta(days=4)

    df = load_projects()
    filtered = df[(df['report_date'] >= today) & (df['report_date'] >= monday) & (df['report_date'] <= friday)]

    if filtered.empty:
        await app.bot.send_message(chat_id=chat_id, text="📭 На этой рабочей неделе нет предстоящих отчетов.")
        return

    filtered = filtered.sort_values(by='report_date')
    message = "📅 Предстоящие отчёты на этой рабочей неделе (Пн–Пт):\n\n"
    for _, row in filtered.iterrows():
        message += f"• {row['project']} — {row['report_date'].day} числа. Ответственный: {row['responsible']}\n"
    message += "\n🔔 Напомните клиентам об оплате!"
    await app.bot.send_message(chat_id=chat_id, text=message)


async def scheduled_report_5(app):
    logging.info("🔔 Запуск запланированного пятничного отчета")
    chat_id = load_chat_id()
    if not chat_id:
        logging.warning("❗ chat_id не найден, уведомления не отправлены.")
        return
    
    try:
        today = datetime.now(tz)
        weekday = today.weekday()
        start_of_week = today - timedelta(days=weekday)
        end_of_week = start_of_week + timedelta(days=4)

        df = load_projects()
        df["report_date"] = pd.to_datetime(df["report_date"], errors='coerce')

        filtered = df[
            (df["report_date"].dt.date >= start_of_week.date()) &
            (df["report_date"].dt.date <= end_of_week.date())
        ]

        if filtered.empty:
            await app.bot.send_message(chat_id=chat_id, text="❌ Нет отчетов на этой рабочей неделе (Пн–Пт).")
            return

        message = "@ellobodefuego Отчёты, сданные на текущей рабочей неделе:\n\n"
        for _, row in filtered.iterrows():
            date_str = row['report_date'].strftime("%d.%m")
            message += f"• {row['project']} — {date_str}, ответственный: {row['responsible']}\n"

        await app.bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        logging.error(f"Ошибка в scheduled_report_5: {e}")
        await app.bot.send_message(chat_id=chat_id, text="❌ Произошла ошибка при формировании отчёта.")


# === Проверка наличия токена ===
def check_token():
    if not TOKEN:
        logging.error("❌ Токен бота не найден в переменных окружения!")
        logging.error("Добавьте переменную окружения BOT_TOKEN в настройках Railway")
        return False
    return True


# === Главная функция ===
async def main():
    # Проверяем наличие токена
    if not check_token():
        return
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler(["start", "Start"], start))
    app.add_handler(CommandHandler("test_3days", test_3days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))
    app.add_handler(CommandHandler("test_random", test_random))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    # Фиксим планировщик - используем правильные функции для запланированных задач
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 5)), 
                      'cron', hour=9, minute=0, misfire_grace_time=60)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 3)), 
                      'cron', hour=9, minute=0, misfire_grace_time=60)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 1)), 
                      'cron', hour=9, minute=0, misfire_grace_time=60)
    scheduler.add_job(lambda: asyncio.create_task(send_scheduled_notifications(app, 0)), 
                      'cron', hour=9, minute=0, misfire_grace_time=60)
    
    # Фиксим вызовы отчетов через новые специальные функции
    scheduler.add_job(lambda: asyncio.create_task(scheduled_report_1(app)), 
                      'cron', day_of_week='mon', hour=9, minute=0, misfire_grace_time=60)
    scheduler.add_job(lambda: asyncio.create_task(scheduled_report_5(app)), 
                      'cron', day_of_week='fri', hour=17, minute=30, misfire_grace_time=60)
    
    scheduler.start()

    logging.info("✅ Планировщик задач запущен.")
    logging.info("▶️ Запуск Telegram polling...")
    
    # Добавляем дополнительное логирование для подтверждения работы бота
    logging.info(f"⏰ Текущее время: {datetime.now(tz)}")
    
    # Запуск веб-хука для Railway вместо обычного polling
    await app.run_polling(allowed_updates=Update.ALL_TYPES)


# === Запуск на Railway ===
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
