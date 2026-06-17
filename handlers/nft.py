from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.marketplaces import get_all_floor_prices, format_marketplace_response
from services.coingecko import get_crypto_price

router = Router()

@router.message(Command("nft"))
async def cmd_nft(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /nft <gift nomi>\nMisol: /nft toy bear")
        return

    gift_name = parts[1].strip()
    await message.answer(f"{gift_name} narxi barcha marketlardan qidirilmoqda...")

    prices, ton_usd = await _search_all_markets(gift_name)

    if not prices:
        await message.answer(f"{gift_name} uchun hech qanday marketplace da narx topilmadi")
        return

    response = format_marketplace_response(gift_name, prices, ton_usd)
    response += f"\n\nAdmin: {ADMIN_USERNAME}"
    await message.answer(response)


async def _search_all_markets(gift_name: str):
    prices = await get_all_floor_prices(gift_name)
    ton_usd = await get_crypto_price("the-open-network", "usd")
    return prices, ton_usd
