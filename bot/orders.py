# Order placement logic.

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = setup_logger("orders")

ORDER_TYPE_MAP = {
    "MARKET": "MARKET",
    "LIMIT": "LIMIT",
    "STOP": "STOP",
}


def _format_order_response(resp: dict) -> dict:
    # Extract and summarise relevant fields from a Binance order response.
    return {
        "orderId": resp.get("orderId"),
        "clientOrderId": resp.get("clientOrderId"),
        "symbol": resp.get("symbol"),
        "side": resp.get("side"),
        "type": resp.get("type"),
        "status": resp.get("status"),
        "origQty": resp.get("origQty"),
        "executedQty": resp.get("executedQty"),
        "cumQuote": resp.get("cumQuote"),
        "avgPrice": resp.get("avgPrice"),
        "price": resp.get("price"),
        "stopPrice": resp.get("stopPrice", ""),
        "timeInForce": resp.get("timeInForce", ""),
        "transactTime": resp.get("transactTime"),
    }


def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: str,
) -> dict:
    # Place a MARKET order.
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    qty = validate_quantity(quantity, sym)

    logger.info("Placing MARKET %s %s qty=%s", sd, sym, qty)

    resp = client.place_order(
        symbol=sym,
        side=sd,
        type="MARKET",
        quantity=qty,
    )

    result = _format_order_response(resp)
    result["_raw"] = resp
    return result


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: str,
    price: str,
    time_in_force: str = "GTC",
) -> dict:
    # Place a LIMIT order.
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    qty = validate_quantity(quantity, sym)
    prc = validate_price(price)

    logger.info("Placing LIMIT %s %s qty=%s price=%s tif=%s", sd, sym, qty, prc, time_in_force)

    resp = client.place_order(
        symbol=sym,
        side=sd,
        type="LIMIT",
        quantity=qty,
        price=prc,
        timeInForce=time_in_force,
    )

    result = _format_order_response(resp)
    result["_raw"] = resp
    return result


def place_stop_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: str,
    stop_price: str,
    price: str | None = None,
) -> dict:
    # Place a STOP order (stop-market or stop-limit).
    sym = validate_symbol(symbol)
    sd = validate_side(side)
    qty = validate_quantity(quantity, sym)
    sp = validate_stop_price(stop_price)

    params: dict = {
        "symbol": sym,
        "side": sd,
        "type": "STOP",
        "quantity": qty,
        "stopPrice": sp,
    }

    if price is not None:
        prc = validate_price(price)
        params["price"] = prc
        order_label = "STOP_LIMIT"
    else:
        order_label = "STOP_MARKET"

    logger.info("Placing %s %s %s qty=%s stopPrice=%s", order_label, sd, sym, qty, sp)

    resp = client.place_order(**params)
    result = _format_order_response(resp)
    result["_raw"] = resp
    return result


def display_order(result: dict) -> None:
    # Pretty-print an order result to the console.
    status = result.get("status", "?")
    symbol = result.get("symbol", "?")
    side = result.get("side", "?")
    otype = result.get("type", "?")
    oid = result.get("orderId", "?")
    qty = result.get("origQty", "?")
    filled = result.get("executedQty", "?")
    avg = result.get("avgPrice", "")
    price = result.get("price", "")

    print(f"\n{'='*60}")
    print(f"  ORDER PLACED  ".center(58, "·"))
    print(f"{'='*60}")
    print(f"  Symbol       : {symbol}")
    print(f"  Side         : {side}")
    print(f"  Type         : {otype}")
    print(f"  Order ID     : {oid}")
    print(f"  Status       : {status}")
    print(f"  Quantity     : {qty}")
    print(f"  Executed     : {filled}")
    if avg:
        print(f"  Avg Price    : {avg}")
    if price:
        print(f"  Limit Price  : {price}")
    print(f"{'='*60}")

    if status in ("NEW", "FILLED", "PARTIALLY_FILLED"):
        print(f"  ✓ Order {'placed successfully' if status == 'NEW' else 'filled!'}")
    elif status == "EXPIRED":
        print(f"  ✗ Order expired — market may be closed.")
    elif status == "REJECTED":
        print(f"  ✗ Order rejected — check parameters and account.")
    else:
        print(f"  ℹ Status: {status}")
    print(f"{'='*60}\n")