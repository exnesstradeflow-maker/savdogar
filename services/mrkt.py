import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

MRKT_API = "https://api.mrkt.fun"
MRKT_COLLECTIONS = f"{MRKT_API}/gifts/collections"

@cached(ttl=120)
async def get_mrkt_floor(gift_name: str) -> dict | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"{MRKT_COLLECTIONS}?search={gift_name}&limit=10"
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    collections = data if isinstance(data, list) else data.get("collections", data.get("data", []))
                    if not collections:
                        return None
                    for col in collections:
                        name = col.get("name", col.get("title", ""))
                        if gift_name.lower() in name.lower():
                            floor = col.get("floor_price_ton") or col.get("floorPrice") or col.get("floor_price")
                            if floor is not None:
                                return {
                                    "price": float(floor),
                                    "currency": "TON",
                                    "market": "MRKT",
                                    "name": name,
                                }
                    first = collections[0] if isinstance(collections, list) else None
                    if first:
                        floor = first.get("floor_price_ton") or first.get("floorPrice") or first.get("floor_price")
                        if floor is not None:
                            return {
                                "price": float(floor),
                                "currency": "TON",
                                "market": "MRKT",
                                "name": first.get("name", first.get("title", gift_name)),
                            }
    except Exception as e:
        logger.debug(f"MRKT API (mrkt.fun) not available: {e}")

    try:
        alt_url = f"https://mrkt.fun/api/collections?search={gift_name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(alt_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data if isinstance(data, list) else data.get("collections", [])
                    if items:
                        item = items[0]
                        floor = item.get("floor_price_ton") or item.get("floorPrice") or item.get("price")
                        if floor is not None:
                            return {
                                "price": float(floor),
                                "currency": "TON",
                                "market": "MRKT",
                                "name": item.get("name", item.get("title", gift_name)),
                            }
    except Exception as e:
        logger.debug(f"MRKT alt API not available: {e}")

    try:
        graph_url = "https://mrkt.fun/api/graphql"
        query = {
            "query": "{ collections(search: \"" + gift_name + "\", limit: 5) { name floorPriceTon } }"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(graph_url, json=query, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    cols = data.get("data", {}).get("collections", [])
                    if cols:
                        floor = cols[0].get("floorPriceTon")
                        if floor is not None:
                            return {
                                "price": float(floor),
                                "currency": "TON",
                                "market": "MRKT",
                                "name": cols[0].get("name", gift_name),
                            }
    except Exception as e:
        logger.debug(f"MRKT GraphQL not available: {e}")

    return None
