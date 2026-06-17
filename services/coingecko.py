import logging
import aiohttp
from .cache import cached

logger = logging.getLogger(__name__)

COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

COIN_MAP = {
    "btc": "bitcoin", "eth": "ethereum", "ton": "the-open-network",
    "usdt": "tether", "usdc": "usd-coin", "bnb": "binancecoin",
}

def resolve_coin(coin: str) -> str:
    return COIN_MAP.get(coin.lower(), coin.lower())

@cached(ttl=60)
async def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> float | None:
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{COINGECKO_API}?ids={coin_id.lower()}&vs_currencies={vs_currency}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get(coin_id.lower(), {}).get(vs_currency)
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")
    return None
