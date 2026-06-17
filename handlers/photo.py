import re
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

async def _format_nft_response(gift_name: str) -> str | None:
    result = await get_tonnel_floor(gift_name)
    ton_usd = await get_crypto_price("the-open-network", "usd")
    if not result:
        return None
    floor, count = result
    lines = [f"[NFT] {gift_name.upper()}", "=" * 30]
    lines.append(f"Floor: {floor:.2f} TON")
    if ton_usd:
        lines.append(f" (~${floor * ton_usd:.2f})")
    lines.append(f"Sotuvda: {count} ta")
    lines.append(f"\nAdmin: {ADMIN_USERNAME}")
    return "\n".join(lines)


async def _try_variations(name: str) -> tuple[str, str] | None:
    candidates = [name]
    parts = re.split(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', name)
    if len(parts) > 1:
        candidates.append(" ".join(parts))
        candidates.append("".join(parts))

    for candidate in candidates:
        resp = await _format_nft_response(candidate)
        if resp:
            return candidate, resp
    return None


@router.message(F.photo)
async def handle_photo(message: Message):
    if not TONNELMP_AVAILABLE:
        await message.answer("Tonnel kutubxonasi ishlamayapti.")
        return

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

    found = await _try_variations(nft_name)
    if found:
        nft_name, response = found
        await message.answer(response)
    else:
        await message.answer(f"{nft_name} uchun narx topilmadi. /nft <nomi> buyrug'ini ishlating.")
