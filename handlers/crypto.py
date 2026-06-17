from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.coingecko import get_crypto_price, resolve_coin
from services.cbu import get_cbu_rate

router = Router()

@router.message(Command("crypto"))
async def cmd_crypto(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /crypto <coin>\nMisol: /crypto bitcoin")
        return

    coin_input = parts[1].strip().lower()
    coin = resolve_coin(coin_input)

    await message.answer(f"{coin.upper()} narxi qidirilmoqda...")

    price_usd = await get_crypto_price(coin, "usd")
    if not price_usd:
        await message.answer(f"{coin_input} topilmadi")
        return

    usd_to_uzs = await get_cbu_rate("USD")
    text = f"$$$ {coin.upper()}\n${price_usd:,.2f}"
    if usd_to_uzs:
        text += f"\n{price_usd * usd_to_uzs:,.0f} so'm"
    text += f"\n\nAdmin: {ADMIN_USERNAME}"

    await message.answer(text)
