import asyncio
from aiogram import Bot,Dispatcher
from config import settings
from database import init_db
from handlers.basic import router as basic_router
from handlers.pack import router as pack_router
from handlers.daily import router as daily_router
from handlers.owner import router as owner_router
async def main():
 await init_db();bot=Bot(settings.bot_token);dp=Dispatcher();dp.include_router(basic_router);dp.include_router(daily_router);dp.include_router(pack_router);dp.include_router(owner_router)
 try:await dp.start_polling(bot)
 finally:await bot.session.close()
if __name__=='__main__':asyncio.run(main())
