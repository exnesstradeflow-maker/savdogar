import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

TONNEL_API = "https://gifts2.tonnel.network/api/pageGifts"
TONNELMP_AVAILABLE = True

async def get_tonnel_floor(gift_name: str):
    name_variants = [gift_name]
    if " " not in gift_name:
        import re
        parts = re.split(r'(?<=[a-z])(?=[A-Z])', gift_name)
        if len(parts) > 1:
            name_variants.append(" ".join(parts))
            name_variants.append(" ".join(parts).lower())

    for variant in name_variants:
        floor = await _query_tonnel_api(variant)
        if floor:
            return floor

    return None


async def _query_tonnel_api(gift_name: str):
    try:
        payload = {
            "page": 1,
            "limit": 10,
            "sort": {"price": 1},
            "filter": {
                "name": {"$regex": gift_name, "$options": "i"},
                "price": {"$exists": True},
                "refunded": {"$ne": True},
                "buyer": {"$exists": False},
            },
            "ref": 0,
            "price_range": None,
            "user_auth": "",
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(TONNEL_API, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    logger.warning(f"Tonnel API status {resp.status}")
                    return None
                data = await resp.json()
                gifts = data if isinstance(data, list) else data.get("data", data.get("gifts", data.get("items", [])))
                if not gifts:
                    return None
                prices = []
                for g in gifts:
                    price = g.get("price")
                    if price:
                        prices.append(float(price))
                if prices:
                    floor = min(prices)
                    logger.info(f"Tonnel API: {gift_name} floor={floor}, total={len(prices)}")
                    return floor, len(prices)
    except Exception as e:
        logger.warning(f"Tonnel API error: {e}")
    return None
