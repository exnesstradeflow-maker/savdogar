import asyncio
import logging

from .tonnel import get_tonnel_floor, TONNELMP_AVAILABLE
from .getgems import get_getgems_floor
from .fragment import get_fragment_floor
from .coingecko import get_crypto_price

logger = logging.getLogger(__name__)


def format_marketplace_response(gift_name: str, prices: list[dict], ton_usd: float | None = None) -> str:
    lines = [f"[NFT] {gift_name.upper()}", "=" * 30]

    if not prices:
        return "\n".join(lines)

    best = prices[0]
    ton_price = best["price"]
    lines.append(f"Eng past: {ton_price:.2f} TON ({best['market']})")
    if ton_usd:
        lines.append(f"~${ton_price * ton_usd:.2f}")

    lines.append("")
    for p in prices:
        line = f"  {p['market']}: {p['price']:.2f} TON"
        if p.get("count"):
            line += f" ({p['count']} ta)"
        lines.append(line)

    return "\n".join(lines)


async def get_all_floor_prices(gift_name: str) -> list[dict]:
    tasks = []

    if TONNELMP_AVAILABLE:
        tasks.append(_fetch_tonnel(gift_name))

    tasks.append(_fetch_with_label("Getgems", get_getgems_floor(gift_name)))
    tasks.append(_fetch_with_label("Fragment", get_fragment_floor(gift_name)))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    prices = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"Marketplace error: {r}")
            continue
        if r and r.get("price") is not None:
            prices.append(r)

    prices.sort(key=lambda x: x["price"])
    return prices


async def _fetch_with_label(label: str, coro):
    try:
        result = await coro
        if result and result.get("price") is not None:
            return result
    except Exception as e:
        logger.warning(f"{label} error: {e}")
    return None


async def _fetch_tonnel(gift_name: str):
    try:
        result = await get_tonnel_floor(gift_name)
        if result and len(result) == 2:
            floor, count = result
            return {
                "price": float(floor),
                "currency": "TON",
                "market": "Tonnel",
                "name": gift_name,
                "count": count,
            }
    except Exception as e:
        logger.warning(f"Tonnel error: {e}")
    return None
