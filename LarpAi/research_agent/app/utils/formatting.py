from datetime import datetime, timezone
from typing import List


def format_timestamp(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime(fmt)


def format_confidence(score: float) -> str:
    pct = max(0.0, min(100.0, score * 100.0))
    return f"{pct:.1f}%"


def format_currency(amount: float, currency: str = "USD") -> str:
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3"}
    sym = symbols.get(currency, currency + " ")
    return f"{sym}{amount:.2f}"


def comma_list(items: List[str], conjunction: str = "and") -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} {conjunction} {items[-1]}"
