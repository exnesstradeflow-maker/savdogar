import asyncio
import logging

from .tonnel import get_tonnel_floor, TONNELMP_AVAILABLE
from .getgems import get_getgems_floor
from .fragment import get_fragment_floor
from .portals import get_portals_floor
from .mrkt import get_mrkt_floor
from .coingecko import get_crypto_price
from .name_utils import generate_name_variations

logger = logging.getLogger(__name__)


def format_marketplace_response(gift_name: str, prices: list[dict], ton_usd: float | None = None) -> str:
    lines = [f"[NFT] {gift_name.upper()}", "=" * 30]

    if not prices:
        lines.append("Hech qanday marketplace da topilmadi")
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
    variations = generate_name_variations(gift_name)[:3]
    logger.info(f"Searching variations for '{gift_name}': {variations}")

    all_prices = []
    seen = set()

    for variant in variations:
        tasks = []

        if TONNELMP_AVAILABLE:
            tasks.append(_fetch_tonnel(variant))

        tasks.append(_fetch_with_label("Getgems", get_getgems_floor(variant)))
        tasks.append(_fetch_with_label("Fragment", get_fragment_floor(variant)))
        tasks.append(_fetch_with_label("Portals", get_portals_floor(variant)))
        tasks.append(_fetch_with_label("MRKT", get_mrkt_floor(variant)))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Market error: {r}")
                continue
            if r and r.get("price") is not None:
                key = (r["market"], round(r["price"], 4))
                if key not in seen:
                    seen.add(key)
                    all_prices.append(r)

        if all_prices:
            break

    all_prices.sort(key=lambda x: x["price"])
    logger.info(f"Total prices found for '{gift_name}': {len(all_prices)}")
    return all_prices


async def _fetch_with_label(label: str, coro):
    try:
        result = await coro
        if result and result.get("price") is not None:
            logger.info(f"{label}: {result['price']} TON")
            return result
        else:
            logger.info(f"{label}: no result")
    except Exception as e:
        logger.warning(f"{label} error: {e}")
    return None


async def _fetch_tonnel(gift_name: str):
    try:
        result = await get_tonnel_floor(gift_name)
        if result and len(result) == 2:
            floor, count = result
            logger.info(f"Tonnel: {floor} TON ({count} ta)")
            return {
                "price": float(floor),
                "currency": "TON",
                "market": "Tonnel",
                "name": gift_name,
                "count": count,
            }
        else:
            logger.info(f"Tonnel: no result for '{gift_name}'")
    except Exception as e:
        logger.warning(f"Tonnel error: {e}")
    return None
