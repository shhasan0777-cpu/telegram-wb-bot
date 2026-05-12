import asyncio
from aiogram import Bot, Dispatcher
from app.config import get_settings
from app.logging_config import setup_logging
from app.db.schema import init_db
from app.services.healthcheck import start_health_server
from app.services.scheduler import scheduler_loop
from app.handlers import start, lessons, admin, crm, media, unit

async def main():
    settings = get_settings()
    setup_logging(settings.log_level)
    init_db()
    bot = Bot(settings.bot_token)
    dp = Dispatcher()
    # Важно: unit с текстовым catch-all подключаем последним.
    dp.include_router(start.router)
    dp.include_router(lessons.router)
    dp.include_router(admin.router)
    dp.include_router(crm.router)
    dp.include_router(media.router)
    dp.include_router(unit.router)
    await start_health_server(settings.health_host, settings.health_port)
    asyncio.create_task(scheduler_loop(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
