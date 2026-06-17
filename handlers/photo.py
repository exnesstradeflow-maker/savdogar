import logging
import aiohttp

from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_USERNAME
from services.ocr import extract_text, find_nft_name, is_tesseract_installed
from services.tonnel import TONNELMP_AVAILABLE, get_tonnel_floor
from services.coingecko import get_crypto_price

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.photo)
async def handle_photo(message: Message):
    if not TONNELMP_AVAILABLE:
        await message.answer("Tonnel kutubxonasi ishlamayapti.")
        return

    if not is_tesseract_installed():
        await message.answer(
            "OCR tizimi o'rnatilmagan. Iltimos, NFT nomini matnda yozing:\n"
            "/nft <gift nomi>"
        )
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

    text = extract_text(image_bytes)
    logger.info(f"OCR result: {text}")

    if not text:
        await message.answer("Rasmdan matn o'qib bo'lmadi. Iltimos, /nft <nomi> buyrug'ini ishlating.")
        return

    nft_name = find_nft_name(text)
    if not nft_name:
        await message.answer(
            f"Rasmdan NFT nomi topilmadi. Topilgan matn: {text[:100]}...\n"
            "/nft <nomi> buyrug'ini ishlating."
        )
        return

    await message.answer(f"{nft_name} narxi qidirilmoqda...")

    result = await get_tonnel_floor(nft_name)
    ton_usd = await get_crypto_price("the-open-network", "usd")

    if not result:
        await message.answer(f"{nft_name} uchun narx topilmadi")
        return

    floor, count = result
    text_response = f"[NFT] {nft_name.upper()}\n"
    text_response += "=" * 30 + "\n"
    text_response += f"Floor: {floor:.2f} TON"
    if ton_usd:
        text_response += f" (~${floor * ton_usd:.2f})"
    text_response += f"\nSotuvda: {count} ta"
    text_response += f"\n\nAdmin: {ADMIN_USERNAME}"

    await message.answer(text_response)
