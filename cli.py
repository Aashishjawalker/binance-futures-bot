import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root before resolving creds
load_dotenv(Path(__file__).resolve().parent / ".env")

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.client import BinanceFuturesClient
from bot.logging_config import setup_logger
from bot.orders import (
    place_market_order,
    place_limit_order,
    place_stop_order,
    display_order,
)

logger = setup_logger("cli")


def _resolve_creds(api_key: str | None, api_secret: str | None):
    # Resolve API credentials from CLI args or env vars.
    key = api_key or os.environ.get("BINANCE_TESTNET_API_KEY", "")
    secret = api_secret or os.environ.get("BINANCE_TESTNET_API_SECRET", "")
    if not key or not secret:
        print("Error: API key and secret are required.")
        print("Set them via --api-key / --api-secret or environment variables:")
        print("  BINANCE_TESTNET_API_KEY")
        print("  BINANCE_TESTNET_API_SECRET")
        sys.exit(1)
    return key, secret


def _interactive_menu(client: BinanceFuturesClient) -> None:
    # Run an interactive order-entry loop.
    print()
    print("=" * 60)
    print("   Binance Futures Testnet — Interactive Order Entry".center(58))
    print("=" * 60)

    while True:
        print()
        print("── Order Type ──────────────────────────────────────────────")
        print("  1) MARKET  (buy/sell at current price)")
        print("  2) LIMIT   (buy/sell at a specified limit price)")
        print("  3) STOP    (stop-market or stop-limit)")
        print("  0) Exit")
        print("────────────────────────────────────────────────────────────")
        choice = input("  Choose [0-3]: ").strip()

        if choice == "0":
            print("  Goodbye.")
            break
        if choice not in ("1", "2", "3"):
            print("  Invalid choice — try again.")
            continue

        order_type = {"1": "MARKET", "2": "LIMIT", "3": "STOP"}[choice]

        symbol = input("  Symbol [BTCUSDT]: ").strip() or "BTCUSDT"
        side = input("  Side (BUY/SELL): ").strip().upper()
        while side not in ("BUY", "SELL"):
            print("  Must be BUY or SELL.")
            side = input("  Side (BUY/SELL): ").strip().upper()

        qty = input("  Quantity: ").strip()
        while True:
            try:
                float(qty)
                break
            except ValueError:
                qty = input("  Invalid — enter a number: ").strip()

        try:
            if order_type == "MARKET":
                result = place_market_order(client, symbol, side, qty)
            elif order_type == "LIMIT":
                price = input("  Limit price: ").strip()
                while True:
                    try:
                        float(price)
                        break
                    except ValueError:
                        price = input("  Invalid — enter a number: ").strip()
                result = place_limit_order(client, symbol, side, qty, price)
            else:
                stop_price = input("  Stop price: ").strip()
                while True:
                    try:
                        float(stop_price)
                        break
                    except ValueError:
                        stop_price = input("  Invalid — enter a number: ").strip()
                has_limit = input("  Add limit price? (y/N): ").strip().lower()
                price = None
                if has_limit == "y":
                    price = input("  Limit price: ").strip()
                result = place_stop_order(client, symbol, side, qty, stop_price, price)
        except Exception as exc:
            logger.error("Order failed: %s", exc)
            print(f"\n  ✗ Error: {exc}")
            continue

        display_order(result)

        another = input("  Place another order? (Y/n): ").strip().lower()
        if another == "n":
            break


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Environment variables:\n"
            "  BINANCE_TESTNET_API_KEY      Your Binance Futures Testnet API key\n"
            "  BINANCE_TESTNET_API_SECRET   Your Binance Futures Testnet API secret\n"
            "\n"
            "Examples:\n"
            "  python cli.py -s BTCUSDT -b BUY -t MARKET -q 0.002\n"
            "  python cli.py -s ETHUSDT -b SELL -t LIMIT -q 0.01 -p 1800.0\n"
            "  python cli.py -s SOLUSDT -b BUY -t STOP -q 1 --stop-price 120.0\n"
            "  python cli.py  (interactive mode)\n"
        ),
    )

    parser.add_argument("--api-key", help="Binance Futures Testnet API key")
    parser.add_argument("--api-secret", help="Binance Futures Testnet API secret")
    parser.add_argument("-s", "--symbol", default="BTCUSDT", help="Trading pair (e.g. BTCUSDT)")
    parser.add_argument("-b", "--side", choices=["BUY", "SELL"], help="Order side")
    parser.add_argument(
        "-t", "--type", dest="order_type",
        choices=["MARKET", "LIMIT", "STOP"],
        help="Order type",
    )
    parser.add_argument("-q", "--quantity", help="Order quantity")
    parser.add_argument("-p", "--price", help="Price (required for LIMIT)")
    parser.add_argument("--stop-price", help="Stop price (required for STOP)")
    parser.add_argument("--tif", default="GTC", help="Time-in-force (default: GTC)")

    return parser


def _run_single_shot(args: argparse.Namespace, client: BinanceFuturesClient) -> None:
    # Execute a single order from CLI arguments.
    if not args.side or not args.order_type or not args.quantity:
        print("Error: --side, --type, and --quantity are required in single-shot mode.")
        print("Use `python cli.py -h` for help.")
        sys.exit(1)

    otype = args.order_type.upper()

    try:
        if otype == "MARKET":
            result = place_market_order(client, args.symbol, args.side, args.quantity)
        elif otype == "LIMIT":
            if not args.price:
                print("Error: --price is required for LIMIT orders.")
                sys.exit(1)
            result = place_limit_order(client, args.symbol, args.side, args.quantity, args.price, args.tif)
        elif otype == "STOP":
            if not args.stop_price:
                print("Error: --stop-price is required for STOP orders.")
                sys.exit(1)
            result = place_stop_order(client, args.symbol, args.side, args.quantity, args.stop_price, args.price)
        else:
            print(f"Error: unknown order type '{otype}'")
            sys.exit(1)
    except Exception as exc:
        logger.error("Order failed: %s", exc)
        print(f"\n  ✗ Error: {exc}")
        sys.exit(1)

    display_order(result)


def main():
    parser = _build_parser()
    args = parser.parse_args()

    key, secret = _resolve_creds(args.api_key, args.api_secret)

    client = BinanceFuturesClient(api_key=key, api_secret=secret)

    if not client.ping():
        print("Warning: Could not reach Binance Futures Testnet API.")
        print("Check your internet connection and the base URL.")

    if args.side or args.order_type or args.quantity:
        _run_single_shot(args, client)
    else:
        _interactive_menu(client)


if __name__ == "__main__":
    main()
