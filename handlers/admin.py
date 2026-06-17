from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID, ADMIN_USERNAME
from services.cache import clear_cache
from services.tonnel import get_tonnel_floor

router = Router()

def is_admin(user_id: int) -> bool:
    return bool(ADMIN_ID) and user_id == ADMIN_ID

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Admin panel:\n"
        "/test_nft <nomi> - API test\n"
        "/stats - Bot statistikasi\n"
        "/cache_clear - Keshni tozalash"
    )

@router.message(Command("test_nft"))
async def cmd_test_nft(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    name = parts[1].strip() if len(parts) > 1 else "SnowMittens"
    msg = await message.answer(f"Test: {name}...")
    result = await get_tonnel_floor(name)
    if result:
        await msg.edit_text(f"Tonnel OK: {name}\nFloor: {result[0]} TON\nSotuvda: {result[1]} ta")
    else:
        await msg.edit_text(f"Tonnel: {name} topilmadi")

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
