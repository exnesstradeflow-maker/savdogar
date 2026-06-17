from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID, ADMIN_USERNAME
from services.cache import clear_cache

router = Router()

def is_admin(user_id: int) -> bool:
    return bool(ADMIN_ID) and user_id == ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Admin panel:\n"
        "/stats - Bot statistikasi\n"
        "/cache_clear - Keshni tozalash"
    )

@router.message(Command("cache_clear"))
async def cmd_cache_clear(message: Message):
    if not is_admin(message.from_user.id):
        return
    clear_cache()
    await message.answer("Kesh tozalandi")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Bot statistikasi\n\n"
        "Tez orada qo'shiladi..."
    )
