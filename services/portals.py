import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

PORTALS_API = "https://portal-market.com/api/collections"

@cached(ttl=120)
async def get_portals_floor(gift_name: str) -> dict | None:
    try:
        url = f"{PORTALS_API}?search={gift_name}&limit=10"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    collections = data.get("collections") if isinstance(data, dict) else data
                    if not collections:
                        return None
                    for col in collections:
                        name = col.get("name", col.get("title", ""))
                        if gift_name.lower() in name.lower():
                            floor = col.get("floor_price") or col.get("floorPrice")
                            if floor is not None:
                                return {
                                    "price": float(floor),
                                    "currency": "TON",
                                    "market": "Portals",
                                    "name": name,
                                }
                    first = collections[0]
                    floor = first.get("floor_price") or first.get("floorPrice")
                    if floor is not None:
                        return {
                            "price": float(floor),
                            "currency": "TON",
                            "market": "Portals",
                            "name": first.get("name", first.get("title", gift_name)),
                        }
    except Exception as e:
        logger.error(f"Portals error: {e}")
    return None
