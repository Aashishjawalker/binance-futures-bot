# Portfolio & position tracking.

from bot.logging_config import setup_logger

logger = setup_logger("portfolio")


def get_balances(client) -> list[dict]:
    # Fetch non-zero wallet balances.
    acct = client.get_account_info()
    return [
        {"asset": a["asset"], "wallet": a["walletBalance"], "available": a["availableBalance"]}
        for a in acct["assets"]
        if float(a["walletBalance"]) > 0
    ]


def get_positions(client) -> list[dict]:
    # Fetch open positions from positionRisk, enriched with entry & P&L info.
    raw = client.get_position_risk()
    positions = []
    for p in raw:
        qty = float(p.get("positionAmt", 0))
        if qty == 0:
            continue
        entry = float(p.get("entryPrice", 0))
        mark = float(p.get("markPrice", 0))
        liq = float(p.get("liquidationPrice", 0))
        upl = float(p.get("unRealizedProfit", 0))
        roe = (upl / (abs(qty) * entry)) * 100 if entry and abs(qty) * entry > 0 else 0
        positions.append({
            "symbol": p["symbol"],
            "side": "LONG" if qty > 0 else "SHORT",
            "size": abs(qty),
            "entryPrice": entry,
            "markPrice": mark,
            "liquidationPrice": liq,
            "unrealizedPnl": round(upl, 2),
            "pnlPercent": round(roe, 2),
            "leverage": float(p.get("leverage", 1)),
        })
    return positions


def get_order_history(client, symbol: str = None, limit: int = 20) -> list[dict]:
    # Fetch recent filled orders. If symbol is None, fetches for BTCUSDT as sample.
    sym = symbol or "BTCUSDT"
    try:
        all_orders = client._signed_request("GET", "/fapi/v1/allOrders", {
            "symbol": sym, "limit": limit,
        })
    except Exception as exc:
        logger.warning("Failed to fetch order history: %s", exc)
        return []

    filled = []
    for o in all_orders:
        if o["status"] == "FILLED":
            filled.append({
                "orderId": o["orderId"],
                "symbol": o["symbol"],
                "side": o["side"],
                "type": o["type"],
                "qty": o["executedQty"],
                "price": o["avgPrice"] or o["price"],
                "cumQuote": o["cumQuote"],
                "time": o["updateTime"],
            })
    return filled


def get_summary(client) -> dict:
    # Return combined account summary: balances + positions + recent orders.
    balances = get_balances(client)
    positions = get_positions(client)
    # Add total equity (wallet + unrealized PnL)
    account = client.get_account_info()
    total_wallet = account.get("totalWalletBalance", 0)
    total_upl = account.get("totalUnrealizedProfit", 0)
    return {
        "balances": balances,
        "positions": positions,
        "recentOrders": get_order_history(client),
        "account": {
            "totalWalletBalance": total_wallet,
            "totalUnrealizedPnl": round(float(total_upl), 2),
            "totalEquity": round(float(total_wallet) + float(total_upl), 2),
        },
    }
