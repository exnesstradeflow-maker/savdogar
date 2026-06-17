import logging
import re
import os

logger = logging.getLogger(__name__)

TESSERACT_AVAILABLE = False
pytesseract = None

try:
    import pytesseract as _pytesseract
    pytesseract = _pytesseract
    TESSERACT_AVAILABLE = True
    logger.info("pytesseract imported successfully")
except Exception as e:
    logger.warning(f"pytesseract not available: {e}")

try:
    from PIL import Image
except ImportError:
    Image = None

NFT_KEYWORDS = [
    "toy bear", "king otta", "otto", "bear", "rabbit", "penguin",
    "skull", "dragon", "lion", "tiger", "wolf", "fox", "owl",
    "cat", "dog", "monkey", "panda", "koala", "frog", "duck",
    "chicken", "fish", "whale", "shark", "horse", "unicorn",
    "robot", "alien", "zombie", "vampire", "ghost", "angel",
    "devil", "ninja", "pirate", "wizard", "knight", "king",
    "queen", "prince", "princess", "crown", "ring", "gem",
    "diamond", "gold", "silver", "bronze", "rainbow", "star",
    "moon", "sun", "cloud", "storm", "lightning", "snow",
    "flower", "tree", "mushroom", "candy", "cake", "ice cream",
    "pizza", "burger", "fries", "cola", "juice", "coffee",
    "tea", "beer", "wine", "champagne", "cocktail",
]

def extract_text(image_bytes: bytes) -> str | None:
    if not TESSERACT_AVAILABLE or not pytesseract or not Image:
        logger.warning("OCR not available")
        return None
    try:
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(img, lang="eng")
        return text.strip()
    except Exception as e:
        logger.error(f"OCR error: {e}")
    return None

def find_nft_name(text: str) -> str | None:
    if not text:
        return None
    text_lower = text.lower()
    for keyword in NFT_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
            return keyword.title()
    words = re.findall(r"\b[a-zA-Z]{2,}\b", text)
    if words:
        return words[0].title()
    return None

def is_tesseract_installed() -> bool:
    return TESSERACT_AVAILABLE
