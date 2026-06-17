# -*- coding: utf-8 -*-
import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.nft import router as nft_router
from handlers.stars import router as stars_router
from handlers.crypto import router as crypto_router
from handlers.gold import router as gold_router
from handlers.text import router as text_router
from handlers.admin import router as admin_router
from services.tonnel import TONNELMP_AVAILABLE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(nft_router)
dp.include_router(stars_router)
dp.include_router(crypto_router)
dp.include_router(gold_router)
dp.include_router(admin_router)
dp.include_router(text_router)


async def main():
    logger.info("Savdogar bot ishga tushdi...")
    logger.info(f"Tonnel available: {TONNELMP_AVAILABLE}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
