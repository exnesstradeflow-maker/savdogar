from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_USERNAME, STAR_TO_SOM

router = Router()

@router.message(Command("stars"))
async def cmd_stars(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /stars <miqdor>\nMisol: /stars 100")
        return

    try:
        stars = int(parts[1])
        if stars <= 0:
            await message.answer("Musbat son kiriting!")
            return
        if stars > 1000000:
            await message.answer("Juda katta miqdor. 1,000,000 dan kichik son kiriting.")
            return
        som = stars * STAR_TO_SOM
        await message.answer(f"{stars} Stars = {som:,} som\n\nAdmin: {ADMIN_USERNAME}")
    except ValueError:
        await message.answer("Raqam kiriting!")
