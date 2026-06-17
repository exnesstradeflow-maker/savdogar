from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.tonnel import TONNELMP_AVAILABLE, get_tonnel_floor
from services.coingecko import get_crypto_price

router = Router()

@router.message(Command("nft"))
async def cmd_nft(message: Message):
    if not TONNELMP_AVAILABLE:
        await message.answer("Tonnel kutubxonasi ishlamayapti. Tekshiring.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /nft <gift nomi>\nMisol: /nft toy bear")
        return

    gift_name = parts[1].strip()
    await message.answer(f"{gift_name} narxi qidirilmoqda...")

    result = await get_tonnel_floor(gift_name)
    ton_usd = await get_crypto_price("the-open-network", "usd")

    if not result:
        await message.answer(f"{gift_name} uchun narx topilmadi")
        return

    floor, count = result
    text = f"[NFT] {gift_name.upper()}\n"
    text += "=" * 30 + "\n"
    text += f"Floor: {floor:.2f} TON"
    if ton_usd:
        text += f" (~${floor * ton_usd:.2f})"
    text += f"\nSotuvda: {count} ta"
    text += f"\n\nAdmin: {ADMIN_USERNAME}"

    await message.answer(text)
