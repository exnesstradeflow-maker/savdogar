from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_USERNAME
from keyboards.inline import main_menu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Savdogar Bot\n\n"
        "Buyruqlar:\n"
        "/nft <nomi> - NFT floor narxi (barcha marketlar)\n"
        "/stars <miqdor> - Stars -> Som\n"
        "/crypto <coin> - Crypto narxi\n"
        "/gold - Oltin narxi\n"
        "[Photo] - NFT rasmini yuboring, floor narxni topaman\n"
        "[Link] - t.me/nft/... linkini yuboring\n\n"
        f"Marketplaces: Tonnel | Fragment | Getgems | Portals | MRKT\n"
        f"Admin: {ADMIN_USERNAME}",
        reply_markup=main_menu(),
    )

@router.callback_query(lambda c: c.data == "menu_nft")
async def menu_nft(callback: CallbackQuery):
    await callback.message.answer("Foydalanish: /nft <gift nomi>\nMisol: /nft toy bear")
    await callback.answer()

@router.callback_query(lambda c: c.data == "menu_stars")
async def menu_stars(callback: CallbackQuery):
    await callback.message.answer("Foydalanish: /stars <miqdor>\nMisol: /stars 100")
    await callback.answer()

@router.callback_query(lambda c: c.data == "menu_crypto")
async def menu_crypto(callback: CallbackQuery):
    await callback.message.answer("Foydalanish: /crypto <coin>\nMisol: /crypto bitcoin")
    await callback.answer()

@router.callback_query(lambda c: c.data == "menu_gold")
async def menu_gold(callback: CallbackQuery):
    await callback.message.answer("/gold - Oltin narxini olish")
    await callback.answer()
