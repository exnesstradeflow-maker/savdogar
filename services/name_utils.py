import re
import logging

logger = logging.getLogger(__name__)


def generate_name_variations(name: str) -> list[str]:
    seen = set()
    result = []

    def add(n):
        n = n.strip()
        if n and n not in seen:
            seen.add(n)
            result.append(n)

    add(name)
    add(name.lower())
    add(name.capitalize())

    parts = re.split(r'(?<=[a-z])(?=[A-Z])|[\s_-]+', name)
    parts = [p for p in parts if p]
    if len(parts) > 1:
        add(" ".join(parts))
        add(" ".join(parts).lower())
        add("".join(parts))
        add("-".join(parts))

    add(name.replace("-", " ").replace("_", " "))
    add(name.replace(" ", ""))

    return result


async def search_with_variations(name: str, search_fn, max_attempts: int = 3) -> list[dict]:
    variations = generate_name_variations(name)[:max_attempts]
    all_prices = []
    seen_prices = set()

    for variant in variations:
        prices = await search_fn(variant)
        for p in prices:
            key = (p["market"], round(p["price"], 4))
            if key not in seen_prices:
                seen_prices.add(key)
                all_prices.append(p)
        if all_prices:
            break

    all_prices.sort(key=lambda x: x["price"])
    return all_prices
