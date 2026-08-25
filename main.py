
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import settings
from database import init_db

from handlers.basic import router as basic_router
from handlers.cards import router as cards_router
from handlers.catch import router as catch_router
from handlers.daily import router as daily_router
from handlers.pack import router as pack_router
from handlers.owner import router as owner_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Initializing database...")

    await init_db()

    bot = Bot(
        token=settings.bot_token
    )

    dp = Dispatcher()

    dp.include_router(basic_router)
    dp.include_router(cards_router)
    dp.include_router(catch_router)
    dp.include_router(daily_router)
    dp.include_router(pack_router)
    dp.include_router(owner_router)

    try:
        me = await bot.get_me()

        logger.info(
            "Bot connected: @%s (%s)",
            me.username,
            me.id,
        )

        await bot.delete_webhook(
            drop_pending_updates=True
        )

        logger.info("Starting polling...")

        await dp.start_polling(bot)

    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
