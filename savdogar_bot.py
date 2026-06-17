# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import aiohttp
import json
import re

try:
    from tonnelmp import getGifts, filterStatsPretty
    TONNELMP_AVAILABLE = True
except Exception as e:
    TONNELMP_AVAILABLE = False
    print(f"tonnelmp import error: {e}")

try:
    from mrktmp import search_gifts, get_collection_floor
    MRKTMP_AVAILABLE = True
except Exception as e:
    MRKTMP_AVAILABLE = False
    print(f"mrktmp import error: {e}")

try:
    from portalsmp import search, giftsFloors
    PORTALSMP_AVAILABLE = True
except Exception as e:
    PORTALSMP_AVAILABLE = False
    print(f"portalsmp import error: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

ADMIN = os.environ.get("ADMIN", "@samir_axii")
STAR_TO_SOM = int(os.environ.get("STAR_TO_SOM", "195"))
CBU_API = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

TONNEL_AUTH = os.environ.get("TONNEL_AUTH", "")
PORTALS_AUTH = os.environ.get("PORTALS_AUTH", "")
MRKT_AUTH = os.environ.get("MRKT_AUTH", "")

print(f"TONNEL_AUTH set: {bool(TONNEL_AUTH)}")
print(f"PORTALS_AUTH set: {bool(PORTALS_AUTH)}")
print(f"MRKT_AUTH set: {bool(MRKT_AUTH)}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def get_cbu_rate(currency: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CBU_API, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data:
                        if item.get("Ccy") == currency.upper():
                            return float(item.get("Rate"))
    except Exception as e:
        logger.error(f"CBU error: {e}")
    return None


async def get_crypto_price(coin_id: str, vs_currency: str = "usd"):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{COINGECKO_API}?ids={coin_id.lower()}&vs_currencies={vs_currency}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get(coin_id.lower(), {}).get(vs_currency)
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")
    return None


async def get_ton_price():
    return await get_crypto_price("the-open-network", "usd")


async def get_nft_floor_tonnel(gift_name: str):
    if not TONNELMP_AVAILABLE:
        logger.error("Tonnel not available - import failed")
        return None
    try:
        logger.info(f"Tonnel search: {gift_name}")
        result = getGifts(gift_name=gift_name, limit=1, sort="price_asc", authData=TONNEL_AUTH)
        logger.info(f"Tonnel result: {result}")
        if result and len(result) > 0:
            return float(result[0].get("price", 0))
    except Exception as e:
        logger.error(f"Tonnel error: {e}")
    return None


async def get_nft_floor_mrkt(collection_name: str):
    if not MRKTMP_AVAILABLE:
        return None
    try:
        floor = get_collection_floor(MRKT_AUTH, collection_name)
        return floor
    except Exception as e:
        logger.error(f"MRKT error: {e}")
    return None


async def get_nft_floor_portals(gift_name: str):
    if not PORTALSMP_AVAILABLE:
        return None
    try:
        floors = giftsFloors(authData=PORTALS_AUTH)
        if floors and isinstance(floors, dict):
            return floors.get(gift_name.lower(), None)
    except Exception as e:
        logger.error(f"Portals error: {e}")
    return None


async def get_nft_floor_multi(gift_name: str):
    results = {}

    if TONNELMP_AVAILABLE:
        floor = await get_nft_floor_tonnel(gift_name)
        if floor:
            results['tonnel'] = floor

    if MRKTMP_AVAILABLE:
        floor = await get_nft_floor_mrkt(gift_name)
        if floor:
            results['mrkt'] = floor

    if PORTALSMP_AVAILABLE:
        floor = await get_nft_floor_portals(gift_name)
        if floor:
            results['portals'] = floor

    return results


def format_nft_response(gift_name: str, floors: dict, ton_usd):
    if not floors:
        return f"[X] {gift_name} uchun narx topilmadi"

    lines = [f"[NFT] {gift_name.upper()}"]
    lines.append("=" * 30)

    for market, price_ton in floors.items():
        usd_val = price_ton * ton_usd if ton_usd else None
        if usd_val:
            lines.append(f"{market.upper()}: {price_ton:.2f} TON (~${usd_val:.2f})")
        else:
            lines.append(f"{market.upper()}: {price_ton:.2f} TON")

    return "\n".join(lines)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        ">>> Savdogar Bot <<<\n\n"
        "Buyruqlar:\n"
        "/nft <gift nomi> - NFT floor narxi\n"
        "/stars <miqdor> - Stars -> Som\n"
        "/crypto <coin> - Crypto narxi\n"
        "/gold - Oltin narxi\n"
        f"\nAdmin: {ADMIN}"
    )
    await message.answer(text)


@dp.message(Command("nft"))
async def cmd_nft(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /nft <gift nomi>\nMisol: /nft toy bear")
        return

    gift_name = parts[1].strip()

    if "tonnel" in gift_name.lower() or "portals" in gift_name.lower() or "mrkt" in gift_name.lower():
        match = re.search(r'([a-z\-]+)', gift_name.lower())
        if match:
            gift_name = match.group(1).replace('-', ' ').title()

    await message.answer(f">>> {gift_name} narxi qidirilmoqda...")

    floors = await get_nft_floor_multi(gift_name)
    ton_usd = await get_ton_price()

    response = format_nft_response(gift_name, floors, ton_usd)
    response += f"\n\nAdmin: {ADMIN}"

    await message.answer(response)


@dp.message(Command("stars"))
async def cmd_stars(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /stars <miqdor>\nMisol: /stars 100")
        return

    try:
        stars = int(parts[1])
        som = stars * STAR_TO_SOM
        await message.answer(f"*** {stars} Stars = {som:,} som\n\nAdmin: {ADMIN}")
    except ValueError:
        await message.answer("[X] Raqam kiriting!")


@dp.message(Command("crypto"))
async def cmd_crypto(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /crypto <coin>\nMisol: /crypto bitcoin\n/crypto ethereum")
        return

    coin = parts[1].strip().lower()

    coin_map = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "ton": "the-open-network",
        "usdt": "tether",
        "usdc": "usd-coin",
        "bnb": "binancecoin",
    }

    coin = coin_map.get(coin, coin)

    await message.answer(f">>> {coin.upper()} narxi qidirilmoqda...")

    price_usd = await get_crypto_price(coin, "usd")

    if not price_usd:
        await message.answer(f"[X] {coin} topilmadi")
        return

    usd_to_uzs = await get_cbu_rate("USD")
    price_uzs = price_usd * usd_to_uzs if usd_to_uzs else None

    response = f"$$$ {coin.upper()}\n"
    response += f"${price_usd:,.2f}"
    if price_uzs:
        response += f"\n{price_uzs:,.0f} so'm"
    response += f"\n\nAdmin: {ADMIN}"

    await message.answer(response)


@dp.message(Command("gold"))
async def cmd_gold(message: Message):
    await message.answer(">>> Oltin narxi qidirilmoqda...")

    price_usd = await get_crypto_price("paxgold", "usd")

    if not price_usd:
        await message.answer("[X] Oltin narxini olish mumkin bo'lmadi")
        return

    usd_to_uzs = await get_cbu_rate("USD")
    price_uzs = price_usd * usd_to_uzs if usd_to_uzs else None

    response = f"** OLTIN (1g approx)\n"
    response += f"~${price_usd:,.2f}/g"
    if price_uzs:
        response += f"\n~{price_uzs:,.0f} so'm/g"
    response += f"\n\nAdmin: {ADMIN}"

    await message.answer(response)


async def parse_marketplace_link(url: str):
    if "tonnel.network" in url:
        match = re.search(r'/gift/([^/?]+)', url)
        if match:
            return match.group(1).replace('_', ' ').title()

    if "portals-market.com" in url:
        match = re.search(r'/nft/([^/?]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if "tgmrkt.io" in url or "mrkt" in url.lower():
        match = re.search(r'/([^/?]+?)(?:\?|/|$)', url.split('/')[-1])
        if match:
            name = match.group(1).replace('-', ' ').title()
            if name and len(name) > 2:
                return name

    return None


@dp.message()
async def handle_text(message: Message):
    text = message.text.lower().strip()

    urls = re.findall(r'https?://[^\s]+', message.text)
    for url in urls:
        gift_name = await parse_marketplace_link(url)
        if gift_name:
            await message.answer(f">>> {gift_name} narxi qidirilmoqda...")
            floors = await get_nft_floor_multi(gift_name)
            ton_usd = await get_ton_price()
            response = format_nft_response(gift_name, floors, ton_usd)
            response += f"\n\nAdmin: {ADMIN}"
            await message.answer(response)
            return

    star_match = re.search(r'(\d+)\s*(?:star|stars)', text, re.IGNORECASE)
    if star_match:
        stars = int(star_match.group(1))
        som = stars * STAR_TO_SOM
        await message.answer(f"*** {stars} Stars = {som:,} som\n\nAdmin: {ADMIN}")
        return

    words = text.split()
    if len(words) >= 2:
        candidates = [text.title()]
        for i in range(len(words) - 1):
            candidates.append(f"{words[i].title()} {words[i+1].title()}")

        for candidate in candidates:
            floors = await get_nft_floor_multi(candidate)
            if floors:
                await message.answer(f">>> {candidate} narxi qidirilmoqda...")
                ton_usd = await get_ton_price()
                response = format_nft_response(candidate, floors, ton_usd)
                response += f"\n\nAdmin: {ADMIN}"
                await message.answer(response)
                return

    crypto_patterns = ['bitcoin', 'ethereum', 'ton', 'usdt', 'usdc', 'bnb', 'btc', 'eth']
    for pattern in crypto_patterns:
        if pattern in text:
            await message.answer(f">>> {pattern.upper()} narxi qidirilmoqda...")
            coin_map = {
                "btc": "bitcoin",
                "eth": "ethereum",
                "ton": "the-open-network",
                "usdt": "tether",
                "usdc": "usd-coin",
                "bnb": "binancecoin",
            }
            coin = coin_map.get(pattern, pattern)
            price_usd = await get_crypto_price(coin, "usd")
            if not price_usd:
                await message.answer(f"[X] {coin} topilmadi")
                return
            usd_to_uzs = await get_cbu_rate("USD")
            price_uzs = price_usd * usd_to_uzs if usd_to_uzs else None
            response = f"$$$ {coin.upper()}\n${price_usd:,.2f}"
            if price_uzs:
                response += f"\n{price_uzs:,.0f} so'm"
            response += f"\n\nAdmin: {ADMIN}"
            await message.answer(response)
            return

    if "oltin" in text or "gold" in text:
        await message.answer(">>> Oltin narxi qidirilmoqda...")
        price_usd = await get_crypto_price("paxgold", "usd")
        if not price_usd:
            await message.answer("[X] Oltin narxini olish mumkin bo'lmadi")
            return
        usd_to_uzs = await get_cbu_rate("USD")
        price_uzs = price_usd * usd_to_uzs if usd_to_uzs else None
        response = f"** OLTIN (1g approx)\n~${price_usd:,.2f}/g"
        if price_uzs:
            response += f"\n~{price_uzs:,.0f} so'm/g"
        response += f"\n\nAdmin: {ADMIN}"
        await message.answer(response)
        return


async def main():
    logger.info("Savdogar bot ishga tushdi...")
    logger.info(f"Tonnel: {TONNELMP_AVAILABLE}, MRKT: {MRKTMP_AVAILABLE}, Portals: {PORTALSMP_AVAILABLE}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
