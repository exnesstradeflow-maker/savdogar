import re
import logging
import aiohttp

from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.ocr import extract_text, find_nft_name, is_tesseract_installed
from services.marketplaces import get_all_floor_prices, format_marketplace_response
from services.coingecko import get_crypto_price

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.photo)
async def handle_photo(message: Message):
    if not is_tesseract_installed():
        await message.answer("OCR o'rnatilmagan. Iltimos, /nft <nomi> yoki NFT linkini yuboring.")
        return

    await message.answer("Rasm tahlil qilinmoqda...")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                image_bytes = await resp.read()
    except Exception as e:
        logger.error(f"Download error: {e}")
        await message.answer("Rasmni yuklab bo'lmadi.")
        return

    ocr_text = extract_text(image_bytes)
    logger.info(f"OCR result: {ocr_text}")

    if not ocr_text:
        await message.answer("Rasmdan matn o'qib bo'lmadi. /nft <nomi> buyrug'ini ishlating.")
        return

    nft_name = find_nft_name(ocr_text)
    if not nft_name:
        await message.answer(
            f"Rasmdan NFT nomi topilmadi: {ocr_text[:120]}...\n/nft <nomi> buyrug'ini ishlating."
        )
        return

    prices = await get_all_floor_prices(nft_name)
    ton_usd = await get_crypto_price("the-open-network", "usd")

    if prices:
        response = format_marketplace_response(nft_name, prices, ton_usd)
        response += f"\n\nAdmin: {ADMIN_USERNAME}"
        await message.answer(response)
    else:
        await message.answer(f"{nft_name} uchun narx topilmadi. /nft <nomi> buyrug'ini ishlating.")
