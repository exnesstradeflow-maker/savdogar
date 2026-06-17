import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

TONNEL_API = "https://gifts2.tonnel.network/api/pageGifts"


async def get_tonnel_floor(gift_name: str):
    name_variants = _get_name_variants(gift_name)

    for variant in name_variants:
        for payload in _build_payloads(variant):
            result = await _query_api(payload, variant)
            if result:
                return result

    return None


def _get_name_variants(name: str):
    variants = [name, name.lower(), name.capitalize()]
    parts = name.replace("-", " ").split()
    if len(parts) < 2:
        import re
        parts = re.split(r'(?<=[a-z])(?=[A-Z])', name)
    if len(parts) > 1:
        variants.append(" ".join(parts))
        variants.append(" ".join(parts).lower())
    return variants


def _build_payloads(gift_name: str):
    base_filter = {
        "price": {"$exists": True},
        "refunded": {"$ne": True},
        "buyer": {"$exists": False},
        "asset": "TON",
    }

    yield {
        "page": 1, "limit": 10,
        "sort": {"price": 1},
        "filter": {**base_filter, "name": {"$regex": gift_name, "$options": "i"}},
        "ref": 0, "price_range": None, "user_auth": "",
    }

    yield {
        "page": 1, "limit": 30,
        "sort": {"price": 1},
        "filter": {**base_filter, "name": gift_name},
        "ref": 0, "price_range": None, "user_auth": "",
    }

    yield {
        "page": 1, "limit": 30,
        "sort": {"price": 1},
        "filter": base_filter,
        "gift_name": gift_name,
        "ref": 0, "price_range": None, "user_auth": "",
    }


async def _query_api(payload: dict, log_name: str):
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(TONNEL_API, json=payload, timeout=15) as resp:
                body = await resp.text()
                logger.info(f"Tonnel API [{log_name}] status={resp.status} body_len={len(body)}")
                if resp.status != 200:
                    return None

                import json
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    return None

                items = data if isinstance(data, list) else data.get("data") or data.get("gifts") or data.get("items") or []
                if not items:
                    return None

                prices = []
                for g in items:
                    price = g.get("price")
                    if price:
                        prices.append(float(price))

                if prices:
                    floor = min(prices)
                    name = items[0].get("name", log_name)
                    logger.info(f"Tonnel OK: '{name}' floor={floor}, {len(prices)} listings")
                    return floor, len(prices)

    except Exception as e:
        logger.warning(f"Tonnel error: {e}")
    return None
