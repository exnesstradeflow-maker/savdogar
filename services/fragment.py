import re
import json
import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

FRAGMENT_URL = "https://fragment.com/gifts"
FRAGMENT_API = "https://fragment.com/api"

@cached(ttl=120)
async def get_fragment_floor(gift_name: str) -> dict | None:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            url = f"{FRAGMENT_URL}/{gift_name}"
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()

                price_match = re.search(
                    r'data-floor-price["\']?\s*[:=]\s*["\']?([\d.]+)',
                    text, re.IGNORECASE
                )
                if price_match:
                    return {
                        "price": float(price_match.group(1)),
                        "currency": "TON",
                        "market": "Fragment",
                        "name": gift_name,
                    }

                json_match = re.search(
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    text, re.DOTALL
                )
                if json_match:
                    state = json.loads(json_match.group(1))
                    gift_data = (
                        state.get("gift", {}) or
                        state.get("gifts", {}).get(gift_name, {})
                    )
                    if gift_data:
                        floor = gift_data.get("floorPrice") or gift_data.get("price")
                        if floor:
                            return {
                                "price": float(floor),
                                "currency": "TON",
                                "market": "Fragment",
                                "name": gift_data.get("name", gift_name),
                            }

                api_url = f"{FRAGMENT_API}/gifts/{gift_name}"
                async with session.get(api_url, timeout=10) as api_resp:
                    if api_resp.status == 200:
                        data = await api_resp.json()
                        floor = data.get("floorPrice") or data.get("price")
                        if floor:
                            return {
                                "price": float(floor),
                                "currency": "TON",
                                "market": "Fragment",
                                "name": data.get("name", gift_name),
                            }
    except Exception as e:
        logger.error(f"Fragment error: {e}")
    return None
