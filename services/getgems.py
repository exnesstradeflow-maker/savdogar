import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

GETGEMS_API = "https://api.getgems.io/graphql"

SEARCH_QUERY = """
query searchCollections($query: String!) {
  collectionSearch(query: $query, limit: 5) {
    address
    name
    floorPrice
  }
}
"""

COLLECTION_QUERY = """
query collectionByAddress($address: String!) {
  collection(address: $address) {
    name
    floorPrice
  }
}
"""

@cached(ttl=120)
async def get_getgems_floor(gift_name: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "query": SEARCH_QUERY,
                "variables": {"query": gift_name}
            }
            headers = {"Content-Type": "application/json"}
            async with session.post(GETGEMS_API, json=payload, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    collections = data.get("data", {}).get("collectionSearch", [])
                    if collections:
                        for col in collections:
                            name = col.get("name", "")
                            if gift_name.lower() in name.lower():
                                floor = col.get("floorPrice")
                                if floor is not None:
                                    logger.info(f"Getgems found: {name} = {floor} TON")
                                    return {"price": float(floor), "currency": "TON", "market": "Getgems", "name": name}
                        first = collections[0]
                        floor = first.get("floorPrice")
                        if floor is not None:
                            logger.info(f"Getgems best: {first.get('name', '?')} = {floor} TON")
                            return {"price": float(floor), "currency": "TON", "market": "Getgems", "name": first.get("name", gift_name)}
    except Exception as e:
        logger.warning(f"Getgems GraphQL error: {e}")

    try:
        rest_url = f"https://api.getgems.io/v1/collections/search?q={gift_name}&limit=5"
        async with aiohttp.ClientSession() as session:
            async with session.get(rest_url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data if isinstance(data, list) else data.get("collections", data.get("data", []))
                    if items:
                        item = items[0]
                        floor = item.get("floor_price") or item.get("floorPrice")
                        if floor is not None:
                            return {"price": float(floor), "currency": "TON", "market": "Getgems", "name": item.get("name", gift_name)}
    except Exception as e:
        logger.warning(f"Getgems REST error: {e}")

    logger.info(f"Getgems: no data for '{gift_name}'")
    return None
