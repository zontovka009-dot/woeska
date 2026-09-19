import asyncio, os
from aiogram import Bot, Dispatcher
from handlers.start import router as start_router
from handlers.commands import router as commands_router
from handlers.invitations import router as invitations_router
async def main():
    bot=Bot(os.environ["BOT_TOKEN"]); dp=Dispatcher(); dp.include_router(start_router); dp.include_router(commands_router); dp.include_router(invitations_router); await dp.start_polling(bot)
if __name__=="__main__": asyncio.run(main())
