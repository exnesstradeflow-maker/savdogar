import re
import json
import asyncio
import logging
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from .cache import cached

logger = logging.getLogger(__name__)

FRAGMENT_URL = "https://fragment.com/gifts"

_cloudscraper = None
try:
    import cloudscraper as _cs
    _cloudscraper = _cs
except Exception:
    pass


def _find_price_in_html(html: str, name: str):
    patterns = [
        r'"floorPrice"\s*:\s*([\d.]+)',
        r'"floor_price"\s*:\s*([\d.]+)',
        r'data-floor-price[=:"]+\s*([\d.]+)',
        r'class="[^"]*price[^"]*"[^>]*>\s*([\d.]+)\s*TON',
        r'([\d.]+)\s*TON',
    ]

    for p in patterns:
        matches = re.findall(p, html, re.IGNORECASE)
        for m in matches:
            try:
                v = float(m)
                if 0.001 < v < 999999:
                    return v
            except ValueError:
                continue

    for jpat in [
        r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
        r'<script[^>]*>window\.__DATA__\s*=\s*({.*?})</script>',
    ]:
        m = re.search(jpat, html, re.DOTALL)
        if m:
            try:
                state = json.loads(m.group(1))
                for section in ["gift", "collection", "gifts"]:
                    data = state.get(section) or state.get(section + "s")
                    if isinstance(data, dict):
                        for key, val in data.items():
                            if name.lower() in key.lower():
                                floor = val.get("floorPrice") or val.get("price")
                                if floor:
                                    return float(floor)
            except (json.JSONDecodeError, AttributeError):
                continue

    return None


async def _fetch_url(url: str, name: str):
    if _cloudscraper:
        def sync_get():
            s = _cloudscraper.create_scraper()
            r = s.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            return (r.status_code, r.text) if r.status_code == 200 else (r.status_code, None)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(1) as pool:
            status, html = await loop.run_in_executor(pool, sync_get)
        if html:
            price = _find_price_in_html(html, name)
            if price:
                return price

    async with aiohttp.ClientSession() as session:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                html = await resp.text()
                return _find_price_in_html(html, name)
    return None


@cached(ttl=120)
async def get_fragment_floor(gift_name: str) -> dict | None:
    url = f"{FRAGMENT_URL}/{gift_name}"
    price = await _fetch_url(url, gift_name)
    if price:
        logger.info(f"Fragment: {gift_name} = {price} TON")
        return {"price": price, "currency": "TON", "market": "Fragment", "name": gift_name}

    alt_name = gift_name.replace(" ", "").replace("-", "")
    if alt_name != gift_name:
        alt_url = f"{FRAGMENT_URL}/{alt_name}"
        price = await _fetch_url(alt_url, alt_name)
        if price:
            logger.info(f"Fragment alt: {alt_name} = {price} TON")
            return {"price": price, "currency": "TON", "market": "Fragment", "name": alt_name}

    logger.info(f"Fragment: no data for '{gift_name}'")
    return None
