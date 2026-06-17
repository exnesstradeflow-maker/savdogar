import re
from aiogram import Router
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.coingecko import get_crypto_price, resolve_coin
from services.cbu import get_cbu_rate

router = Router()

CRYPTO_KEYWORDS = [
    "bitcoin", "ethereum", "ton", "usdt", "usdc", "bnb",
    "btc", "eth", "sol", "doge", "xrp", "ada", "matic",
]

@router.message()
async def handle_text(message: Message):
    if not message.text:
        return
    text = message.text.lower().strip()

    for keyword in CRYPTO_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text):
            coin = resolve_coin(keyword)
            price_usd = await get_crypto_price(coin, "usd")
            if not price_usd:
                await message.answer(f"{coin} topilmadi")
                return
            usd_to_uzs = await get_cbu_rate("USD")
            response = f"$$$ {coin.upper()}\n${price_usd:,.2f}"
            if usd_to_uzs:
                response += f"\n{price_usd * usd_to_uzs:,.0f} so'm"
            response += f"\n\nAdmin: {ADMIN_USERNAME}"
            await message.answer(response)
            return

    if re.search(r"\b(oltin|gold|zoloto)\b", text, re.IGNORECASE):
        price_usd = await get_crypto_price("paxgold", "usd")
        if not price_usd:
            await message.answer("Oltin narxini olish mumkin bo'lmadi")
            return
        usd_to_uzs = await get_cbu_rate("USD")
        response = f"** OLTIN (1g)\n~${price_usd:,.2f}/g"
        if usd_to_uzs:
            response += f"\n~{price_usd * usd_to_uzs:,.0f} so'm/g"
        response += f"\n\nAdmin: {ADMIN_USERNAME}"
        await message.answer(response)
