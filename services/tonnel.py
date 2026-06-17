import logging
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

TONNEL_API = "https://gifts2.tonnel.network/api/pageGifts"
TONNELMP_AVAILABLE = False
_getGifts = None
_executor = ThreadPoolExecutor(max_workers=2)

try:
    from tonnelmp import getGifts as _getGifts
    TONNELMP_AVAILABLE = True
    logger.info("tonnelmp library loaded successfully")
except Exception as e:
    logger.warning(f"tonnelmp not available: {e}")


async def get_tonnel_floor(gift_name: str):
    if TONNELMP_AVAILABLE:
        result = await _search_via_library(gift_name)
        if result:
            return result

    result = await _search_via_api(gift_name)
    if result:
        return result

    return None


async def _search_via_library(gift_name: str):
    variants = _get_variants(gift_name)
    for variant in variants:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, _sync_lookup, variant)
        if result:
            return result
    return None


def _sync_lookup(name: str):
    try:
        result = _getGifts(gift_name=name, limit=5, sort="price_asc")
        if result and len(result) > 0:
            prices = [float(g.get("price", 0)) for g in result if g.get("price")]
            if prices:
                floor = min(prices)
                logger.info(f"Tonnel lib: '{name}' floor={floor}, {len(prices)} listings")
                return floor, len(result)
    except Exception as e:
        logger.warning(f"Tonnel lib error for '{name}': {e}")
    return None


async def _search_via_api(gift_name: str):
    variants = _get_variants(gift_name)
    for variant in variants:
        result = await _try_api_payload(variant)
        if result:
            return result
    return None


def _get_variants(name: str):
    seen = set()
    result = []
    def add(n):
        n = n.strip()
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    add(name)
    add(name.lower())
    parts = name.replace("-", " ").split()
    if len(parts) < 2:
        import re
        parts = re.split(r'(?<=[a-z])(?=[A-Z])', name)
    if len(parts) > 1:
        add(" ".join(parts))
        add(" ".join(parts).lower())
    return result


async def _try_api_payload(gift_name: str):
    base_filter = {
        "price": {"$exists": True},
        "refunded": {"$ne": True},
        "buyer": {"$exists": False},
        "asset": "TON",
    }

    payloads = [
        {"page": 1, "limit": 10, "sort": {"price": 1},
         "filter": {**base_filter, "name": {"$regex": gift_name, "$options": "i"}},
         "ref": 0, "price_range": None, "user_auth": ""},
        {"page": 1, "limit": 10, "sort": {"price": 1},
         "filter": {**base_filter, "name": gift_name},
         "ref": 0, "price_range": None, "user_auth": ""},
    ]

    for payload in payloads:
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://tonnel.app",
                "Referer": "https://tonnel.app/",
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(TONNEL_API, json=payload, timeout=10) as resp:
                    if resp.status != 200:
                        continue
                    import json
                    body = await resp.text()
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        continue
                    items = data if isinstance(data, list) else data.get("data") or data.get("gifts") or data.get("items") or []
                    prices = [float(g["price"]) for g in items if g.get("price")]
                    if prices:
                        floor = min(prices)
                        logger.info(f"Tonnel API: '{gift_name}' floor={floor}, {len(prices)} listings")
                        return floor, len(prices)
        except Exception as e:
            logger.warning(f"Tonnel API error: {e}")
    return None
