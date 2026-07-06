# Input validation for CLI arguments and order parameters.

import re
import sys

from bot.logging_config import setup_logger

logger = setup_logger("validators")

COMMON_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "UNIUSDT", "SHIBUSDT", "LTCUSDT", "ATOMUSDT",
    "ETCUSDT", "XLMUSDT", "BCHUSDT", "ALGOUSDT", "TRXUSDT",
    "FILUSDT", "APTUSDT", "ARBUSDT", "PEPEUSDT", "OPUSDT",
    "NEARUSDT", "AAVEUSDT", "INJUSDT", "TIAUSDT", "SEIUSDT",
}


def validate_symbol(raw: str) -> str:
    # Validate and normalise a symbol string.
    cleaned = raw.strip().upper()
    cleaned = re.sub(r"[-/_]", "", cleaned)
    if not cleaned.endswith("USDT"):
        raise ValueError(f"Symbol '{raw}' does not end with USDT — only USDT-M supported.")
    if cleaned not in COMMON_SYMBOLS:
        logger.warning("Symbol '%s' is not in the known set — proceeding anyway.", cleaned)
    return cleaned


def validate_side(raw: str) -> str:
    # Validate BUY or SELL.
    val = raw.strip().upper()
    if val not in ("BUY", "SELL"):
        raise ValueError(f"side must be BUY or SELL, got '{raw}'")
    return val


def validate_order_type(raw: str) -> str:
    # Validate MARKET, LIMIT, or STOP.
    val = raw.strip().upper()
    if val not in ("MARKET", "LIMIT", "STOP"):
        raise ValueError(f"order type must be MARKET, LIMIT, or STOP, got '{raw}'")
    return val


def validate_quantity(raw: str, symbol: str = "BTCUSDT") -> float:
    # Validate and parse quantity.
    try:
        qty = float(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"quantity must be a number, got '{raw}'") from exc

    if qty <= 0:
        raise ValueError(f"quantity must be positive, got {qty}")

    step_map = {
        "BTCUSDT": 0.001,
        "ETHUSDT": 0.001,
        "SOLUSDT": 0.1,
        "XRPUSDT": 1,
    }
    step = step_map.get(symbol.upper(), 0.001)
    rounded = round(qty / step) * step
    if abs(rounded - qty) > 1e-8:
        logger.info("Quantity %s rounded to %s (step size %s)", qty, rounded, step)
        qty = rounded

    return qty


def validate_price(raw: str) -> float:
    # Validate and parse price.
    try:
        price = float(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"price must be a number, got '{raw}'") from exc

    if price <= 0:
        raise ValueError(f"price must be positive, got {price}")

    return price


def validate_stop_price(raw: str) -> float:
    # Validate and parse stopPrice for STOP orders.
    try:
        sp = float(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"stopPrice must be a number, got '{raw}'") from exc

    if sp <= 0:
        raise ValueError(f"stopPrice must be positive, got {sp}")

    return sp
