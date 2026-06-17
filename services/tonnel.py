import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_cloudscraper = None
_executor = ThreadPoolExecutor(max_workers=3)

try:
    import cloudscraper as _cs
    _cloudscraper = _cs
    logger.info("cloudscraper loaded")
except Exception as e:
    logger.warning(f"cloudscraper not available: {e}")

TONNEL_API = "https://gifts2.tonnel.network/api/pageGifts"


async def get_tonnel_floor(gift_name: str):
    if not _cloudscraper:
        logger.warning("cloudscraper not installed, skipping Tonnel")
        return None

    variants = _get_variants(gift_name)
    for variant in variants:
        for payload in _build_payloads(variant):
            result = await _query(variant, payload)
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
    add(name.capitalize())
    import re
    parts = re.split(r'(?<=[a-z])(?=[A-Z])|[\s_-]+', name)
    parts = [p for p in parts if p]
    if len(parts) > 1:
        add(" ".join(parts))
        add(" ".join(parts).lower())
    return result[:4]


def _build_payloads(gift_name: str):
    base = {
        "price": {"$exists": True},
        "refunded": {"$ne": True},
        "buyer": {"$exists": False},
        "asset": "TON",
    }
    yield {"page": 1, "limit": 10, "sort": {"price": 1},
           "filter": {**base, "name": {"$regex": gift_name, "$options": "i"}},
           "ref": 0, "price_range": None, "user_auth": ""}
    yield {"page": 1, "limit": 10, "sort": {"price": 1},
           "filter": {**base, "name": gift_name},
           "ref": 0, "price_range": None, "user_auth": ""}


def _sync_query(payload: dict):
    scraper = _cloudscraper.create_scraper()
    try:
        resp = scraper.post(
            TONNEL_API,
            json=payload,
            timeout=15,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Origin": "https://tonnel.app",
                "Referer": "https://tonnel.app/",
            },
        )
        if resp.status_code != 200:
            logger.info(f"Tonnel cloudscraper status={resp.status_code}")
            return None
        data = resp.json()
        items = data if isinstance(data, list) else data.get("data") or data.get("gifts") or data.get("items") or []
        prices = [float(g["price"]) for g in items if g.get("price")]
        if prices:
            floor = min(prices)
            name = items[0].get("name", "?")
            logger.info(f"Tonnel cloudscraper: '{name}' floor={floor}, {len(prices)} items")
            return floor, len(prices)
    except Exception as e:
        logger.warning(f"Tonnel cloudscraper error: {e}")
    return None


async def _query(log_name: str, payload: dict):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _sync_query, payload)
