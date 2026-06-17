import logging
import re

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

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "has", "have", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "you", "your",
    "we", "our", "they", "their", "he", "she", "him", "her",
    "and", "or", "but", "not", "no", "nor", "so", "if", "then",
    "else", "when", "where", "why", "how", "what", "which", "who",
    "whom", "by", "with", "from", "to", "in", "on", "at", "for",
    "of", "as", "up", "down", "out", "off", "over", "under",
    "floor", "price", "narxi", "sotuvda", "ton", "usd", "nft",
    "buy", "sell", "sale", "collection", "item", "gift",
}

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

def parse_tg_nft_link(text: str) -> str | None:
    m = re.search(r't\.me/nft/([A-Za-z0-9]+)', text)
    if m:
        raw = m.group(1)
        name = re.sub(r'-\d+$', '', raw)
        if name:
            return name
    return None

def find_nft_name(text: str) -> str | None:
    if not text:
        return None

    link_name = parse_tg_nft_link(text)
    if link_name:
        return link_name

    words = re.findall(r"[A-Za-z][a-zA-Z0-9]{1,}", text)

    camelcase_words = []
    for w in words:
        if w[0].isupper() and any(c.islower() for c in w[1:]):
            camelcase_words.append(w)

    if camelcase_words:
        return max(camelcase_words, key=len)

    cleaned = [w for w in words if w.lower() not in STOP_WORDS and len(w) > 1]
    if cleaned:
        return max(cleaned, key=len)

    if words:
        return words[0]

    return None

def is_tesseract_installed() -> bool:
    return TESSERACT_AVAILABLE
