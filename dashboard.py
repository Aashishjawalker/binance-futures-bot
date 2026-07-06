#!/usr/bin/env python3
# Dashboard server — serves UI/ + Binance API proxy.
# Usage:  python dashboard.py  →  http://localhost:8080

import json
import os
import sys
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.client import BinanceFuturesClient
from bot.portfolio import get_summary, get_order_history

KEY = os.environ.get("BINANCE_TESTNET_API_KEY", "")
SECRET = os.environ.get("BINANCE_TESTNET_API_SECRET", "")
client = BinanceFuturesClient(api_key=KEY, api_secret=SECRET) if KEY and SECRET else None

UI_DIR = Path(__file__).resolve().parent / "ui"


def get_open_orders(client, symbol: str = None) -> list[dict]:
    raw = client._signed_request("GET", "/fapi/v1/openOrders", {})
    return [{
        "orderId": o["orderId"], "symbol": o["symbol"], "side": o["side"],
        "type": o["type"], "price": o["price"], "origQty": o["origQty"],
        "executedQty": o["executedQty"], "time": o["time"],
    } for o in raw]


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/summary":
            self._json(get_summary(client) if client else {"error": "No credentials"})
        elif path == "/api/orders":
            qs = parse_qs(parsed.query)
            symbol = qs.get("symbol", [None])[0]
            self._json({"orders": get_order_history(client, symbol) if client else []})
        elif path == "/api/open_orders":
            self._json({"orders": get_open_orders(client) if client else []})
        else:
            self._serve_static(path)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        try:
            if self.path == "/api/place_order":
                self._json(self._place(body))
            elif self.path == "/api/cancel_order":
                self._json(self._cancel(body))
            else:
                self.send_error(404)
        except Exception as e:
            self._json({"error": str(e)}, 400)

    def _place(self, body: dict) -> dict:
        params = {
            "symbol": body["symbol"], "side": body["side"],
            "type": body["type"], "quantity": float(body["quantity"]),
        }
        if body.get("price"): params["price"] = float(body["price"])
        if body.get("stopPrice"): params["stopPrice"] = float(body["stopPrice"])
        if body["type"] == "LIMIT": params["timeInForce"] = body.get("timeInForce", "GTC")
        r = client.place_order(**params)
        return {"orderId": r["orderId"], "status": r["status"], "symbol": r["symbol"], "message": f"Order {r['orderId']} {r['status']}"}

    def _cancel(self, body: dict) -> dict:
        r = client.cancel_order(symbol=body["symbol"], order_id=int(body["orderId"]))
        return {"message": f"Cancelled {r['orderId']}", "result": r}

    def _serve_static(self, path: str):
        if path == "/": path = "/index.html"
        filepath = UI_DIR / path.lstrip("/")
        # Security: prevent directory traversal
        try:
            filepath = filepath.resolve()
            if not str(filepath).startswith(str(UI_DIR.resolve())):
                self.send_error(403); return
        except OSError:
            self.send_error(403); return

        if not filepath.is_file():
            self.send_error(404); return

        mime, _ = mimetypes.guess_type(str(filepath))
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, fmt, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    if not client:
        print("Error: BINANCE_TESTNET_API_KEY / SECRET not set.")
        sys.exit(1)
    if not client.ping():
        print("Warning: Cannot reach Binance testnet.")
    print(f"Dashboard: http://localhost:{port}")
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
