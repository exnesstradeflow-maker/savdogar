from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.coingecko import get_crypto_price
from services.cbu import get_cbu_rate

router = Router()

@router.message(Command("gold"))
async def cmd_gold(message: Message):
    await message.answer("Oltin narxi qidirilmoqda...")
    price_usd = await get_crypto_price("paxgold", "usd")
    if not price_usd:
        await message.answer("Oltin narxini olish mumkin bo'lmadi")
        return

    usd_to_uzs = await get_cbu_rate("USD")
    text = f"** OLTIN (1g)\n~${price_usd:,.2f}/g"
    if usd_to_uzs:
        text += f"\n~{price_usd * usd_to_uzs:,.0f} so'm/g"
    text += f"\n\nAdmin: {ADMIN_USERNAME}"

    await message.answer(text)
