import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

GETGEMS_API = "https://api.getgems.io/graphql"
FRAGMENT_API = "https://fragment.com/api/gifts"

SEARCH_QUERY = """
query searchCollections($query: String!) {
  collections(search: $query, first: 5) {
    edges {
      node {
        name
        floorPrice
        currency {
          code
        }
      }
    }
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
                    edges = data.get("data", {}).get("collections", {}).get("edges", [])
                    for edge in edges:
                        node = edge.get("node", {})
                        name = node.get("name", "")
                        if gift_name.lower() in name.lower():
                            floor = node.get("floorPrice")
                            if floor is not None:
                                return {
                                    "price": float(floor),
                                    "currency": node.get("currency", {}).get("code", "TON"),
                                    "market": "Getgems",
                                    "name": name,
                                }
    except Exception as e:
        logger.error(f"Getgems error: {e}")
    return None
