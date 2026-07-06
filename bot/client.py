import hashlib
import hmac
import os
import time
import urllib.parse

import requests

from bot.logging_config import setup_logger

DEFAULT_BASE_URL = os.environ.get(
    "BINANCE_TESTNET_BASE_URL",
    "https://testnet.binancefuture.com",
)

logger = setup_logger("client")


class BinanceFuturesClient:

    def __init__(self, api_key: str, api_secret: str, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

        # connectivity to API.
    def ping(self) -> bool:
        try:
            resp = self.session.get(f"{self.base_url}/fapi/v1/ping", timeout=5)
            resp.raise_for_status()
            logger.debug("Ping OK — %s", resp.json())
            return True
        except requests.RequestException as exc:
            logger.error("Ping failed: %s", exc)
            return False

        # get trading metadata.
    def get_exchange_info(self) -> dict:
        resp = self.session.get(f"{self.base_url}/fapi/v1/exchangeInfo", timeout=10)
        resp.raise_for_status()
        return resp.json()

        # get time in milliseconds.
    def get_server_time(self) -> int:
        resp = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=5)
        resp.raise_for_status()
        return resp.json()["serverTime"]

    def _sign(self, params: dict) -> str:
        query_string = urllib.parse.urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _signed_request(self, method: str, endpoint: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 60_000
        params["signature"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"

        logger.debug("API %s %s  params=%s", method, endpoint, params)

        body_raw = b""
        try:
            if method.upper() == "GET":
                resp = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "DELETE":
                resp = self.session.delete(url, params=params, timeout=30)
            else:
                resp = self.session.post(url, data=params, timeout=30)
            body_raw = resp.content
            resp.raise_for_status()
            data = resp.json()
            logger.debug("API response [%s]: %s", endpoint, data)
            return data
        except requests.HTTPError as exc:
            body_text = body_raw.decode("utf-8", errors="replace") if body_raw else "(empty)"
            logger.error("HTTP %s on %s: %s | body: %s", exc.response.status_code, endpoint, exc, body_text)
            raise RuntimeError(f"API error {exc.response.status_code}: {body_text}") from exc
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.error("Network error on %s: %s", endpoint, exc)
            raise RuntimeError(f"Network error: {exc}") from exc

        # get account info and balances.
    def get_account_info(self) -> dict:
        return self._signed_request("GET", "/fapi/v2/account")

        # get open position.
    def get_position_risk(self) -> list[dict]:
        return self._signed_request("GET", "/fapi/v2/positionRisk")

        # place order using API.
    def place_order(self, **kwargs) -> dict:
        return self._signed_request("POST", "/fapi/v1/order", kwargs)

        # cancel order.
    def cancel_order(self, symbol: str, order_id: int | None = None, orig_client_order_id: str | None = None) -> dict:
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        return self._signed_request("DELETE", "/fapi/v1/order", params)

        # get order status.
    def get_order(self, symbol: str, order_id: int | None = None, orig_client_order_id: str | None = None) -> dict:
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        return self._signed_request("GET", "/fapi/v1/order", params)
