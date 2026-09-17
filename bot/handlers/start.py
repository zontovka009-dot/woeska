from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.main import main_keyboard
router=Router()
@router.message(CommandStart())
async def start(message:Message): await message.answer("🎬 <b>Wathis</b>\nСмотри видео синхронно с друзьями.",reply_markup=main_keyboard(),parse_mode="HTML")
