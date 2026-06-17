from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="NFT", callback_data="menu_nft")
    builder.button(text="Stars", callback_data="menu_stars")
    builder.button(text="Crypto", callback_data="menu_crypto")
    builder.button(text="Gold", callback_data="menu_gold")
    builder.adjust(2)
    return builder.as_markup()
