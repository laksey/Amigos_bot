# ... (весь код сверху не меняется, включая импорты, утилиты, команды, планировщик)

# --- Запуск бота ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_5days", test_5days))
    app.add_handler(CommandHandler("test_today", test_today))
    app.add_handler(CommandHandler("report_1", report_1))
    app.add_handler(CommandHandler("report_5", report_5))

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(notify_5days, CronTrigger(day_of_week='mon', hour=9, minute=0), kwargs={"context": app})
    scheduler.add_job(notify_today, CronTrigger(day_of_week='fri', hour=9, minute=0), kwargs={"context": app})
    scheduler.start()

    logger.info("Запуск ClientOpsBot...")
    await app.run_polling()

# ✅ Без asyncio.run, чтобы избежать RuntimeError
if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(main())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен вручную.")
