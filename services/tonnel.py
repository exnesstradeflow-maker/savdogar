import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

TONNELMP_AVAILABLE = False
_getGifts = None
_executor = ThreadPoolExecutor(max_workers=2)

try:
    from tonnelmp import getGifts as _getGifts
    TONNELMP_AVAILABLE = True
    logger.info("tonnelmp imported successfully")
except Exception as e:
    logger.error(f"tonnelmp import failed: {e}")

def _sync_get_floor(gift_name: str):
    if not TONNELMP_AVAILABLE or not _getGifts:
        return None
    try:
        logger.info(f"Tonnel search: {gift_name}")
        result = _getGifts(gift_name=gift_name, limit=5, sort="price_asc")
        logger.info(f"Tonnel result count: {len(result) if result else 0}")
        if result and len(result) > 0:
            prices = [float(g.get("price", 0)) for g in result if g.get("price")]
            if prices:
                return min(prices), len(result)
    except Exception as e:
        logger.error(f"Tonnel error: {e}")
    return None

async def get_tonnel_floor(gift_name: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _sync_get_floor, gift_name)
