import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

CBU_API = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"

@cached(ttl=60)
async def get_cbu_rate(currency: str) -> float | None:
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
