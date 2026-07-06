Steps to run on a new laptop:

  # 1. Install Python 3.11+ (from python.org — check "Add to PATH")
      After python is installed  run the below command to install libs
  #       pip install requests python-dotenv  <!-- this installs both request and python-dotenv -->
  #       requests
  #       python-dotenv

  # 2. Download the trading_bot folder to your desktop

  # 3. Create .env file with your Binance testnet keys
  #    (get them from https://testnet.binancefuture.com/)

  The current .env file have api keys inbuild and will be expired after 13-july-2026 after the key is expired u can create it from STEP 4
  #   BINANCE_TESTNET_API_KEY=your_api_key_here
  #   BINANCE_TESTNET_API_SECRET=your_api_secret_here

trading_bot/
## 📁 Project Structure

```
trading_bot/
├── app.py              ← Main entry point (Landing + Terminal server)
├── dashboard.py        ← Dashboard API server
├── cli.py              ← CLI-based trading interface
├── bot/                ← Core trading logic
│   ├── client.py         Binance API client
│   ├── orders.py         Order placement logic
│   ├── portfolio.py      Portfolio tracking
│   ├── validators.py     Input validation
│   └── logging_config.py Logging setup
├── ui/                 ← Frontend files
│   ├── index.html
│   ├── style.css
│   └── app.js
└── logs/               ← Log files
```
