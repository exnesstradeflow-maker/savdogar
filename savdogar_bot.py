# -*- coding: utf-8 -*-
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

ADMIN = os.environ.get("ADMIN", "@samir_axii")
STAR_TO_SOM = int(os.environ.get("STAR_TO_SOM", "195"))
CBU_API = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

TONNELMP_AVAILABLE = False
getGifts = None

try:
    from tonnelmp import getGifts as _getGifts
    getGifts = _getGifts
    TONNELMP_AVAILABLE = True
    logger.info("tonnelmp imported successfully")
except Exception as e:
    logger.error(f"tonnelmp import failed: {e}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def get_cbu_rate(currency):
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


async def get_crypto_price(coin_id, vs_currency="usd"):
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


def get_tonnel_floor(gift_name):
    if not TONNELMP_AVAILABLE or not getGifts:
        return None
    try:
        logger.info(f"Tonnel search: {gift_name}")
        result = getGifts(gift_name=gift_name, limit=5, sort="price_asc")
        logger.info(f"Tonnel result count: {len(result) if result else 0}")
        if result and len(result) > 0:
            prices = [float(g.get("price", 0)) for g in result if g.get("price")]
            if prices:
                return min(prices), len(result)
    except Exception as e:
        logger.error(f"Tonnel error: {e}")
    return None


@dp.message(Command("start"))
async def cmd_start(message: Message):
    status = "ON" if TONNELMP_AVAILABLE else "OFF"
    await message.answer(
        "Savdogar Bot\n\n"
        "Buyruqlar:\n"
        "/nft <nomi> - NFT floor narxi (Tonnel)\n"
        "/stars <miqdor> - Stars -> Som\n"
        "/crypto <coin> - Crypto narxi\n"
        "/gold - Oltin narxi\n\n"
        f"Tonnel: {status}\n"
        f"Admin: {ADMIN}"
    )


@dp.message(Command("nft"))
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

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_tonnel_floor, gift_name)
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
    text += "\n"
    text += f"Sotuvda: {count} ta"
    text += f"\n\nAdmin: {ADMIN}"

    await message.answer(text)


@dp.message(Command("stars"))
async def cmd_stars(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /stars <miqdor>\nMisol: /stars 100")
        return

    try:
        stars = int(parts[1])
        som = stars * STAR_TO_SOM
        await message.answer(f"{stars} Stars = {som:,} som\n\nAdmin: {ADMIN}")
    except ValueError:
        await message.answer("Raqam kiriting!")


@dp.message(Command("crypto"))
async def cmd_crypto(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Foydalanish: /crypto <coin>\nMisol: /crypto bitcoin")
        return

    coin = parts[1].strip().lower()
    coin_map = {
        "btc": "bitcoin", "eth": "ethereum", "ton": "the-open-network",
        "usdt": "tether", "usdc": "usd-coin", "bnb": "binancecoin",
    }
    coin = coin_map.get(coin, coin)

    await message.answer(f"{coin.upper()} narxi qidirilmoqda...")

    price_usd = await get_crypto_price(coin, "usd")
    if not price_usd:
        await message.answer(f"{coin} topilmadi")
        return

    usd_to_uzs = await get_cbu_rate("USD")
    text = f"$$$ {coin.upper()}\n${price_usd:,.2f}"
    if usd_to_uzs:
        text += f"\n{price_usd * usd_to_uzs:,.0f} so'm"
    text += f"\n\nAdmin: {ADMIN}"

    await message.answer(text)


@dp.message(Command("gold"))
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
    text += f"\n\nAdmin: {ADMIN}"

    await message.answer(text)


@dp.message()
async def handle_text(message: Message):
    text = message.text.lower().strip()

    crypto_patterns = ['bitcoin', 'ethereum', 'ton', 'usdt', 'usdc', 'bnb', 'btc', 'eth']
    for pattern in crypto_patterns:
        if pattern in text:
            coin_map = {
                "btc": "bitcoin", "eth": "ethereum", "ton": "the-open-network",
                "usdt": "tether", "usdc": "usd-coin", "bnb": "binancecoin",
            }
            coin = coin_map.get(pattern, pattern)
            price_usd = await get_crypto_price(coin, "usd")
            if not price_usd:
                await message.answer(f"{coin} topilmadi")
                return
            usd_to_uzs = await get_cbu_rate("USD")
            response = f"$$$ {coin.upper()}\n${price_usd:,.2f}"
            if usd_to_uzs:
                response += f"\n{price_usd * usd_to_uzs:,.0f} so'm"
            response += f"\n\nAdmin: {ADMIN}"
            await message.answer(response)
            return

    if "oltin" in text or "gold" in text:
        price_usd = await get_crypto_price("paxgold", "usd")
        if not price_usd:
            await message.answer("Oltin narxini olish mumkin bo'lmadi")
            return
        usd_to_uzs = await get_cbu_rate("USD")
        response = f"** OLTIN (1g)\n~${price_usd:,.2f}/g"
        if usd_to_uzs:
            response += f"\n~{price_usd * usd_to_uzs:,.0f} so'm/g"
        response += f"\n\nAdmin: {ADMIN}"
        await message.answer(response)
        return


async def main():
    logger.info("Savdogar bot ishga tushdi...")
    logger.info(f"Tonnel available: {TONNELMP_AVAILABLE}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
