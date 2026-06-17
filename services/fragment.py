import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

FRAGMENT_URL = "https://fragment.com/gifts"

@cached(ttl=120)
async def get_fragment_floor(gift_name: str) -> dict | None:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html, */*",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"{FRAGMENT_URL}/{gift_name}"
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    logger.info(f"Fragment status {resp.status} for '{gift_name}'")
                    return None
                text = await resp.text()
                import re

                floor_patterns = [
                    r'data-floor-price[="\']?\s*[:=]\s*["\']?([\d.]+)',
                    r'"floorPrice"\s*:\s*([\d.]+)',
                    r'"floor_price"\s*:\s*([\d.]+)',
                    r'floorPrice["\']?\s*:\s*["\']?([\d.]+)',
                ]
                for pat in floor_patterns:
                    m = re.search(pat, text, re.IGNORECASE)
                    if m:
                        price = float(m.group(1))
                        logger.info(f"Fragment found: {gift_name} = {price} TON")
                        return {"price": price, "currency": "TON", "market": "Fragment", "name": gift_name}

                import json
                json_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'<script[^>]*>window\.__DATA__\s*=\s*({.*?})</script>',
                ]
                for jpat in json_patterns:
                    m = re.search(jpat, text, re.DOTALL)
                    if m:
                        try:
                            state = json.loads(m.group(1))
                            gift = state.get("gift") or state.get("gifts", {}).get(gift_name, {})
                            if isinstance(gift, dict):
                                floor = gift.get("floorPrice") or gift.get("price") or gift.get("floor_price")
                                if floor:
                                    return {"price": float(floor), "currency": "TON", "market": "Fragment", "name": gift.get("name", gift_name)}
                        except json.JSONDecodeError:
                            pass

    except Exception as e:
        logger.warning(f"Fragment error for '{gift_name}': {e}")
    logger.info(f"Fragment: no data for '{gift_name}'")
    return None
