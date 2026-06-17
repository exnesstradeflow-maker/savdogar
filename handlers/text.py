import re
from aiogram import Router
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.coingecko import get_crypto_price, resolve_coin
from services.cbu import get_cbu_rate
from services.marketplaces import get_all_floor_prices, format_marketplace_response

router = Router()

CRYPTO_KEYWORDS = [
    "bitcoin", "ethereum", "ton", "usdt", "usdc", "bnb",
    "btc", "eth", "sol", "doge", "xrp", "ada", "matic",
]

NFT_LINK_PATTERN = re.compile(r't\.me/nft/([A-Za-z0-9-]+)')


@router.message()
async def handle_text(message: Message):
    if not message.text:
        return
    text = message.text.strip()

    nft_match = NFT_LINK_PATTERN.search(text)
    if nft_match:
        raw_name = nft_match.group(1)
        gift_name = re.sub(r'-\d+$', '', raw_name)
        await message.answer(f"{gift_name} narxi barcha marketlardan qidirilmoqda...")
        prices = await get_all_floor_prices(gift_name)
        ton_usd = await get_crypto_price("the-open-network", "usd")
        if prices:
            response = format_marketplace_response(gift_name, prices, ton_usd)
            response += f"\n\nAdmin: {ADMIN_USERNAME}"
            await message.answer(response)
        else:
            await message.answer(f"{gift_name} uchun narx topilmadi")
        return

    text_lower = text.lower()

    for keyword in CRYPTO_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
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

    if re.search(r"\b(oltin|gold|zoloto)\b", text_lower):
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
