import logging
import aiohttp
from .cache import cached
from .name_utils import generate_name_variations

logger = logging.getLogger(__name__)

PORTALS_API = "https://portal-market.com/api/collections"

@cached(ttl=120)
async def get_portals_floor(gift_name: str) -> dict | None:
    variations = generate_name_variations(gift_name)[:3]
    for variant in variations:
        try:
            url = f"{PORTALS_API}?search={variant}&limit=5"
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        logger.info(f"Portals status {resp.status} for '{variant}'")
                        continue
                    data = await resp.json()
                    collections = data.get("collections") if isinstance(data, dict) else data
                    if not collections:
                        continue
                    for col in collections:
                        name = col.get("name", col.get("title", ""))
                        if gift_name.lower() in name.lower():
                            floor = col.get("floor_price") or col.get("floorPrice")
                            if floor is not None:
                                logger.info(f"Portals found: {name} = {floor} TON")
                                return {"price": float(floor), "currency": "TON", "market": "Portals", "name": name}
                    first = collections[0]
                    floor = first.get("floor_price") or first.get("floorPrice")
                    if floor is not None:
                        logger.info(f"Portals best match: {first.get('name', '?')} = {floor} TON")
                        return {"price": float(floor), "currency": "TON", "market": "Portals", "name": first.get("name", gift_name)}
        except Exception as e:
            logger.warning(f"Portals error for '{variant}': {e}")
    logger.info(f"Portals: no data for '{gift_name}'")
    return None
